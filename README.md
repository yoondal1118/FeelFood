# 🍽️ AI를 활용한 감성 기반 맛집 추천 서비스

빅데이터 수집, 인공지능(AI) 감정 분석, 그리고 웹 서비스를 결합한 **지능형 맛집 추천 플랫폼**입니다.
네이버 지도에서 수집한 방대한 리뷰 데이터를 딥러닝 모델(DistilKoBERT)로 분석하고, 날씨와 운세, 사용자의 기분에 맞춰 최적의 메뉴를 추천해 줍니다.

## 📂 프로젝트 구조 (Project Structure)

이 프로젝트는 크게 **데이터 수집(Crawler)**, **웹 서비스(Web Service)**, **감정 분석 모델링(Machine Learning)** 세 가지 파트로 구성되어 있습니다.

```bash
.
├── crawler/             # [Data Collection] 네이버 지도 맛집 및 리뷰 크롤러
├── front/               # [Service] Flask 기반 웹 애플리케이션 (AI 추천 기능 포함)
├── machine-learning/    # [Data Analysis] DistilKoBERT 기반 감정 분류 모델링
├── requirements.txt     # 설치 라이브러리 모음집
└── README.md            # (Current File)
```

---

## 🏗️ 모듈별 상세 소개

### 1. 🕷️ Crawler (데이터 수집)
네이버 지도를 통해 특정 대학가 주변의 음식점 정보, 메뉴, 그리고 방문자 리뷰를 수집하여 데이터베이스(MySQL)에 구축하는 모듈입니다.
*   **주요 기능**: 가게 목록 수집, 상세 정보(메뉴/가격/이미지) 크롤링, 리뷰 데이터 수집
*   **기술 스택**: Python, Selenium, PyMySQL
*   👉 **자세한 사용법 및 설정**: [`crawler/README.md`](./crawler/README.md) 를 참고하세요.

### 2. 🖥️ Web Service (웹 서비스)
수집된 데이터와 AI API를 활용하여 사용자에게 맛집을 추천해주는 Flask 웹 애플리케이션입니다.
*   **주요 기능**:
    *   **날씨 기반 추천**: 실시간 날씨/기온에 따른 메뉴 추천 (OpenWeatherMap)
    *   **AI 감정/운세 추천**: Gemini API를 활용한 기분 분석 및 운세별 메뉴 추천
    *   **상세 정보**: 가게 위치, 메뉴, 감정 분석 통계 그래프 제공
*   **기술 스택**: Flask, Gemini API, OpenWeatherMap API, Kakao Map API
*   👉 **자세한 실행 방법**: [`front/README.md`](./front/README.md) 를 참고하세요.

### 3. 🧠 Machine Learning (감정 분석)
수집된 리뷰 텍스트를 분석하여 6가지 세부 감정(희, 노, 슬, 사, 락, 불만)으로 라벨링하는 딥러닝 모델링 파트입니다.
*   **주요 기능**:
    *   **모델 학습**: DistilKoBERT 파인튜닝 (노이즈 주입 학습)
    *   **앙상블 예측**: 6개의 개별 감정 모델을 결합하여 편향을 보정한 최종 감정 도출
    *   **자동 라벨링**: 대량의 리뷰 데이터에 감정 태그 부착
*   **기술 스택**: TensorFlow, Transformers (Hugging Face), SoyNLP
*   👉 **모델 학습 및 추론 방법**: [`machine-learning/README.md`](./machine-learning/README.md) 를 참고하세요.

---

## ⚙️ 전체 설치 (Global Installation)

프로젝트 전체를 실행하기 위해 필요한 라이브러리는 아래 명령어로 한 번에 설치할 수 있습니다.

```bash
pip install -r requirements.txt
```

*각 모듈(Crawler, front, machine-learning)을 개별적으로 실행하려면 해당 폴더로 이동하여 각 폴더의 README 가이드를 따라주세요.*

---

## 🛠️ 전체 기술 스택 (Tech Stack)

| Category | Technologies |
| :--- | :--- |
| **Language** | Python 3.10 |
| **Web Framework** | Flask |
| **Database** | MySQL (PyMySQL) |
| **AI / LLM** | Google Gemini API, TensorFlow, Hugging Face Transformers |
| **Crawling** | Selenium WebDriver |
| **Data Processing** | Pandas, NumPy, SoyNLP |
| **External APIs** | OpenWeatherMap, Kakao Map |
