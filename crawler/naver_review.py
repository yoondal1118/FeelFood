import logging
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
import time
import random
import os
import numpy as np

from DBManager import DBManager
from dotenv import load_dotenv
load_dotenv()

dbm = DBManager()
host = os.environ.get('host')
port = int(os.environ.get('port', 3306))
id = os.environ.get('user')
pw = os.environ.get('passwd')
dbName = os.environ.get('dbname')

logging.basicConfig(        # 로그 기록 설정하기
    filename='log.txt',     # 파일 이름
    level=logging.INFO,    # 모든 정보 기록
    encoding='utf-8',       # TXT 파일 인코딩 설정
    format='%(asctime)s : %(levelname)s - %(message)s' )

def random_sleep(base_time) :
    random_offset = round(random.uniform(-1.0,1.0),1)
    sleep_time = max(base_time + random_offset, 0.1)
    time.sleep(sleep_time)

def search_iframe(driver, wait, search) :
    iframe = wait.until(EC.presence_of_element_located((By.ID, 'searchIframe')))
    # 상호 검색시 "조건에 맞는 업체가 없습니다"가 뜨면 다시 검색
    if not iframe:
        no_condition = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.FYvSc')))
        if no_condition:
            search.click()
            search.send_keys(Keys.ENTER)
        else :
            return
    driver.switch_to.frame(iframe)

    try :
        # 클릭이 안되는 경우가 있어서 여러번 클릭 (작동하면 냅둬라)
        target = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.place_bluelink')))
        target.click()
        [target.click() for _ in range(4)]
    except Exception as e :
        logging.info("메인 프레임으로 전환 시도 중입니다")
        print(e)
        return

def main_iframe(driver, wait) :
    # 오른쪽에 뜨는 iFrame 화면으로 들어가는 함수
    driver.switch_to.default_content()
    try :
        iframe = wait.until(EC.presence_of_element_located((By.ID, 'entryIframe')))
        driver.switch_to.frame(iframe)
    except Exception as e:
        logging.critical("메인 프레임 전환에 실패하였습니다")
        print(e)

def menu_price(store, location, wait, dbm) :
    """
    트랜잭션용 메뉴 저장 함수
    - DB 연결/종료를 하지 않음 (외부에서 관리)
    """

    # 데이터 저장 할 임시 리스트
    menu_list = []
    price_list = []
    s_idx_list = []
    location_list = []

    # 메뉴 버튼 찾기
    try :
        menu_xpath = "//span[text()='메뉴']"
        try :
            menu_span = wait.until(EC.presence_of_element_located((By.XPATH, menu_xpath)))
            menu_span.click()
        except Exception as e:
            logging.critical("메뉴 객체를 찾지 못했습니다")
            print(e)
            return -1
        
        # s_idx 먼저 찾기
        sql = "SELECT s_idx FROM store WHERE s_name = %s LIMIT 1"
        dbm.OpenSQL(sql, (store,))

        row = dbm.getData(0)
        if not row:
            print(f"[ERROR] store_name으로 s_idx 찾기 실패: {store}")
            dbm.CloseSQL()
            return -1
        
        s_idx = row["s_idx"]
        dbm.CloseSQL()

        # 메뉴 버튼을 찾음
        try :
            # 모든 메뉴의 박스 찾기
            menu_data = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.E2jtL')))
            # 각 박스를 하나씩 반복
            for menu in menu_data :
                # 각 데이터 찾아서 저장
                menu_text = menu.find_element(By.CSS_SELECTOR, "span.lPzHi").get_attribute("innerText")
                price_text = menu.find_element(By.CSS_SELECTOR,"div.GXS1X").get_attribute("innerText")
                
                # 현재 세션 중복 체크
                if menu_text in menu_list:
                    continue

                # DB 중복 체크 - CheckDuplicate 사용
                sql = "SELECT 1 FROM menu WHERE s_idx = %s AND m_name = %s LIMIT 1"
                if dbm.CheckDuplicate(sql, (s_idx, menu_text)): # 메뉴가 이미 존재하면 True
                    logging.info(f"DB에 이미 존재하는 메뉴: {menu_text}")
                    continue

                # 중복 아니면 추가
                menu_list.append(menu_text)
                price_list.append(price_text)
                s_idx_list.append(s_idx)
                location_list.append(location)

            # for문 끝난 후 (모든 메뉴를 찾아옴)
            # 새로운 메뉴만 저장
            if menu_list:  # 새로운 메뉴가 있을 때만
                menu_info = {
                    's_idx' : s_idx_list,
                    'm_name' : menu_list,
                    'm_price' : price_list,
                    'm_location' : location_list
                }
                df = pd.DataFrame(menu_info)
                dbm.InsertDataFrame(df, "menu")
                logging.info(f"{len(menu_list)}개의 새 메뉴 저장 완료")
            else :
                logging.info("저장할 새 메뉴가 없습니다 (모두 중복)")
                return
                
        # 메뉴 버튼은 있는데, 메뉴 박스가 없을때 (포장/ 매장)
        except Exception as e:
            logging.info('포장/배달 메뉴로 나뉘어져 있는 가게입니다')
            try :
                # 포장 / 매장 메뉴의 객체 박스를 찾음
                menu_data = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.MenuContent__info_detail__rCviz')))
                for menu in menu_data :
                    menu_text = menu.find_element(By.CSS_SELECTOR, "div.MenuContent__tit__313LA").get_attribute("innerText")
                    price_text = menu.find_element(By.CSS_SELECTOR,"div.MenuContent__price__lhCy9").get_attribute("innerText")
                    
                    # 현재 세션 중복 체크
                    if menu_text in menu_list:
                        continue
                    
                    # DB 중복 체크 - CheckDuplicate 사용
                    sql = "SELECT 1 FROM menu WHERE s_idx = %s AND m_name = %s LIMIT 1"
                    if dbm.CheckDuplicate(sql, (s_idx, menu_text)):
                        logging.info(f"DB에 이미 존재하는 메뉴: {menu_text}")
                        continue
                    
                    # 중복 아니면 추가
                    menu_list.append(menu_text)
                    price_list.append(price_text)
                    s_idx_list.append(s_idx)
                    location_list.append(location)

                # **새로운 메뉴만 저장**
                if menu_list:
                    # 리스트를 딕셔너리로 변환 (DataFrame 시켜야하니까)
                    menu_info = {
                    's_idx' : s_idx_list,
                    'm_name' : menu_list,
                    'm_price' : price_list,
                    'm_location' : location_list
                    }
                    df = pd.DataFrame(menu_info)
                    dbm.InsertDataFrame(df, "menu")
                    logging.info(f"{len(menu_list)}개의 새 메뉴 저장 완료")
                else :
                    logging.info("저장할 새 메뉴가 없습니다 (모두 중복)")

            # 포장 / 매장 메뉴의 객체 박스를 못찾음
            except Exception as e:
                logging.critical("상세 메뉴 객체를 찾지 못했습니다")
                return -1
            
        return True
    
    except Exception as e:
        print(f"메뉴 로직 에러: {e}")
        return -1

def find_img_address(store, location, wait, dbm) :
    """
    트랜잭션용 이미지/주소 저장 함수
    - DB 연결/종료를 하지 않음 (외부에서 관리)
    - 성공하면 True, 실패하면 -1 반환
    """
    try :
        # 이미지, 주소 CSS 셀렉터 찾기
        img = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img.K0PDV'))).get_attribute("src")
        address = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.LDgIH'))).get_attribute("innerText")
        
        # 중복 체크 추가
        check_sql = """
            SELECT s_location 
            FROM store 
            WHERE s_name = %s AND s_address = %s AND s_location != %s
        """
        
        if dbm.CheckDuplicate(check_sql, (store, address, location)):
            print(f"중복 가게 발견: {store}")
            
            # 현재 지역의 데이터 삭제
            delete_sql = "DELETE FROM store WHERE s_name = %s AND s_location = %s"
            dbm.RunSQL(delete_sql, (store, location))

            print(f"   → {location} 데이터 삭제 완료")
            return -1 # 중복이므로 실패로 처리

        # 중복 아니면 sql문에 s_img, s_address 입력
        sql = "UPDATE store SET s_img = %s, s_address = %s WHERE s_name = %s AND s_location = %s"
        datas = (img, address, store, location) # 이미지, 주소, 스토어(조건), 로케이션(조건)
        dbm.RunSQL(sql, datas)
        return True

    except Exception as e :
        logging.critical("이미지 및 주소 객체를 찾지 못했습니다")
        print(e)
        return -1

def find_review(store, driver, location, wait, dbm):
    """
    트랜잭션용 리뷰 저장 함수
    - DB 연결/종료를 하지 않음 (외부에서 관리)
    """

    # 리뷰 버튼 찾음
    review_xpath = "//span[text()='리뷰']"
    # 리뷰 최신순 버튼 찾음
    recent_xpath = "//a[text()='최신순']"
    # 방문 횟수, 작성일 셀렉터
    xpath_expression = ".//span[contains(text(), '번째')]"
    date_xpath_expression = ".//span[contains(text(), '년')]"

    previous_review_count = 0
    
    try :
        # s_idx 먼저 찾기
        sql = "SELECT s_idx FROM store WHERE s_name = %s LIMIT 1"
        dbm.OpenSQL(sql, (store,))
        row = dbm.getData(0)
        s_idx = row['s_idx'] if row else None
        dbm.CloseSQL()

        if not s_idx:
            print("s_idx를 찾을 수 없어 리뷰 수집 중단")
            return -1
        
        try:
            # 리뷰 버튼을
            review = wait.until(EC.presence_of_element_located((By.XPATH, review_xpath)))
            # JavaScript로 클릭
            driver.execute_script("arguments[0].click();", review)
            random_sleep(2)  # 리뷰 페이지 로딩 대기
        except Exception as e:
            logging.critical('리뷰로 진입하지 못했습니다')
            print(e)
            return -1
        
        # 최신순 버튼 클릭
        try :
            recent_xpath = wait.until(EC.presence_of_element_located((By.XPATH, recent_xpath)))
            driver.execute_script("arguments[0].click();", recent_xpath)
            random_sleep(2)  # 리뷰 페이지 로딩 대기
        except Exception as e :
            logging.critical("최신순 버튼을 찾지 못했습니다")

        # 스크롤 하면서 전체 리뷰 저장 시작 부분
        Flag = True
        while Flag :
            Flag = scroll(driver, wait)
            random_sleep(1)  # 페이지 로딩 대기
            review_data = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.place_apply_pui')))
            new_reviews_to_collect = review_data[previous_review_count:]
            previous_review_count += len(new_reviews_to_collect)
            for element in new_reviews_to_collect:
                try:
                    review_text = element.find_element(By.CSS_SELECTOR, "div.pui__vn15t2 > a").get_attribute("innerText")
                    visit_count = element.find_element(By.XPATH, xpath_expression).get_attribute("innerText")
                    review_date = element.find_element(By.XPATH, date_xpath_expression).get_attribute("innerText")
                    review_writer = element.find_element(By.CSS_SELECTOR, "span.pui__NMi-Dp").get_attribute("innerText")

                    # 개별 리뷰를 바로 DB에 저장
                    if save_review_to_db(s_idx, store, review_text, visit_count, review_date, location, review_writer, dbm) == -1:
                        return -1

                except Exception as e:
                    logging.warning(f"개별 리뷰 추출 또는 저장 실패: {str(e)}")
                    continue

        print(f"총 {previous_review_count}개의 리뷰 수집 완료")
        logging.info(f"총 {previous_review_count}개의 리뷰 수집 완료")
        return True
    
    except Exception as e:
        print(f"리뷰 수집 에러: {e}")
        return -1



def save_review_to_db(s_idx, store_name, review_text, visit_count, review_date, location, review_writer, dbm):
    """
    트랜잭션용 개별 리뷰 저장 함수
    - DB 연결/종료를 하지 않음 (외부에서 관리)
    """

    try:
        # 줄바꿈 제거 및 전처리
        review_text = review_text.replace('\n', ' ').strip()
        
        # 빈 리뷰는 저장 안 함
        if not review_text or review_text == '':
            return False
        
        # 날짜 형식 변환: "2025년 12월 11일 목요일" -> "2025-12-11"
        formatted_date = convert_date_format(review_date)
        
        # 방문 횟수를 정수로 변환: "5번째 방문" -> 5
        visit_count = extract_visit_number(visit_count)

        # 중복 체크
        sql = "SELECT 1 FROM review WHERE s_idx = %s AND r_content = %s AND r_date = %s AND r_writer = %s"
        if dbm.CheckDuplicate(sql, (s_idx, review_text, formatted_date, review_writer)):
            print(f"중복 리뷰 건너뜀: {store_name} - {formatted_date}")
            return -1
        
        # DB에 Insert(추가) 할 SQL문
        sql = """
            INSERT INTO review (s_idx, r_content, r_visit_count, r_date, r_location, r_writer) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # DB에 저장
        if dbm.RunSQL(sql, (s_idx, review_text, visit_count, formatted_date, location, review_writer)):
            return True
        else:
            print(f"리뷰 저장 실패: {store_name}")
            return False
            
    except Exception as e:
        logging.error(f"리뷰 DB 저장 중 오류: {e}")
        print(e)
        return False

def extract_visit_number(visit_str):
    """
    '5번째 방문' 형식에서 숫자만 추출
    """
    try:
        # "번째", "방문", 공백 제거
        # 정규표현식으로 숫자만 추출
        import re
        # 문자열에서 숫자(\d), +(1개 이상 반복) 하는 값만 가져오기
        numbers = re.findall(r'\d+', visit_str)
        
        if numbers:
            return int(numbers[0])  # 첫 번째 숫자를 정수로 변환
        else:
            return 1  # 숫자가 없으면 기본값 1
    
    except Exception as e:
        print(f"방문 횟수 변환 실패: {visit_str}, 오류: {e}")
        return 1  # 변환 실패시 기본값 1

def convert_date_format(date_str):
    """
    '2025년 12월 11일 금요일' 형식을 '2025-12-11' 형식으로 변환
    """
    try:
        # 요일 제거 (월요일, 화요일, ... 일요일)
        weekdays = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        for weekday in weekdays:
            date_str = date_str.replace(weekday, '')
        
        # "년", "월", "일" 제거 및 "-"로 대체
        date_str = date_str.replace('년', '-').replace('월', '-').replace('일', '')
        
        # 공백 제거
        date_str = date_str.strip().replace(' ', '')
        
        # "2025-12-11" 형태로 변환 (월, 일이 한자리일 경우 0 추가)
        parts = date_str.split('-')
        year = parts[0]
        month = parts[1].zfill(2)
        day = parts[2].zfill(2)
        
        return f"{year}-{month}-{day}"
    
    except Exception as e:
        print(f"날짜 변환 실패: {date_str}, 오류: {e}")
        return date_str

def scroll(driver, wait) :
    try :
        next_page = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"a.fvwqf")))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_page)
        next_page = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.fvwqf")))
        driver.execute_script("arguments[0].click();", next_page)
        return True
    except Exception as e:
        print("더 이상 스크롤을 할 수 없습니다")
        logging.info("더 이상 스크롤을 할 수 없습니다")
        print(e)
        return False

def create_driver() :
    # 드라이버 생성
    option = Options()
    # 봇 감지 회피 설정
    # 자동화 탐지 방지
    option.add_argument('--disable-blink-features=AutomationControlled')
    # 자동화 표시 제거
    option.add_experimental_option("excludeSwitches",['enable-automation'])
    # 자동화 확장 기능 사용 안함
    option.add_experimental_option('useAutomationExtension',False)
    # User_Agent 설정 (일반 사용자처럼 보이기)
    option.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')
    
    # 페이지 로드 전략 추가
    option.add_argument('--page-load-strategy=eager')
    option.add_argument("--headless")

    # 옵션을 사용하여 드라이버 생성
    driver = webdriver.Chrome(options=option)

    # WebDriver 속성 숨시기
    driver.execute_script('Object.defineProperty(navigator,"webdriver",{get:()=>undefined})')

     # 타임아웃 설정 추가 (초 단위)
    driver.set_page_load_timeout(30)   # 페이지 로드 30초 제한
    driver.set_script_timeout(30)      # 스크립트 실행 30초 제한

    wait = WebDriverWait(driver, 10)
    return driver, wait

def load_stores_from_db(target_location) :
    """DB에서 특정 지역의 가게 목록을 가져옵니다"""
    store_list = []

    try:
        # DB 연결
        if not dbm.DBOpen(host, id, pw, dbName, port):
            print("DB 연결 실패")
            return []
        
        # store 테이블에서 해당 지역의 가게 목록 조회 + 처리 건너뛴 가게만 처리하기 위한 후처리 (최신화 하려면, 뒷부분 제거)
        sql = "SELECT s_name FROM store WHERE s_location = %s " + "AND s_img IS NULL"

        if dbm.OpenSQL(sql, (target_location,)):
            total = dbm.getTotal()
            print(f"DB에서 {total}개의 가게를 찾았습니다")

            # 모든 가게 만큼 for문 돌리고, 이름을 리스트로 저장
            for i in range(total):
                store_name = dbm.getValue(i, 's_name')
                if store_name:
                    store_list.append(store_name)
            dbm.CloseSQL()
        else:
            # sql문 실행했을 때 False 나오면
            print("데이터 조회 실패")
        
        # DB 연결 종료
        dbm.DBClose()
        return store_list

    except Exception as e:
        print(f"DB에서 데이터를 가져오는 중 오류 발생: {e}")
        return []

def get_location() :
    """DB에서 중복 제거된 지역 목록을 가져옴"""
    uni_list = []

    try:
        # DB 연결
        if not dbm.DBOpen(host, id, pw, dbName, port):
            print("DB 연결 실패")
            return []
        
        # 뷰테이블 업데이트
        dbm.create_view()

        sql = "SELECT DISTINCT s_location FROM store_view;"

        if dbm.OpenSQL(sql):
            total = dbm.getTotal()
            print(f"DB에서 {total}개의 지역을 찾았습니다")

            # 모든 지역을 리스트로 저장
            for i in range(total):
                uni_name = dbm.getValue(i, 's_location')
                if uni_name:
                    uni_list.append(uni_name)
            dbm.CloseSQL()
        else:
            # sql문 실행했을 때 False 나오면
            print("데이터 조회 실패")

    except Exception as e:
        print(f"DB에서 view 데이터를 가져오는 중 오류 발생: {e}")
        return []
    finally:
        # DB 연결이 열려있으면 반드시 종료
        if dbm.con:
            dbm.DBClose()
    
    # finally 이후에 return
    return uni_list


def main() :
    # 전체 리뷰 수집 get_location() / 원하는 대학교만 골라서 수집 ['연세대', '고려대', '성균관대']
    uni_list = ['서울대 입구역', '전북대', '부산대', '충남대', '충북대', '강원대', '경북대', '경상국립대', '전남대', '제주대']

    # 드라이버 생성
    driver, wait = create_driver()

    try :
        for location in uni_list :
            # DB에서 가게 목록 불러오기
            store_list = load_stores_from_db(location)

            if len(store_list) == 0:
                print("수집할 가게가 없습니다.")
                continue

            # driver 생성
            # 우선 네이버 지도를 **대 로 화면 고정
            url = f"https://map.naver.com/p/search/{location}"
            driver.get(url)

            for idx, store in enumerate(store_list, 1):
                print(f"\n진행률: {idx}/{len(store_list)} ({idx/len(store_list)*100:.1f}%)")
                logging.info(f"진행률: {idx}/{len(store_list)}")
                
                try :
                    # 네이버지도 검색바 찾기
                    search = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.input_search')))
                    # 검색바 초기화
                    search.click()
                    search.send_keys(Keys.CONTROL + 'a')
                    search.send_keys(Keys.DELETE)

                    # 5초 잠시대기
                    time.sleep(1)
                    # 가게 이름 검색바에 입력 후 엔터
                    search.send_keys(store + Keys.ENTER)

                    print(f"{store}에 대해 수집을 시작합니다")
                    
                    search_iframe(driver, wait, search)
                    logging.info(f"{store}에 대해 수집을 시작합니다")

                    main_iframe(driver, wait)
                    
                    time.sleep(2)
                    
                    # ========== 트랜잭션 시작 ==========
                    # DB 연결 (한 번만 열어서 트랜잭션으로 묶음)
                    if not dbm.DBOpen(host, id, pw, dbName, port):
                        print("DB 연결 실패")
                        continue

                    try:
                        # autocommit을 False로 설정 (수동 트랜잭션 모드)
                        # 이렇게 하면 명시적으로 commit()을 호출하기 전까지 DB에 반영 안됨
                        dbm.con.autocommit(False)

                        # 1. 이미지, 주소 저장
                        result1 = find_img_address(store, location, wait, dbm)
                        if result1 == -1:
                            # 함수가 실패하면 rollback하고 다음 가게로
                            print(f"[ROLLBACK] {store}: 이미지/주소 수집 실패")
                            dbm.con.rollback()
                            dbm.DBClose()
                            continue
                        
                        # 2. 메뉴 가격 저장
                        result2 = menu_price(store, location, wait, dbm)
                        if result2 == -1:
                            # 함수가 실패하면 rollback하고 다음 가게로
                            print(f"[ROLLBACK] {store}: 메뉴 수집 실패")
                            dbm.con.rollback()
                            dbm.DBClose()
                            continue
                        
                        # 3. 리뷰 수집
                        result3 = find_review(store, driver, location, wait, dbm)
                        if result3 == -1:
                            # 함수가 실패하면 rollback하고 다음 가게로
                            print(f"[ROLLBACK] {store}: 리뷰 수집 실패")
                            dbm.con.rollback()
                            dbm.DBClose()
                            continue
                        
                        # ========== 세 함수 모두 성공했을 때만 commit ==========
                        dbm.con.commit()
                        print(f"[COMMIT] {store}: 모든 데이터 저장 완료 ✓")
                        logging.info(f"[COMMIT] {store}: 트랜잭션 성공")

                    except Exception as e:
                        # 예상치 못한 오류 발생시 rollback
                        print(f"[ROLLBACK] {store}: 예상치 못한 오류 - {e}")
                        logging.error(f"트랜잭션 오류: {store} - {e}")
                        dbm.con.rollback()
                        
                    finally:
                        # 트랜잭션이 끝나면 반드시 DB 연결 종료
                        dbm.DBClose()

                except TimeoutException as e:
                    logging.critical(f"타임아웃 오류 발생: {store} - {str(e)}")
                    print(f"⏱️ {store} 타임아웃으로 건너뜀")
                    # 드라이버 재생성 추가
                    try:
                        driver.quit()
                    except:
                        pass
                    driver, wait = create_driver()
                    url = f"https://map.naver.com/p/search/{location}"
                    driver.get(url)
                    time.sleep(2)
                    
                except Exception as x:
                    error_msg = str(x)
                    if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
                        logging.critical(f"네트워크 타임아웃 오류: {store}")
                        print(f"⏱️ {store} 네트워크 타임아웃으로 건너뜀")
                        driver.quit()
                        driver, wait = create_driver()
                        # 추가: 네이버 지도로 다시 이동
                        url = f"https://map.naver.com/p/search/{location}"
                        driver.get(url)
                        time.sleep(2)  # 페이지 로딩 대기
                    
                finally:
                    # 항상 기본 프레임으로 복귀
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass

            print(f"\n{location} 지역 수집 완료!")
            
    finally:
        driver.quit()
        print("\n모든 수집 작업 완료!")

if __name__ == "__main__" :
    main()