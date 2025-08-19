# -*- coding: utf-8 -*-

import re
import json
from datetime import datetime
from flask import request, session, redirect, render_template, jsonify, abort
from werkzeug.utils import secure_filename
import logging
from functools import wraps
from route.tool.func import *

# 보안 로깅 설정
logging.basicConfig(
    filename='admin_access.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# IP 화이트리스트 (환경변수나 설정파일에서 읽어오는 것을 권장)
ALLOWED_IPS = [
    '127.0.0.1',
    '::1',
    # '192.168.1.0/24',  # 실제 관리자 IP 대역으로 변경
    # 'your-admin-ip-here'
]

def check_ip_whitelist():
    """IP 화이트리스트 검사"""
    client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    
    # 개발 환경에서는 로컬 IP 허용
    if client_ip in ['127.0.0.1', '::1', 'localhost']:
        return True
    
    # 화이트리스트 검사
    for allowed_ip in ALLOWED_IPS:
        if '/' in allowed_ip:  # CIDR 표기법
            # 간단한 CIDR 검사 (실제로는 ipaddress 모듈 사용 권장)
            network = allowed_ip.split('/')[0]
            if client_ip.startswith(network.rsplit('.', 1)[0]):
                return True
        elif client_ip == allowed_ip:
            return True
    
    return False

def security_check(f):
    """보안 검사 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 관리자 권한 검사
        if not admin_check():
            logging.warning(f'Unauthorized access attempt from {request.remote_addr}')
            return redirect('/login')
        
        # IP 화이트리스트 검사
        if not check_ip_whitelist():
            client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            logging.warning(f'IP not in whitelist: {client_ip}')
            abort(403)
        
        # 접근 로그 기록
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        user_agent = request.headers.get('User-Agent', 'Unknown')
        logging.info(f'Chat parser accessed by {client_ip} - {user_agent}')
        
        return f(*args, **kwargs)
    return decorated_function

def parse_kakao_chat(chat_text):
    """카카오톡 대화 내용을 파싱하여 구조화된 데이터로 변환 (보안 강화)"""
    if not chat_text or len(chat_text.strip()) == 0:
        return []
    
    # 입력 크기 제한 (DoS 방지)
    if len(chat_text) > 1000000:  # 1MB 제한
        raise ValueError("입력 데이터가 너무 큽니다.")
    
    lines = chat_text.strip().split('\n')
    parsed_data = []
    
    # 정규표현식 패턴들
    date_pattern = r'(\d{4}년 \d{1,2}월 \d{1,2}일 (?:오전|오후) \d{1,2}:\d{2})'
    invite_pattern = r'(.+?)님이 (.+?)를 초대했습니다'
    message_pattern = r'(.+?) : (.+)'
    
    current_date = None
    processed_lines = 0
    
    for line in lines:
        processed_lines += 1
        if processed_lines > 10000:  # 라인 수 제한
            break
            
        line = line.strip()
        if not line:
            continue
            
        # XSS 방지를 위한 기본 이스케이프
        line = line.replace('<', '&lt;').replace('>', '&gt;')
            
        # 날짜 라인 체크
        date_match = re.match(date_pattern, line)
        if date_match:
            current_date = date_match.group(1)
            continue
            
        # 초대 메시지 체크
        if '초대했습니다' in line:
            invite_match = re.search(invite_pattern, line)
            if invite_match:
                inviter = invite_match.group(1)[:50]  # 길이 제한
                invitees = invite_match.group(2)[:200]  # 길이 제한
                parsed_data.append({
                    'type': 'invite',
                    'datetime': current_date,
                    'inviter': inviter,
                    'invitees': invitees,
                    'content': line[:500]  # 길이 제한
                })
            continue
            
        # 일반 메시지 체크
        if current_date and ', ' in line:
            parts = line.split(', ', 2)
            if len(parts) >= 3:
                datetime_str = parts[0] + ', ' + parts[1]
                message_part = parts[2]
                
                message_match = re.match(message_pattern, message_part)
                if message_match:
                    speaker = message_match.group(1)[:50]  # 길이 제한
                    content = message_match.group(2)[:1000]  # 길이 제한
                    
                    parsed_data.append({
                        'type': 'message',
                        'datetime': datetime_str,
                        'speaker': speaker,
                        'content': content
                    })
    
    return parsed_data

def convert_to_wiki_format(parsed_data, title="카카오톡 대화 기록"):
    """파싱된 데이터를 위키 형식으로 변환 (보안 강화)"""
    if not parsed_data:
        return "= 빈 대화 기록 =\n\n대화 내용이 없습니다."
    
    # 제목 길이 제한 및 이스케이프
    title = title[:100].replace('<', '&lt;').replace('>', '&gt;')
    wiki_content = f"= {title} =\n\n"
    
    # 참여자 목록 추출
    participants = set()
    for item in parsed_data:
        if item['type'] == 'message':
            participants.add(item['speaker'])
        elif item['type'] == 'invite':
            participants.add(item['inviter'])
            invitees = item['invitees'].replace('님', '').replace('과 ', ', ').replace('와 ', ', ')
            for invitee in invitees.split(', '):
                if invitee.strip():
                    participants.add(invitee.strip())
    
    # 참여자 수 제한
    if len(participants) > 100:
        participants = list(participants)[:100]
    
    # 참여자 섹션
    wiki_content += "== 참여자 ==\n"
    for participant in sorted(participants):
        wiki_content += f"* {participant}\n"
    wiki_content += "\n"
    
    # 대화 내용 섹션
    wiki_content += "== 대화 내용 ==\n"
    
    current_date = None
    item_count = 0
    
    for item in parsed_data:
        item_count += 1
        if item_count > 1000:  # 항목 수 제한
            wiki_content += "\n''(너무 많은 메시지로 인해 일부가 생략되었습니다)''\n"
            break
            
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

@app.route('/tool_chat_parser', methods=['GET', 'POST'])
@security_check
def tool_chat_parser():
    """보안 강화된 카카오톡 대화 파서"""
    if request.method == 'POST':
        try:
            chat_content = request.form.get('chat_content', '').strip()
            page_title = request.form.get('page_title', '카카오톡 대화 기록').strip()
            
            if not chat_content:
                return render_template('ringo/chat_parser.html', 
                                     error='대화 내용을 입력해주세요.',
                                     lang=load_lang())
            
            # 입력 검증
            if len(chat_content) > 1000000:  # 1MB 제한
                return render_template('ringo/chat_parser.html', 
                                     error='입력 데이터가 너무 큽니다. (최대 1MB)',
                                     lang=load_lang())
            
            if len(page_title) > 100:
                return render_template('ringo/chat_parser.html', 
                                     error='페이지 제목이 너무 깁니다. (최대 100자)',
                                     lang=load_lang())
            
            # 파싱 및 변환
            parsed_data = parse_kakao_chat(chat_content)
            
            if not parsed_data:
                return render_template('ringo/chat_parser.html', 
                                     error='파싱할 수 있는 대화 내용이 없습니다.',
                                     lang=load_lang())
            
            wiki_content = convert_to_wiki_format(parsed_data, page_title)
            
            # 페이지 생성
            page_name = secure_filename(page_title) or 'kakao_chat_' + datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 중복 페이지명 체크
            original_name = page_name
            counter = 1
            while curs.execute("SELECT title FROM data WHERE title = ?", [page_name]).fetchone():
                page_name = f"{original_name}_{counter}"
                counter += 1
            
            # 데이터베이스에 저장
            curs.execute("INSERT INTO data (title, data, date) VALUES (?, ?, ?)", 
                        [page_name, wiki_content, get_time()])
            conn.commit()
            
            # 성공 로그
            client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            logging.info(f'Wiki page created: {page_name} by {client_ip}')
            
            return render_template('ringo/chat_parser.html', 
                                 success=f'위키 페이지 "{page_name}"이(가) 성공적으로 생성되었습니다!',
                                 page_name=page_name,
                                 lang=load_lang())
            
        except ValueError as e:
            logging.warning(f'Validation error: {str(e)} from {request.remote_addr}')
            return render_template('ringo/chat_parser.html', 
                                 error=str(e),
                                 lang=load_lang())
        except Exception as e:
            logging.error(f'Unexpected error: {str(e)} from {request.remote_addr}')
            return render_template('ringo/chat_parser.html', 
                                 error='처리 중 오류가 발생했습니다.',
                                 lang=load_lang())
    
    return render_template('ringo/chat_parser.html', lang=load_lang())