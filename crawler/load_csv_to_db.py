import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

# DB 연결
conn = mysql.connector.connect(
    host=os.environ.get('host'),
    user=os.environ.get('user'),
    password=os.environ.get('passwd'),
    database=os.environ.get('dbname'),
    port=int(os.environ.get('port', 3306))
)

cursor = conn.cursor()

# CSV 읽기
df = pd.read_csv("reviews_labled.csv")

# 감정 컬럼 → t_idx 매핑
emotion_map = {
    "t_happy": 1,
    "t_angry": 2,
    "t_sad": 3,
    "t_love": 4,
    "t_fun": 5,
    "t_complaint": 6
}

insert_sql = """
INSERT INTO emotion (e_score, t_idx, r_idx)
VALUES (%s, %s, %s)
"""

for _, row in df.iterrows():
    r_idx = int(row["r_idx"])

    for emo_col, t_idx in emotion_map.items():
        e_score = float(row[emo_col])

        cursor.execute(insert_sql, (
            e_score,
            t_idx,
            r_idx
        ))

conn.commit()
cursor.close()
conn.close()

print("emotion 테이블 저장 완료")
