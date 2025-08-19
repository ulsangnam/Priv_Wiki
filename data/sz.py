import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# 현재 host 값 확인
cursor.execute("SELECT * FROM other WHERE name = 'host'")
print(cursor.fetchall())

# host 값을 127.0.0.1로 수정
cursor.execute("UPDATE other SET data = '127.0.0.1' WHERE name = 'host'")
conn.commit()

# 수정 확인
cursor.execute("SELECT * FROM other WHERE name = 'host'")
print("수정 후:", cursor.fetchall())

conn.close()