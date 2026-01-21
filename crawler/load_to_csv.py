from dotenv import load_dotenv
import mysql.connector
import pandas as pd
import os

load_dotenv()

conn = mysql.connector.connect(
    host=os.environ.get('host'),
    user=os.environ.get('user'),
    password=os.environ.get('passwd'),
    database=os.environ.get('dbname'),
    port=int(os.environ.get('port', 3306))
)

# 쿼리 작성
query = """
SELECT r.*
FROM review r
LEFT JOIN emotion e ON r.r_idx = e.r_idx
WHERE e.r_idx IS NULL;
"""

# DB → DataFrame
df = pd.read_sql(query, conn)

# CSV로 저장
df.to_csv("review.csv", index=False, encoding="utf-8-sig")

# 연결 종료
conn.close()

print("CSV 저장 완료")