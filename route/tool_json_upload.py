from .tool.func import *
import json
import os
import tempfile

async def tool_json_upload():
    """JSON 파일로 위키 데이터 업로드"""
    with get_db_connect() as conn:
        curs = conn.cursor()
        
        # 관리자 권한 확인
        if await acl_check(tool='owner_auth') != 1:
            return await re_error(conn, 3)
        
        if flask.request.method == 'POST':
            try:
                # 파일 업로드 처리
                uploaded_file = flask.request.files.get('json_file')
                if not uploaded_file or uploaded_file.filename == '':
                    return flask.jsonify({'error': 'JSON 파일을 선택해주세요.'})
                
                # 파일 확장자 확인
                if not uploaded_file.filename.lower().endswith('.json'):
                    return flask.jsonify({'error': 'JSON 파일만 업로드 가능합니다.'})
                
                # 파일 크기 제한 (10MB)
                file_content = uploaded_file.read()
                if len(file_content) > 10 * 1024 * 1024:
                    return flask.jsonify({'error': '파일 크기가 너무 큽니다. (최대 10MB)'})
                
                # JSON 파싱
                try:
                    json_data = json.loads(file_content.decode('utf-8'))
                except json.JSONDecodeError as e:
                    return flask.jsonify({'error': f'JSON 형식이 올바르지 않습니다: {str(e)}'})
                except UnicodeDecodeError:
                    return flask.jsonify({'error': 'UTF-8 인코딩이 아닙니다.'})
                
                # 데이터 형식 검증
                if not isinstance(json_data, dict):
                    return flask.jsonify({'error': 'JSON 데이터는 객체(Object) 형태여야 합니다.'})
                
                # 업로드 옵션
                overwrite = flask.request.form.get('overwrite') == 'true'
                add_prefix = flask.request.form.get('add_prefix', '').strip()
                
                # 페이지 생성/업데이트
                created_pages = []
                updated_pages = []
                skipped_pages = []
                
                for title, content in json_data.items():
                    if not isinstance(title, str) or not isinstance(content, str):
                        continue
                    
                    # 제목에 접두사 추가
                    final_title = f"{add_prefix}{title}" if add_prefix else title
                    
                    # 기존 페이지 확인
                    curs.execute(db_change("select title from data where title = ?"), [final_title])
                    existing_page = curs.fetchone()
                    
                    if existing_page and not overwrite:
                        skipped_pages.append(final_title)
                        continue
                    
                    # 페이지 데이터 삽입/업데이트
                    if existing_page:
                        curs.execute(db_change("update data set data = ? where title = ?"), 
                                   [content, final_title])
                        updated_pages.append(final_title)
                    else:
                        curs.execute(db_change("insert into data (title, data, type) values (?, ?, ?)"), 
                                   [final_title, content, 'r'])
                        created_pages.append(final_title)
                    
                    # 히스토리 추가
                    now_time = get_time()
                    ip = ip_check()
                    
                    history_plus(conn, 
                        final_title,
                        content,
                        now_time,
                        ip,
                        'JSON 업로드',
                        '0'
                    )
                    
                    # 백링크 렌더링
                    render_set(conn, 
                        doc_name = final_title,
                        doc_data = content,
                        data_type = 'backlink'
                    )
                
                conn.commit()
                
                # 결과 반환
                result = {
                    'success': True,
                    'created': len(created_pages),
                    'updated': len(updated_pages),
                    'skipped': len(skipped_pages),
                    'created_pages': created_pages[:10],  # 최대 10개만 표시
                    'updated_pages': updated_pages[:10],
                    'skipped_pages': skipped_pages[:10]
                }
                
                return flask.jsonify(result)
                
            except Exception as e:
                return flask.jsonify({'error': f'업로드 중 오류가 발생했습니다: {str(e)}'})
        
        else:
            # GET 요청 - 업로드 폼 표시
            return easy_minify(conn, flask.render_template(skin_check(conn),
                imp = [get_lang(conn, 'json_upload'), await wiki_set(), await wiki_custom(conn), wiki_css([0, 0])],
                data = '''
                    <div class="opennamu_tool_box">
                        <h2>📄 JSON 위키 데이터 업로드</h2>
                        <p>JSON 파일로 여러 위키 페이지를 한 번에 업로드할 수 있습니다.</p>
                        
                        <div class="upload_form">
                            <form id="jsonUploadForm" enctype="multipart/form-data">
                                <div class="form_group">
                                    <label for="json_file">📁 JSON 파일 선택:</label>
                                    <input type="file" id="json_file" name="json_file" accept=".json" required>
                                    <small>최대 파일 크기: 10MB</small>
                                </div>
                                
                                <div class="form_group">
                                    <label for="add_prefix">🏷️ 페이지 제목 접두사 (선택사항):</label>
                                    <input type="text" id="add_prefix" name="add_prefix" placeholder="예: 프로젝트/">
                                    <small>모든 페이지 제목 앞에 추가될 텍스트</small>
                                </div>
                                
                                <div class="form_group">
                                    <label>
                                        <input type="checkbox" id="overwrite" name="overwrite" value="true">
                                        기존 페이지 덮어쓰기
                                    </label>
                                    <small>체크하지 않으면 기존 페이지는 건너뜁니다</small>
                                </div>
                                
                                <button type="submit" id="uploadBtn" class="opennamu_save_button">
                                    📤 업로드 시작
                                </button>
                            </form>
                        </div>
                        
                        <div id="uploadResult" style="display: none; margin-top: 20px;"></div>
                        
                        <div class="help_section">
                            <h3>📋 JSON 파일 형식</h3>
                            <p>JSON 파일은 다음과 같은 형식이어야 합니다:</p>
                            <pre><code>{
  "페이지제목1": "페이지 내용1",
  "페이지제목2": "페이지 내용2",
  "메인페이지": "= 위키 메인페이지 =\\n\\n환영합니다!"
}</code></pre>
                            
                            <h3>⚠️ 주의사항</h3>
                            <ul>
                                <li>JSON 파일은 UTF-8 인코딩이어야 합니다</li>
                                <li>페이지 제목과 내용은 모두 문자열이어야 합니다</li>
                                <li>기존 페이지와 동일한 제목이 있으면 덮어쓰기 옵션에 따라 처리됩니다</li>
                                <li>업로드된 모든 페이지는 히스토리에 기록됩니다</li>
                            </ul>
                        </div>
                    </div>
                    
                    <style>
                    .opennamu_tool_box {
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    .upload_form {
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }
                    .form_group {
                        margin-bottom: 15px;
                    }
                    .form_group label {
                        display: block;
                        margin-bottom: 5px;
                        font-weight: bold;
                    }
                    .form_group input[type="file"],
                    .form_group input[type="text"] {
                        width: 100%;
                        padding: 8px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                    }
                    .form_group small {
                        color: #666;
                        font-size: 0.9em;
                    }
                    .help_section {
                        background: #e9ecef;
                        padding: 20px;
                        border-radius: 8px;
                        margin-top: 20px;
                    }
                    .help_section pre {
                        background: #fff;
                        padding: 10px;
                        border-radius: 4px;
                        overflow-x: auto;
                    }
                    .result_success {
                        background: #d4edda;
                        color: #155724;
                        padding: 15px;
                        border-radius: 4px;
                        border: 1px solid #c3e6cb;
                    }
                    .result_error {
                        background: #f8d7da;
                        color: #721c24;
                        padding: 15px;
                        border-radius: 4px;
                        border: 1px solid #f5c6cb;
                    }
                    </style>
                    
                    <script>
                    document.getElementById('jsonUploadForm').addEventListener('submit', function(e) {
                        e.preventDefault();
                        
                        const formData = new FormData();
                        const fileInput = document.getElementById('json_file');
                        const prefixInput = document.getElementById('add_prefix');
                        const overwriteInput = document.getElementById('overwrite');
                        const uploadBtn = document.getElementById('uploadBtn');
                        const resultDiv = document.getElementById('uploadResult');
                        
                        if (!fileInput.files[0]) {
                            alert('JSON 파일을 선택해주세요.');
                            return;
                        }
                        
                        formData.append('json_file', fileInput.files[0]);
                        formData.append('add_prefix', prefixInput.value);
                        formData.append('overwrite', overwriteInput.checked ? 'true' : 'false');
                        
                        uploadBtn.disabled = true;
                        uploadBtn.textContent = '업로드 중...';
                        resultDiv.style.display = 'none';
                        
                        fetch('/tool_json_upload', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                resultDiv.className = 'result_success';
                                resultDiv.innerHTML = `
                                    <h3>✅ 업로드 완료!</h3>
                                    <p><strong>생성된 페이지:</strong> ${data.created}개</p>
                                    <p><strong>업데이트된 페이지:</strong> ${data.updated}개</p>
                                    <p><strong>건너뛴 페이지:</strong> ${data.skipped}개</p>
                                    ${data.created_pages.length > 0 ? '<p><strong>생성된 페이지 목록:</strong> ' + data.created_pages.join(', ') + '</p>' : ''}
                                    ${data.updated_pages.length > 0 ? '<p><strong>업데이트된 페이지 목록:</strong> ' + data.updated_pages.join(', ') + '</p>' : ''}
                                    ${data.skipped_pages.length > 0 ? '<p><strong>건너뛴 페이지 목록:</strong> ' + data.skipped_pages.join(', ') + '</p>' : ''}
                                `;
                            } else {
                                resultDiv.className = 'result_error';
                                resultDiv.innerHTML = `<h3>❌ 업로드 실패</h3><p>${data.error}</p>`;
                            }
                            resultDiv.style.display = 'block';
                        })
                        .catch(error => {
                            resultDiv.className = 'result_error';
                            resultDiv.innerHTML = `<h3>❌ 오류 발생</h3><p>${error.message}</p>`;
                            resultDiv.style.display = 'block';
                        })
                        .finally(() => {
                            uploadBtn.disabled = false;
                            uploadBtn.textContent = '📤 업로드 시작';
                        });
                    });
                    </script>
                ''',
                menu = [['tool', get_lang(conn, 'tool')], ['other', get_lang(conn, 'return')]]
            ))