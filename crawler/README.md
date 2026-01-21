# 🗺️ Naver Map Restaurant Crawler

이 프로젝트는 Python과 Selenium을 사용하여 네이버 지도에서 특정 지역(주로 대학교 주변)의 음식점 정보를 수집하는 크롤러입니다. 가게의 기본 정보, 메뉴 및 가격, 방문자 리뷰를 수집하여 MySQL 데이터베이스에 저장합니다.

## ✨ 주요 기능

*   **가게 목록 수집 (`store_list.py`)**: 검색어(예: "제주대 음식점")를 기반으로 가게 이름, 카테고리, 지역 정보를 수집합니다.
*   **상세 정보 및 리뷰 수집 (`naver_review.py`)**:
    *   가게의 대표 이미지 및 상세 주소 수집.
    *   메뉴 이름 및 가격 정보 수집 (포장/배달 메뉴 포함).
    *   방문자 영수증 리뷰(내용, 방문 횟수, 날짜, 작성자) 수집.
*   **데이터베이스 연동 (`DBManager.py`)**:
    *   PyMySQL을 이용한 DB 연결 및 트랜잭션 관리.
    *   Pandas DataFrame을 활용한 대량 데이터 삽입(`executemany`).
    *   중복 데이터 방지 로직 구현.
*   **안정성 및 우회**:
    *   `Headless` 브라우저 사용 및 User-Agent 설정으로 봇 탐지 회피.
    *   `iframe` 전환 및 동적 요소 로딩 대기(`WebDriverWait`) 처리.
    *   네트워크/타임아웃 오류 시 자동 재시도 로직 포함.

## 🛠️ 기술 스택 (Tech Stack)

*   **Language**: Python 3.x
*   **Web Scraping**: Selenium WebDriver
*   **Database**: MySQL (8.0+ recommended)
*   **Data Processing**: Pandas, NumPy
*   **Environment Management**: python-dotenv

## ⚙️ 설치 및 설정 (Installation)

### 1. 필수 라이브러리 설치
프로젝트 실행에 필요한 Python 패키지를 설치합니다.

```bash
pip install selenium pymysql pandas python-dotenv numpy
```

*Chrome 브라우저가 설치되어 있어야 하며, Selenium이 자동으로 드라이버를 관리하지만 버전에 맞는 `chromedriver` 이슈가 발생할 경우 수동 설정이 필요할 수 있습니다.*

### 2. 환경 변수 설정 (.env)
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 데이터베이스 접속 정보를 입력하세요.

```ini
host=localhost
port=3306
user=your_db_username
passwd=your_db_password
dbname=your_db_name
```

### 3. 데이터베이스 테이블 생성 (Schema)
MySQL에 아래 쿼리를 실행하여 필요한 테이블을 생성해야 합니다.

```sql
CREATE TABLE store (
  s_idx INT NOT NULL AUTO_INCREMENT,
  s_name VARCHAR(255),
  s_categ VARCHAR(255),
  s_location VARCHAR(255),
  s_address VARCHAR(255),
  s_img TEXT,
  s_y_coord DECIMAL(12, 9) COMMENT '위도(latitude)',
  s_x_coord DECIMAL(12, 9) COMMENT '경도(longitude)',
  PRIMARY KEY (s_idx)
) ENGINE=InnoDB;


CREATE TABLE review (
  r_idx         INT NOT NULL AUTO_INCREMENT,
  s_idx         INT NOT NULL,
  r_content     TEXT,
  r_visit_count INT,
  r_date        DATE,
  r_location VARCHAR(255),
  r_writer VARCHAR(255),
  PRIMARY KEY (r_idx),
  FOREIGN KEY (s_idx) REFERENCES store(s_idx)
) ENGINE=InnoDB;


CREATE TABLE menu (
  m_idx INT NOT NULL AUTO_INCREMENT,
  s_idx INT NOT NULL,
  m_name VARCHAR(255),
  m_price VARCHAR(255),
  m_location VARCHAR(255),
  PRIMARY KEY (m_idx),
  FOREIGN KEY (s_idx) REFERENCES store(s_idx)
) ENGINE=InnoDB;
```

## 🚀 사용 방법 (Usage)

### 1단계: 가게 목록 수집 (`store_list.py`)
특정 검색어에 대한 가게 목록을 먼저 수집하여 DB에 저장합니다.

1.  `store_list.py` 파일을 엽니다.
2.  `main()` 함수 내의 `lc` 변수를 수집하고 싶은 지역명으로 수정합니다.
    ```python
    def main():
        lc = "부산대" # 예: 제주대, 홍대, 강남역 등
        # ...
    ```
3.  코드를 실행합니다.
    ```bash
    python store_list.py
    ```

### 2단계: 상세 정보 및 리뷰 수집 (`naver_review.py`)
DB에 저장된 가게 목록을 바탕으로 상세 정보를 크롤링합니다.

1.  `naver_review.py` 파일을 엽니다.
2.  `main()` 함수 내의 `uni_list`에 1단계에서 수집한 지역명이 포함되어 있는지 확인합니다.
    ```python
    def main():
        uni_list = ['제주대', '부산대'] # 수집할 지역 리스트
        # ...
    ```
3.  코드를 실행합니다.
    ```bash
    python naver_review.py
    ```
    *   이 스크립트는 `store` 테이블에서 이미지가 없는(`s_img IS NULL`) 가게들을 대상으로 작동합니다.
    *   로그는 `log.txt` 파일에 기록됩니다.

## 📂 파일 구조

```
.
├── DBManager.py       # DB 연결, 쿼리 실행, 트랜잭션 관리 클래스
├── store_list.py      # [1단계] 네이버 지도 검색 -> 가게 목록 수집
├── naver_review.py    # [2단계] 가게별 상세 정보(메뉴, 리뷰) 수집
├── .env               # (사용자 생성 필요) DB 접속 정보
└── log.txt            # (자동 생성) 크롤링 로그 파일
```

## ⚠️ 주의사항 (Disclaimer)

*   **법적 책임**: 이 코드는 학습 및 연구 목적으로 작성되었습니다. 네이버의 서비스 이용 약관을 준수해야 하며, 과도한 요청(Traffice)은 IP 차단 등의 제재를 받을 수 있습니다. 실서비스 이용 시에는 `robots.txt` 규정을 확인하시기 바랍니다.
*   **Selector 변경**: 네이버 지도의 HTML 구조(CSS Selector, Class Name)는 수시로 변경될 수 있습니다. 코드가 작동하지 않을 경우 `By.CSS_SELECTOR` 등의 경로를 최신화해야 합니다.
*   **Chrome Driver**: 사용 중인 Chrome 브라우저 버전과 Selenium이 사용하는 드라이버 버전이 호환되지 않으면 오류가 발생할 수 있습니다.


