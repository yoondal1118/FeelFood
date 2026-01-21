# 🍽️ 감성기반 맛집 추천 서비스 (AI & Weather Based Food Recommender)

대학가 주변의 맛집을 **사용자의 감정(AI)**, **운세(AI)**, 그리고 **실시간 날씨**를 기반으로 추천해주는 Flask 웹 서비스입니다. 
단순한 별점 순위가 아닌, 현재 상황과 기분에 딱 맞는 메뉴를 제안하여 메뉴 결정 장애를 해결해 줍니다.

## ✨ 주요 기능 (Key Features)

### 1. 🤖 AI 기반 추천 (Powered by Google Gemini)
*   **감정 분석 추천**: 사용자가 현재 기분을 문장으로 입력하면, AI가 감정(희, 노, 슬, 사, 락)을 분석하여 기분 전환이나 상황에 어울리는 맛집을 추천합니다.
*   **운세 기반 추천**: 사용자의 생년월일을 기반으로 오늘의 운세를 분석하고, 행운을 불러오는 음식 카테고리를 추천합니다.

### 2. 🌤️ 실시간 날씨 기반 추천 (Rule-Based Algorithm)
*   **OpenWeatherMap API**를 활용하여 선택한 대학(지역)의 실시간 날씨와 기온을 조회합니다.
*   맑음, 흐림, 비, 눈 등의 날씨 상태와 온도(폭염, 혹한 등)를 조합하여 최적의 음식 메뉴를 우선순위대로 추천합니다. (예: 비 오는 날 -> 파전/막걸리, 짬뽕)

### 3. 🏫 대학가 맞춤 서비스
*   전국 주요 10개 대학(거점국립대 및 서울대) 주변 상권을 타겟팅하여 필터링 기능을 제공합니다.

### 4. 📊 상세한 맛집 정보 및 감정 통계
*   **메뉴 및 가격 정보**: 크롤링된 최신 메뉴 정보를 제공합니다.
*   **감정 통계 차트**: 해당 식당의 리뷰 데이터를 분석하여 방문객들이 주로 느낀 감정 비율(기쁨, 분노, 슬픔 등)을 시각화하여 제공합니다.

### 5. 👤 회원 기능
*   회원가입, 로그인, 마이페이지, 비밀번호 변경 기능을 제공합니다.
*   사용자의 생년월일 정보를 저장하여 운세 서비스 이용 시 편의를 제공합니다.

## 🛠️ 기술 스택 (Tech Stack)

*   **Backend Framework**: Python Flask
*   **Database**: MySQL (PyMySQL)
*   **AI/LLM**: Google Gemini API (Generative AI)
*   **External APIs**: OpenWeatherMap API, Kakao Map API
*   **Libraries**: Pandas, Werkzeug (Security), Requests

## ⚙️ 설치 및 실행 (Installation & Run)

### 1. 필수 라이브러리 설치
```bash
pip install flask pymysql pandas python-dotenv google-genai requests
```

### 2. 환경 변수 설정 (.env)
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 정보를 입력해야 정상 작동합니다.

```ini
# Database Configuration
host=localhost
port=3306
user=your_db_username
passwd=your_db_password
dbname=your_db_name

# Flask Configuration
SECRET_KEY=your_random_secret_key

# Google Gemini API (AI Features)
GEMINI_API_KEY=your_google_gemini_api_key
LLM_MODEL=gemini-2.5-flash 

# OpenWeatherMap API (Weather Features)
OPEN_WEATHER_API=your_openweathermap_api_key

# Kakao Map API (Frontend Map Display)
KAKAO_API_KEY=your_kakao_javascript_key
```

### 4. 어플리케이션 실행
```bash
python app.py
```
*   서버가 실행되면 브라우저에서 `http://127.0.0.1:5000`으로 접속합니다.

## 📂 프로젝트 구조 (File Structure)

```
.
├── app.py                     # Flask 메인 애플리케이션 (라우팅, 컨트롤러)
├── DBManager.py               # 데이터베이스 연결 및 쿼리 실행 클래스
├── gemini_api.py              # Google Gemini API 연동 (감정분석, 운세생성)
├── reco_based_on_weather.py   # 날씨 API 연동 및 추천 알고리즘 로직
├── service.py                 # 비즈니스 로직 (맛집 검색, 감정 통계 계산 등)
├── user_service.py            # 회원 관련 단순 조회 로직
├── templates/                 # HTML 템플릿 폴더 (index.html, detail.html 등)
├── static/                    # CSS, JS, 이미지 파일 폴더
└── .env                       # 환경 변수 파일 (비공개)
```

## 🧩 주요 로직 설명

### 감정 분석 로직 (`gemini_api.py`, `service.py`)
1.  사용자가 입력한 텍스트를 Gemini API로 전송하여 5가지 감정(희, 노, 슬, 사, 락) 중 하나로 분류합니다.
2.  DB에서 해당 감정 점수가 높은 식당들을 조회합니다.
3.  단순 리뷰 개수가 아닌, 전체 리뷰 대비 해당 감정의 **비율(Percentage)**을 계산하여 랭킹을 산정합니다.

### 날씨 추천 로직 (`reco_based_on_weather.py`)
1.  OpenWeatherMap API로 현재 기온과 날씨 상태(Clear, Rain, Snow 등)를 가져옵니다.
2.  사전에 정의된 `CATEGORY_PRIORITY_TABLE` 매핑 테이블을 통해 현재 날씨 상황에 가장 적합한 음식 카테고리 순위를 결정합니다.
3.  DB에서 해당 카테고리에 속하는 식당 목록을 불러옵니다.

## ⚠️ 주의사항
*   **API 비용**: Google Gemini API와 OpenWeatherMap API는 무료 사용량을 초과할 경우 비용이 발생할 수 있습니다.
*   **데이터베이스**: 이 웹 서비스는 크롤러를 통해 수집된 데이터(store, review, menu, emotion 테이블 등)가 DB에 존재해야 정상적으로 맛집을 추천할 수 있습니다.
*   **보안**: `.env` 파일이 GitHub 등 공개 저장소에 업로드되지 않도록 주의하세요 (`.gitignore` 설정 필수).
