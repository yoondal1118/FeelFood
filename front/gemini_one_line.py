import os
import pandas as pd
from google import genai
from google.genai import types
from DBManager import DBManager
from dotenv import load_dotenv

load_dotenv()
LLM_MODEL = os.getenv('LLM_MODEL')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
dbm = DBManager()
client = genai.Client(api_key=GEMINI_API_KEY)

host = os.environ.get('host')
port = os.environ.get('port', 3306)
id = os.environ.get('user')
pw = os.environ.get('passwd')
dbName = os.environ.get('dbname')


def generate_one_liner_review(store_name):
    if not dbm.DBOpen(host, id, pw, dbName, port):
        print("DB 연결 실패")
        return 
    sql = """SELECT r_content FROM review INNER JOIN store ON review.s_idx = store.s_idx WHERE store.s_name = %s"""
    dbm.OpenSQL(sql, (store_name,))
    datas = dbm.getAll()
    reviews = [data["r_content"] for data in datas]
    # 리뷰들을 보고 한줄평을 만드는 함수
    reviews_text = "\n---\n".join(reviews)
    
    prompt = f"""
당신은 리뷰 분석가입니다. '{store_name}' 가게의 리뷰들을 보고,
30자 이내의 간결한 한줄평을 작성해주세요.
리뷰를 확인하였을때 해당 가게의 핵심 메뉴를 확인하고 그 메뉴에대한 핵심내용을 추출하여 한줄평을 작성해주세요.
해당 메뉴에 어떠한 부분이 좋은지 내용이 있으면 좋겠어요. 
일반 소비고객이 한줄평을 듣고 강력한 인상이 남도록 작성해주세요.
한줄평만 작성하고 다른 설명은 하지 마세요.

--- {store_name} 리뷰 목록 ---
{reviews_text}
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7)
        )
        one_liner = response.text.strip().replace('"', '').replace("'", '')
        print(one_liner)
        return one_liner
    except Exception as e:
        print(f"    ❌ API 호출 오류: {e}")
        return "한줄평 생성 실패"



# --- 실행 ---
if __name__ == "__main__":
    generate_one_liner_review("계도리")