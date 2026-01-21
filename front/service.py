from DBManager import DBManager
from dotenv import load_dotenv
import traceback
import os

load_dotenv()

def get_dbm():
    return DBManager()

host = os.environ.get('host')
port = int(os.environ.get('port', 3306))
id = os.environ.get('user')
pw = os.environ.get('passwd')
dbName = os.environ.get('dbname')

def find_emotion(store_name, dbm):
    sql = '''SELECT t.t_emo_type, AVG(e.e_score) as avg_score
    FROM emotion e
    JOIN review r ON e.r_idx = r.r_idx
    JOIN store s ON r.s_idx = s.s_idx
    JOIN etype t ON e.t_idx = t.t_idx
    WHERE s.s_name = %s
    GROUP BY t.t_emo_type;''' 
    
    dbm.OpenSQL(sql, (store_name,))
    emotions = dbm.getAll()
    emotion_dic = {
        "희" : 0,
        "노" : 0,
        "애(슬픔)" : 0,
        "애(사랑)" : 0,
        "락" : 0
    }
    if not emotions :
        return emotion_dic
    dbm.CloseSQL()
    for emotion in emotions:
        t_emo_type = emotion.get('t_emo_type')  # '희'
        avg_score = emotion.get('avg_score')     # 0.85
        if t_emo_type in emotion_dic:
            emotion_dic[t_emo_type] = avg_score
    return emotion_dic

def find_menu(store_name, dbm):

    sql = """SELECT m.m_name, m.m_price
    FROM menu m INNER JOIN store s 
    ON m.s_idx = s.s_idx WHERE s.s_name = %s;"""
    
    dbm.OpenSQL(sql, (store_name,))
    menus = dbm.getAll()
    dbm.CloseSQL()
    
    # 초기값 설정 (항상 정의되도록)
    menu_name_list = []
    menu_price_list = []
    avg_price = "변동"
    
    # 만약 메뉴 테이블에 데이터가 존재한다면 
    if menus:
        # 메뉴 한개씩 반복
        for menu in menus[:3]:
            if menu:
                # 메뉴 이름
                menu_name = menu.get("m_name")
                menu_name_list.append(menu_name)
                
                # 메뉴 가격
                menu_price = menu.get("m_price")
                if menu_price:
                    # 평균 가격을 산출하기 위해 원, ',' 제거
                    menu_price = menu_price.replace("원", "").replace(",", "")
                    # 간혹, 변동가격으로 되어 있는 곳이 있어 조건 추가
                    if menu_price.isdigit() and int(menu_price) >= 200000:
                        menu_price = "변동"
                else:
                    menu_price = "변동"
                menu_price_list.append(menu_price)
        
        # 메뉴 평균 가격 산출
        valid_prices = [int(price) for price in menu_price_list if price.isdigit()]
        if valid_prices:
            avg_price = int(sum(valid_prices) / len(valid_prices) / 1000) * 1000
            avg_price = f"{avg_price:,}"
    
    # 항상 menu_dic 반환
    menu_dic = {
        "menu_name": menu_name_list,
        "menu_price": menu_price_list,
        "avg_price": avg_price
    }
    
    return menu_dic

def weather_store(s_location, cat_list):
    dbm = get_dbm()
    # DB 연결 시도
    if not dbm.DBOpen(host, id, pw, dbName, port):
        print("DB 연결 실패")
        return []
    
    # 최종적으로 {카테고리 : 가게 정보} 가 담긴 리스트로 반환하기 위해 생성
    restaurant_list = []

    try:
        # 카테고리 리스트에서 카테고리 한개씩 산출
        for cat in cat_list:
            # 가게 정보를 담는 리스트
            store_list = []
            # 카테고리, 위치에 맞는 가게 정보 DB에서 조회
            sql = """SELECT s.*, v.major_categ 
                FROM store s INNER JOIN vw_store_major_category v ON s.s_idx = v.s_idx
                WHERE v.major_categ = %s AND s.s_location = %s"""
            # DB에서 데이터 가져오기
            if not dbm.OpenSQL(sql, (cat,s_location)):
                print(f"{cat} 카테고리 조회 실패")
                continue
            # 한 카테고리에 여러 가게가 있으니 전체를 가져와야함
            datas = dbm.getAll()
            dbm.CloseSQL()
            
            # 카테고리 안에 가게 정보가 있을 때만 처리
            if datas:
                for data in datas:
                    # 가게 주소가 null일 경우 아직 수집 전이니 패스
                    if data.get('s_address') is None :
                        continue
                    # 가게 이름 저장
                    store_name = data.get("s_name")
                    # 메뉴 정보를 담을 함수 호출
                    menu_dic = find_menu(store_name, dbm)
                    # 감정 정보를 담을 함수 호출
                    emotion_dic = find_emotion(store_name, dbm)
                    # 가게 정보를 딕셔너리로 저장
                    store_dic = {
                        's_idx': data.get('s_idx'),
                        'name': store_name,
                        'address': data.get('s_address'),
                        'img': data.get('s_img'),
                        'menu' : menu_dic,
                        'emotion_score' : emotion_dic
                    }
                    # store_list에 딕셔너리 저장
                    store_list.append(store_dic)
            # 최종적으로, restaurants 딕셔너리엔 카테고리 : [가게 정보]가 담김
            restaurants = {
                "cat": cat,
                "store_list": store_list
            }
            # restaurant_list에는 카테고리별로 가게정보가 담긴 딕셔너리가 리스트로 저장됨
            restaurant_list.append(restaurants)
    
    except Exception as e:
        print(f"오류 발생: {e}")
        traceback.print_exc()

    finally:
        # DB 연결이 되어있을 때만 종료
        if dbm.con is not None:
            dbm.DBClose()
    
    return restaurant_list

def find_store(emotion, s_location, cat_list, count, review_count):
    dbm = get_dbm()
    emotion_column_map = {
        "희": "happy_cnt",
        "노": "angry_cnt",
        "애(슬픔)": "sad_cnt",
        "애(사랑)": "love_cnt",
        "락": "fun_cnt"
    }
    
    if not dbm.DBOpen(host, id, pw, dbName, port):
        print("DB 연결 실패")
        return []
    
    restaurant_list = []
    
    try:
        # ⭐ 핵심 개선: 모든 카테고리를 한 번에 조회
        placeholders = ', '.join(['%s'] * len(cat_list))
        
        # ⭐ 메뉴까지 한 번에 JOIN
        sql = f"""
            SELECT 
                s.s_idx, 
                s.s_name, 
                s.s_address, 
                s.s_img, 
                s.s_location, 
                v.major_categ,
                m.m_idx,    -- 메뉴 고유 번호
                m.m_name,      -- 메뉴 이름
                m.m_price,     -- 메뉴 가격
                ROUND(sec.happy_cnt * 100.0 / NULLIF(sec.happy_cnt + sec.angry_cnt + sec.sad_cnt + sec.love_cnt + sec.fun_cnt, 0), 2) as `희`,
                ROUND(sec.angry_cnt * 100.0 / NULLIF(sec.happy_cnt + sec.angry_cnt + sec.sad_cnt + sec.love_cnt + sec.fun_cnt, 0), 2) as `노`,
                ROUND(sec.sad_cnt * 100.0 / NULLIF(sec.happy_cnt + sec.angry_cnt + sec.sad_cnt + sec.love_cnt + sec.fun_cnt, 0), 2) as `애슬픔`,
                ROUND(sec.love_cnt * 100.0 / NULLIF(sec.happy_cnt + sec.angry_cnt + sec.sad_cnt + sec.love_cnt + sec.fun_cnt, 0), 2) as `애사랑`,
                ROUND(sec.fun_cnt * 100.0 / NULLIF(sec.happy_cnt + sec.angry_cnt + sec.sad_cnt + sec.love_cnt + sec.fun_cnt, 0), 2) as `락`,
                -- ⭐ 정렬 우선순위를 위한 감정 점수
                ROUND(sec.{emotion_column_map[emotion]} * 100.0 / NULLIF(sec.happy_cnt + sec.angry_cnt + sec.sad_cnt + sec.love_cnt + sec.fun_cnt, 0), 2) as emotion_score
            FROM store s
            INNER JOIN vw_store_major_category v ON s.s_idx = v.s_idx
            INNER JOIN store_emotion_count_table sec ON s.s_idx = sec.s_idx
            LEFT JOIN menu m ON s.s_idx = m.s_idx  -- 메뉴 JOIN
            WHERE v.major_categ IN ({placeholders})  -- 모든 카테고리 한번에
            AND (sec.happy_cnt + sec.angry_cnt + sec.sad_cnt + sec.love_cnt + sec.fun_cnt) > {review_count}
            AND s.s_location = %s
            ORDER BY v.major_categ, emotion_score DESC, s.s_idx, m.m_idx
        """
        
        params = tuple(cat_list) + (s_location,)
        
        if not dbm.OpenSQL(sql, params):
            print("가게 조회 실패")
            return []
            
        datas = dbm.getAll()
        dbm.CloseSQL()
        
        # ⭐ 메모리에서 데이터 그룹핑 및 개수 제한
        category_store_map = {}
        
        for data in datas:
            if data.get('s_address') is None:
                continue
            
            cat = data.get('major_categ')
            s_idx = data.get('s_idx')
            
            if cat not in category_store_map:
                category_store_map[cat] = {}
            
            # ⭐ 카테고리별 개수 제한 (count 적용)
            if s_idx not in category_store_map[cat]:
                # 이미 count 개수만큼 있으면 더 추가 안 함
                if len(category_store_map[cat]) >= count:
                    continue
                    
                category_store_map[cat][s_idx] = {
                    's_idx': s_idx,
                    'name': data.get('s_name'),
                    'address': data.get('s_address'),
                    'img': data.get('s_img'),
                    'menus': []
                }
            
            # 메뉴 정보 추가
            if data.get('m_name') is not None:
                menu_info = {
                    'name': data.get('m_name'),
                    'price': data.get('m_price')
                }
                category_store_map[cat][s_idx]['menus'].append(menu_info)
        
        # 최종 결과 구성
        for cat in cat_list:
            store_list = []
            
            if cat in category_store_map:
                for s_idx, store_data in category_store_map[cat].items():
                    # 메뉴 처리
                    menu_dic = process_menu_data(store_data['menus'])
                    
                    store_dic = {
                        'name': store_data['name'],
                        'address': store_data['address'],
                        'img': store_data['img'],
                        'menu': menu_dic
                    }
                    store_list.append(store_dic)
            
            restaurants = {
                "cat": cat,
                "store_list": store_list
            }
            restaurant_list.append(restaurants)
    
    except Exception as e:
        print(f"오류 발생: {e}")
        traceback.print_exc()

    finally:
        if dbm.con is not None:
            dbm.DBClose()
    
    return restaurant_list


# 메뉴 데이터 처리 (DB 쿼리 없이 메모리에서 처리)
def process_menu_data(menus):
    """
    메뉴 리스트를 받아서 find_menu와 동일한 결과 반환
    차이점: DB 조회 없이 이미 가져온 데이터를 처리
    
    menus: [{'name': '김치찌개', 'price': '8,000원'}, ...]
    """
    menu_name_list = []
    menu_price_list = []
    avg_price = "변동"
    
    # 메뉴가 있으면 처리 (최대 3개만)
    if menus:
        for menu in menus[:3]:
            if menu:
                # 메뉴 이름
                menu_name = menu.get("name")
                menu_name_list.append(menu_name)
                
                # 메뉴 가격
                menu_price = menu.get("price")
                if menu_price:
                    # 평균 가격 산출을 위해 원, ',' 제거
                    menu_price = menu_price.replace("원", "").replace(",", "")
                    # 변동가격 처리 (20만원 이상은 변동으로 간주)
                    if menu_price.isdigit() and int(menu_price) >= 200000:
                        menu_price = "변동"
                else:
                    menu_price = "변동"
                menu_price_list.append(menu_price)
        
        # 평균 가격 계산
        valid_prices = [int(price) for price in menu_price_list if price.isdigit()]
        if valid_prices:
            # 1000원 단위로 반올림
            avg_price = int(sum(valid_prices) / len(valid_prices) / 1000) * 1000
            avg_price = f"{avg_price:,}"
    
    # 결과 딕셔너리 반환
    menu_dic = {
        "menu_name": menu_name_list,
        "menu_price": menu_price_list,
        "avg_price": avg_price
    }
    
    return menu_dic

def get_stores_by_category(s_categ):
    dbm = get_dbm()
    """카테고리(업종)로 가게 리스트 조회"""
    try:
        # 1. DB 연결 시도
        if not dbm.DBOpen(host, id, pw, dbName, port):
            print("DB 연결 실패")
            return []
            
        # 2. SQL 문법 수정 (AND 제거)
        sql = """
            SELECT * FROM store 
            WHERE s_categ = %s
            LIMIT 10
        """
        
        # 3. 매개변수를 반드시 튜플 (value,) 형태로 전달
        if not dbm.OpenSQL(sql, (s_categ,)):
            print(f"{s_categ} 조회 실패")
            return []
            
        results = dbm.getAll()
        dbm.CloseSQL()
        
        # 결과가 None인 경우를 대비해 빈 리스트 반환 처리
        return results if results else []
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return []
    finally:
        dbm.DBClose()

def get_monthly_emotion_data(s_idx):
    dbm = get_dbm()
    """
    특정 가게의 최근 12개월 월별 감정 데이터를 가져오는 함수
    """
    # DB 연결 시도
    if not dbm.DBOpen(host, id, pw, dbName, port):
        print("DB 연결 실패")
        return {
            'months': [],
            'review_counts': [],
            'emotions': {'희': [], '노': [], '애(슬픔)': [], '애(사랑)': [], '락': []}
        }
    
    try:
        # SQL 쿼리: 최근 12개월 월별 감정 데이터 조회
        # 🔥 %Y-%m을 %%Y-%%m으로 변경!
        sql = """
        SELECT 
            DATE_FORMAT(r.r_date, '%%Y-%%m') AS month,
            COUNT(DISTINCT r.r_idx) AS review_count,
            
            -- 각 감정별 비율 계산 (대표 감정 기준)
            ROUND(
                SUM(CASE WHEN re.t_idx = 1 THEN 1 ELSE 0 END) * 100.0 / 
                NULLIF(COUNT(DISTINCT r.r_idx), 0), 
                1
            ) AS happy_ratio,
            
            ROUND(
                SUM(CASE WHEN re.t_idx = 2 THEN 1 ELSE 0 END) * 100.0 / 
                NULLIF(COUNT(DISTINCT r.r_idx), 0), 
                1
            ) AS angry_ratio,
            
            ROUND(
                SUM(CASE WHEN re.t_idx = 3 THEN 1 ELSE 0 END) * 100.0 / 
                NULLIF(COUNT(DISTINCT r.r_idx), 0), 
                1
            ) AS sad_ratio,
            
            ROUND(
                SUM(CASE WHEN re.t_idx = 4 THEN 1 ELSE 0 END) * 100.0 / 
                NULLIF(COUNT(DISTINCT r.r_idx), 0), 
                1
            ) AS love_ratio,
            
            ROUND(
                SUM(CASE WHEN re.t_idx = 5 THEN 1 ELSE 0 END) * 100.0 / 
                NULLIF(COUNT(DISTINCT r.r_idx), 0), 
                1
            ) AS fun_ratio
            
        FROM review r
        
        -- 각 리뷰의 대표 감정 가져오기 (가장 높은 점수의 감정)
        LEFT JOIN (
            SELECT 
                e.r_idx,
                e.t_idx
            FROM emotion e
            JOIN (
                SELECT r_idx, MAX(e_score) AS max_score
                FROM emotion
                GROUP BY r_idx
            ) m ON e.r_idx = m.r_idx AND e.e_score = m.max_score
        ) re ON r.r_idx = re.r_idx
        
        WHERE r.s_idx = %s
          AND r.r_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
          
        GROUP BY DATE_FORMAT(r.r_date, '%%Y-%%m')
        ORDER BY month ASC
        """
        
        # SQL 실행
        if not dbm.OpenSQL(sql, (s_idx,)):
            print(f"가게 {s_idx}의 월별 데이터 조회 실패")
            return {
                'months': [],
                'review_counts': [],
                'emotions': {'희': [], '노': [], '애(슬픔)': [], '애(사랑)': [], '락': []}
            }
        
        # 결과 가져오기
        results = dbm.getAll()
        dbm.CloseSQL()
        
        # 결과를 정리해서 반환할 형태로 변환
        months = []
        review_counts = []
        emotions = {
            '희': [],
            '노': [],
            '애(슬픔)': [],
            '애(사랑)': [],
            '락': []
        }
        
        # 결과가 있으면 데이터 정리
        if results:
            for row in results:
                # 월 추가 (예: '2024-01')
                months.append(row.get('month'))
                
                # 리뷰 개수 추가
                review_counts.append(row.get('review_count', 0))
                
                # 각 감정 비율 추가 (None이면 0으로 처리)
                emotions['희'].append(row.get('happy_ratio') or 0)
                emotions['노'].append(row.get('angry_ratio') or 0)
                emotions['애(슬픔)'].append(row.get('sad_ratio') or 0)
                emotions['애(사랑)'].append(row.get('love_ratio') or 0)
                emotions['락'].append(row.get('fun_ratio') or 0)
        
        # 🔥 디버깅: 결과 출력
        print(f"✅ SQL 조회 성공! 결과 개수: {len(results) if results else 0}")
        print(f"✅ months: {months}")
        print(f"✅ review_counts: {review_counts}")
        
        # 최종 결과 반환
        return {
            'months': months,
            'review_counts': review_counts,
            'emotions': emotions
        }
        
    except Exception as e:
        print(f"월별 감정 데이터 조회 오류: {e}")
        traceback.print_exc()
        return {
            'months': [],
            'review_counts': [],
            'emotions': {'희': [], '노': [], '애(슬픔)': [], '애(사랑)': [], '락': []}
        }
        
    finally:
        # DB 연결 종료
        if dbm.con is not None:
            dbm.DBClose()

def get_store_idx(store_name):
    dbm = get_dbm()
    """
    가게 이름으로 s_idx를 조회하는 함수
    
    Args:
        store_name (str): 가게 이름
        
    Returns:
        int: 가게 고유 번호 (s_idx), 없으면 None
    """
    
    # DB 연결 시도
    if not dbm.DBOpen(host, id, pw, dbName, port):
        print("DB 연결 실패")
        return None
    
    try:
        # SQL 쿼리
        sql = "SELECT s_idx FROM store WHERE s_name = %s LIMIT 1"
        
        # SQL 실행
        if not dbm.OpenSQL(sql, (store_name,)):
            print(f"가게 {store_name}의 s_idx 조회 실패")
            return None
        
        # 결과 가져오기
        result = dbm.getOne()
        dbm.CloseSQL()
        
        # s_idx 반환
        if result:
            return result.get('s_idx')
        else:
            return None
            
    except Exception as e:
        print(f"s_idx 조회 오류: {e}")
        traceback.print_exc()
        return None
        
    finally:
        # DB 연결 종료
        if dbm.con is not None:
            dbm.DBClose()

def find_store_by_fortune(s_location, cat_list):
    """운세 기반 음식 카테고리로 가게 찾기 (weather_store와 동일)"""
    return weather_store(s_location, cat_list)

def detail_store(s_name):
    dbm = get_dbm()
    """가게 상세 정보 조회"""
    # DB 연결 시도
    if not dbm.DBOpen(host, id, pw, dbName, port):
        print("DB 연결 실패")
        return None
    sql = "select * from store where s_name=%s"
    dbm.OpenSQL(sql, (s_name,))
    data = dbm.getData(0)
    dbm.CloseSQL()
    menu_dic = find_menu(s_name, dbm)
    emotion_dic = find_emotion(s_name, dbm)
    dbm.DBClose()
    store_dic = {
        's_idx': data.get('s_idx'),
        'name': data.get('s_name'),
        'address': data.get('s_address'),
        'img': data.get('s_img'),
        'menu' : menu_dic,
        'emotion_score' : emotion_dic,
        'x_coord' : data.get('s_x_coord'),
        'y_coord' : data.get('s_y_coord')
    }
    return store_dic
 
