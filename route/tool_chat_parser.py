import re
import json
from datetime import datetime
from flask import Flask, request, redirect, render_template, jsonify
from route.tool.func import *

def chat_parser_main():
    """카카오톡 대화 파서 메인 페이지"""
    if admin_check() != 1:
        return re_error('/error/3')
    
    return render_template('chat_parser.html', 
                         menu=[['tool_chat_parser', get_lang('chat_parser')]], 
                         data='')

def parse_kakao_chat(chat_text):
    """카카오톡 대화 내용을 파싱하여 구조화된 데이터로 변환"""
    lines = chat_text.strip().split('\n')
    parsed_data = []
    
    # 정규표현식 패턴들
    date_pattern = r'(\d{4}년 \d{1,2}월 \d{1,2}일 (?:오전|오후) \d{1,2}:\d{2})'
    invite_pattern = r'(.+?)님이 (.+?)를 초대했습니다'
    message_pattern = r'(.+?) : (.+)'
    
    current_date = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 날짜 라인 체크
        date_match = re.match(date_pattern, line)
        if date_match:
            current_date = date_match.group(1)
            continue
            
        # 초대 메시지 체크
        if '초대했습니다' in line:
            invite_match = re.search(invite_pattern, line)
            if invite_match:
                inviter = invite_match.group(1)
                invitees = invite_match.group(2)
                parsed_data.append({
                    'type': 'invite',
                    'datetime': current_date,
                    'inviter': inviter,
                    'invitees': invitees,
                    'content': line
                })
            continue
            
        # 일반 메시지 체크
        if current_date and ', ' in line:
            # 날짜와 메시지가 함께 있는 경우
            parts = line.split(', ', 2)
            if len(parts) >= 3:
                datetime_str = parts[0] + ', ' + parts[1]
                message_part = parts[2]
                
                message_match = re.match(message_pattern, message_part)
                if message_match:
                    speaker = message_match.group(1)
                    content = message_match.group(2)
                    
                    parsed_data.append({
                        'type': 'message',
                        'datetime': datetime_str,
                        'speaker': speaker,
                        'content': content
                    })
    
    return parsed_data

def convert_to_wiki_format(parsed_data, title="카카오톡 대화 기록"):
    """파싱된 데이터를 위키 형식으로 변환"""
    wiki_content = f"= {title} =\n\n"
    
    # 참여자 목록 추출
    participants = set()
    for item in parsed_data:
        if item['type'] == 'message':
            participants.add(item['speaker'])
        elif item['type'] == 'invite':
            participants.add(item['inviter'])
            # 초대받은 사람들도 추가
            invitees = item['invitees'].replace('님', '').replace('과 ', ', ').replace('와 ', ', ')
            for invitee in invitees.split(', '):
                if invitee.strip():
                    participants.add(invitee.strip())
    
    # 참여자 섹션
    wiki_content += "== 참여자 ==\n"
    for participant in sorted(participants):
        wiki_content += f"* {participant}\n"
    wiki_content += "\n"
    
    # 대화 내용 섹션
    wiki_content += "== 대화 내용 ==\n"
    
    current_date = None
    for item in parsed_data:
        # 날짜가 바뀌면 새로운 섹션 생성
        item_date = item['datetime'].split(' 오')[0] if item['datetime'] else None
        if item_date and item_date != current_date:
            current_date = item_date
            wiki_content += f"\n=== {current_date} ===\n"
        
        if item['type'] == 'invite':
            wiki_content += f"'''{item['datetime']}''' - {item['inviter']}님이 {item['invitees']}를 초대했습니다.\n\n"
        elif item['type'] == 'message':
            time_part = item['datetime'].split(', ')[-1] if ', ' in item['datetime'] else item['datetime']
            wiki_content += f"'''{time_part}''' '''[[{item['speaker']}]]''': {item['content']}\n\n"
    
    return wiki_content

def chat_parser_submit():
    """카카오톡 대화 파싱 및 위키 생성 처리"""
    if admin_check() != 1:
        return re_error('/error/3')
    
    if request.method == 'POST':
        chat_text = request.form.get('chat_text', '')
        wiki_title = request.form.get('wiki_title', '카카오톡 대화 기록')
        
        if not chat_text:
            return jsonify({'error': '대화 내용을 입력해주세요.'})
        
        try:
            # 대화 내용 파싱
            parsed_data = parse_kakao_chat(chat_text)
            
            if not parsed_data:
                return jsonify({'error': '파싱할 수 있는 대화 내용이 없습니다.'})
            
            # 위키 형식으로 변환
            wiki_content = convert_to_wiki_format(parsed_data, wiki_title)
            
            # 위키 페이지 생성
            curs = conn.cursor()
            
            # 기존 페이지가 있는지 확인
            curs.execute(db_change("select title from data where title = ?"), [wiki_title])
            if curs.fetchone():
                return jsonify({'error': f'이미 "{wiki_title}" 페이지가 존재합니다.'})
            
            # 새 페이지 생성
            curs.execute(db_change("insert into data (title, data, type) values (?, ?, ?)"), 
                        [wiki_title, wiki_content, 'r'])
            
            # 히스토리 추가
            now_time = get_time()
            curs.execute(db_change("insert into history (id, title, data, date, ip, send, leng, hide, type) values (?, ?, ?, ?, ?, ?, ?, ?, ?)"), 
                        [1, wiki_title, wiki_content, now_time, ip_check(), '카카오톡 대화 자동 생성', str(len(wiki_content)), '', 'r'])
            
            conn.commit()
            
            return jsonify({
                'success': True, 
                'message': f'"{wiki_title}" 페이지가 성공적으로 생성되었습니다.',
                'wiki_url': f'/w/{wiki_title}',
                'parsed_count': len(parsed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'처리 중 오류가 발생했습니다: {str(e)}'})
    
    return redirect('/tool_chat_parser')