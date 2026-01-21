from DBManager import DBManager
from dotenv import load_dotenv
import os

load_dotenv()
dbm = DBManager()

host = os.environ.get('host')
port = int(os.environ.get('port', 3306))
id = os.environ.get('user')
pw = os.environ.get('passwd')
dbName = os.environ.get('dbname')

def get_user_birthdate(u_idx):
    """회원 IDX로 생년월일 조회"""
    try :
        dbm.DBOpen(host, id, pw, dbName, port)
    except :
        print("DB연결 실패")
    try :
        sql = "SELECT u_dob, u_name FROM user WHERE u_idx = %s AND is_active = TRUE"
        dbm.OpenSQL(sql, (u_idx))
        result = dbm.getData(0)
        return result
    finally:
        dbm.DBClose()
