import os
from DBManager import DBManager
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import random
from dotenv import load_dotenv
load_dotenv()

dbm = DBManager()
host = os.environ.get('host')
port = int(os.environ.get('port', 3306))
id = os.environ.get('user')
pw = os.environ.get('passwd')
dbName = os.environ.get('dbname')

def random_sleep(base_time) :
    random_offset = round(random.uniform(-1.0,1.0),1)
    sleep_time = max(base_time + random_offset, 0.1)
    time.sleep(sleep_time)

def find_store(driver, wait, location) :

    current_page = 1
    """단일 가게 요소를 받아서 이름과 테마를 추출하여 리스트에 추가합니다."""
    while True :
        print(f"{current_page}페이지 수집 중")

        # 하나의 리스트에 딕셔너리 형태로 담도록 변경
        store_data = []

        # 스크롤을 맨 아래까지 내려서 모든 가게 로딩
        while scroll(driver, wait) :
            time.sleep(2)
        
        # 네이버 지도의 객체 리스트(가게 박스 전체)
        try :
            store_list = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.UEzoS")))
        except:
            print(f"{current_page}페이지에서 가게 리스트를 찾지 못했습니다.")
            break

        # 데이터 추출
        for store in store_list:
            try :
                try: # 이름 추출
                    name = store.find_element(By.CSS_SELECTOR, "span.TYaxT").get_attribute("innerText")
                except:
                    name = "Null"
                
                try: # 테마(카테고리) 추출
                    thema = store.find_element(By.CSS_SELECTOR, "span.KCMnt").get_attribute("innerText")
                except:
                    thema = "Null"
                
                # 이름과 테마를 세트로 묶어서 저장 (데이터 밀림 현상 방지)
                if name != "Null": # name 값이 존재하면
                    store_data.append({
                        'name': name,
                        'thema': thema,
                        'location': location
                    })
            except Exception as e:
                print(e)
                continue
            
        # DB 저장 함수 호출
        if store_data:
            save_to_db(store_data)
            print(f"{current_page}페이지: {len(store_data)}개 데이터 처리 완료")
        else:
            print(f"{current_page}페이지: 수집된 데이터가 없습니다.")

        # 다음 페이지 이동
        if not next_page_click(wait):
            print("마지막 페이지 도달 또는 이동 실패. 수집 종료.")
            break

        # 다음 페이지 클릭 후 로딩 대기
        print("다음 페이지 로딩 대기 중...")
        random_sleep(2.5)
        current_page += 1


def save_to_db(store_data) :
    # 인자를 딕셔너리 리스트 하나로 받아옴
    try :
        # DB 오픈
        if not dbm.DBOpen(host, id, pw, dbName, port):
            print("DB 연결에 실패했습니다.")
            return

        # 중복이 아닌 데이터만 모을 리스트
        new_names = []
        new_themas = []
        new_cities = []

        # 현재 세션에서 이미 처리한 (이름, 위치) 조합을 추적하는 set
        processed_set = set()

        print("중복 데이터 확인 중...")

        # 딕셔너리 데이터를 리스트로 분해
        for item in store_data:
            name = item['name']
            thema = item['thema']
            location = item['location']

            # 세션 내부 중복 체크 (같은 페이지 내에서 중복된 가게)
            key = (name, location)  # 이름과 위치를 튜플로 묶어서 set에 저장
            if key in processed_set:
                # 이미 처리한 가게면 건너뛰기
                continue

            # DB 중복 체크
            check_sql = "SELECT 1 FROM store WHERE s_name = %s AND s_location = %s"
            if dbm.CheckDuplicate(check_sql, (name, location)):
                continue
            
            # 중복 없으면 리스트에 넣는다
            new_names.append(name)
            new_themas.append(thema)
            new_cities.append(location)

            # 처리 완료한 가게를 set에 추가
            processed_set.add(key)

        # 데이터프레임 변환 및 저장
        if new_names:
            df = pd.DataFrame({
                's_name': new_names,
                's_categ': new_themas,
                's_location': new_cities
            })

            # DB에 저장
            if dbm.InsertDataFrame(df, "store"):
                print(f"{len(new_names)}건의 신규 가게 저장 성공")
            else:
                print("데이터 프레임 저장 실패")
        else:
            print("모든 데이터가 중복이어서 저장하지 않았습니다.")

    except Exception as e :
        print(f"DB 저장 중 오류 발생: {e}")

    finally:
        # 함수 종료 시 무조건 DB 닫기
        dbm.DBClose()


def is_scroll_end_reached(driver, element):
    script = """
        const currentScrollPosition = arguments[0].scrollTop;
        const maxScrollPosition = arguments[0].scrollHeight - arguments[0].clientHeight;
        return currentScrollPosition >= maxScrollPosition - 1; 
    """
    # JavaScript 실행 및 결과 반환
    return driver.execute_script(script, element)

def scroll(driver, wait) :
    try :
        element = wait.until(EC.presence_of_element_located((By.ID, "_pcmap_list_scroll_container")))
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;",element)
        
        # 스크롤 명령 후 화면이 움직일 시간을 줌
        time.sleep(1)

        if is_scroll_end_reached(driver, element):
            print("스크롤 가능한 요소의 맨 끝에 도달했습니다.")
            return False
        return True
    except Exception as e :
        return False

def next_page_click(wait) :
    xpath_locator = (By.XPATH, "//span[normalize-space(text())='다음페이지']/parent::a")
    try :
        next_page = wait.until(EC.presence_of_element_located(xpath_locator))
        if next_page.get_attribute('aria-disabled') == 'true':
            print("🚨 '다음페이지' 버튼이 비활성화되었습니다. 마지막 페이지입니다.")
            return False
        else :
            next_page.click()
            return True
    except Exception as e :
        print("오류가 발생하여 중단합니다")
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
    option.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36')
    option.add_argument("--headless")
    # 옵션을 사용하여 드라이버 생성
    driver = webdriver.Chrome(options=option)
    # WebDriver 속성 숨기기
    driver.execute_script('Object.defineProperty(navigator,"webdriver",{get:()=>undefined})')
    wait = WebDriverWait(driver, 10)
    return driver, wait


def main() :
    #######################################################
    lc = "제주대"
    #######################################################

    place = f"{lc} 음식점"
    location = f"{lc}"

    driver, wait = create_driver()

    # 에러 발생 시에도 브라우저 종료
    try:
        url = f"https://map.naver.com/p/search/{place}"
        driver.get(url)
        iframe = wait.until(EC.presence_of_element_located((By.ID, 'searchIframe')))
        driver.switch_to.frame(iframe)
        find_store(driver, wait, location)
    except Exception as e:
        print(f"메인 실행 중 오류 발생: {e}")
    finally:
        # 프로그램 종료 시 드라이버 메모리 해제
        driver.quit() 
        print("드라이버를 종료합니다.")

if __name__ == "__main__" :
    main()