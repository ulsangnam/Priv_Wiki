#!/usr/bin/env python3
"""
PostgreSQL 설정 스크립트
"""

import json
import os
from pathlib import Path

def create_postgresql_config():
    """PostgreSQL 설정 파일을 생성합니다"""
    print("🐘 PostgreSQL 설정 파일 생성 중...")
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # PostgreSQL 설정
    postgresql_config = {
        "user": "wiki_user",
        "password": "wiki_password",
        "host": "localhost",
        "port": "5432"
    }
    
    # postgresql.json 생성
    with open(data_dir / "postgresql.json", "w", encoding="utf-8") as f:
        json.dump(postgresql_config, f, ensure_ascii=False, indent=2)
    
    # set.json 업데이트
    set_config = {
        "db_type": "postgresql",
        "db": "wiki_db"
    }
    
    with open(data_dir / "set.json", "w", encoding="utf-8") as f:
        json.dump(set_config, f, ensure_ascii=False, indent=2)
    
    print("✓ PostgreSQL 설정 파일이 생성되었습니다.")
    print(f"📋 PostgreSQL 정보:")
    print(f"   데이터베이스: wiki_db")
    print(f"   사용자: {postgresql_config['user']}")
    print(f"   비밀번호: {postgresql_config['password']}")
    print(f"   호스트: {postgresql_config['host']}")
    print(f"   포트: {postgresql_config['port']}")
    
    return True

if __name__ == "__main__":
    create_postgresql_config()