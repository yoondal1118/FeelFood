"""
날씨 기반 음식 추천 모듈
- OpenWeather API로 실시간 날씨 조회
- Gemini API로 날씨에 맞는 음식 카테고리 추천
"""

import requests
import os
from dotenv import load_dotenv
import gemini_api

# 환경 변수 로드
load_dotenv()
API_KEY = os.getenv("OPEN_WEATHER_API")

# 지거국 10곳 좌표 정보
UNIVERSITIES = {
    "서울대학교": {"lat": 37.4599, "lon": 126.9519, "short_name": "서울대"},
    "부산대학교": {"lat": 35.2330, "lon": 129.0780, "short_name": "부산대"},
    "경북대학교": {"lat": 35.8906, "lon": 128.6122, "short_name": "경북대"},
    "전북대학교": {"lat": 35.8468, "lon": 127.1290, "short_name": "전북대"},
    "전남대학교": {"lat": 35.1760, "lon": 126.9059, "short_name": "전남대"},
    "경상국립대학교": {"lat": 35.1515, "lon": 128.0983, "short_name": "경상국립대"},
    "충북대학교": {"lat": 36.6284, "lon": 127.4560, "short_name": "충북대"},
    "충남대학교": {"lat": 36.3665, "lon": 127.3446, "short_name": "충남대"},
    "강원대학교": {"lat": 37.8695, "lon": 127.7449, "short_name": "강원대"},
    "제주대학교": {"lat": 33.4520, "lon": 126.5675, "short_name": "제주대"}
}


def get_weather_by_university(university_name):
    """
    특정 대학의 날씨 정보를 조회하는 함수
    
    Args:
        university_name (str): 대학 이름 (예: "서울대학교")
    
    Returns:
        dict: 날씨 정보 딕셔너리
            {
                "success": bool,
                "temperature": float,
                "description": str,
                "main": str (Clear, Rain, Snow, Clouds 등),
                "humidity": int,
                "wind_speed": float
            }
    """
    if not API_KEY:
        return {"success": False, "error": "OpenWeather API 키가 설정되지 않았습니다."}
    
    if university_name not in UNIVERSITIES:
        return {"success": False, "error": "존재하지 않는 대학입니다."}
    
    coord = UNIVERSITIES[university_name]
    
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": coord["lat"],
            "lon": coord["lon"],
            "appid": API_KEY,
            "units": "metric",  # 섭씨 온도
            "lang": "kr"        # 한국어 설명
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            return {
                "success": True,
                "university": university_name,
                "temperature": round(data["main"]["temp"], 1),
                "description": data["weather"][0]["description"],
                "main": data["weather"][0]["main"],  
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"].get("speed", 0),
                "feels_like": round(data["main"]["feels_like"], 1)
            }
        else:
            return {
                "success": False,
                "error": f"날씨 API 호출 실패 (상태 코드: {response.status_code})"
            }
            
    except requests.Timeout:
        return {"success": False, "error": "날씨 API 응답 시간 초과"}
    except Exception as e:
        return {"success": False, "error": f"날씨 조회 중 오류 발생: {str(e)}"}


def get_food_recommendation_by_weather(weather_data):
    """
    날씨 정보를 바탕으로 Gemini API를 통해 음식 카테고리를 추천받는 함수
    
    Args:
        weather_data (dict): get_weather_by_university()에서 반환된 날씨 정보
    
    Returns:
        dict: {
            "success": bool,
            "recommendation_text": str (Gemini가 생성한 추천 문구),
            "categories": list (추천된 음식 카테고리 리스트, 예: ["한식", "중식"])
        }
    """
    if not weather_data.get("success"):
        return {
            "success": False,
            "error": "날씨 정보가 올바르지 않습니다."
        }
    
    try:
        # Gemini API 호출을 위한 프롬프트 생성
        prompt = f"""
현재 {weather_data['university']}의 날씨 상황:
- 기온: {weather_data['temperature']}°C (체감온도: {weather_data['feels_like']}°C)
- 날씨: {weather_data['description']}
- 습도: {weather_data['humidity']}%
- 풍속: {weather_data['wind_speed']}m/s

위 날씨 상황을 고려하여 먹으면 좋을 음식을 추천해주세요.
답변은 다음 형식으로 작성해주세요:

1. 먼저 날씨 상황에 대한 공감과 재미있는 멘트 (1-2문장)
2. 이런 날씨에 어울리는 음식 카테고리 설명 (2-3문장)
3. 마지막 줄에 추천 카테고리를 다음 형식으로 작성:
   [추천 카테고리: 한식, 중식, 일식, 양식, 분식, 카페/베이커리 중 1-2개]

예시:
오늘은 비가 우중충 오는 날이군요! 이런 날엔 따뜻한 음식으로 마음을 녹여보세요.
비 오는 날에는 따끈한 국물 요리가 최고입니다. 한식의 든든한 국밥이나 찌개가 생각나는 날씨네요!
[추천 카테고리: 한식]
"""
        
        # Gemini API를 통해 추천 받기
        recommendation_text = gemini_api.get_weather_food_recommendation(prompt)
        
        if not recommendation_text:
            return {
                "success": False,
                "error": "Gemini API 응답이 없습니다."
            }
        
        # 추천 카테고리 추출
        categories = extract_categories_from_text(recommendation_text)
        
        return {
            "success": True,
            "recommendation_text": recommendation_text,
            "categories": categories
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"음식 추천 생성 중 오류: {str(e)}"
        }


def extract_categories_from_text(text):
    """
    Gemini 응답 텍스트에서 음식 카테고리를 추출하는 함수
    
    Args:
        text (str): Gemini API 응답 텍스트
    
    Returns:
        list: 추출된 카테고리 리스트
    """
    # 가능한 모든 카테고리
    all_categories = ["한식", "중식", "일식", "양식", "분식", "카페, 베이커리", "치킨", "피자"]
    
    # [추천 카테고리: ...] 형식에서 추출
    if "[추천 카테고리:" in text:
        category_section = text.split("[추천 카테고리:")[1].split("]")[0]
        extracted = []
        
        for category in all_categories:
            if category in category_section:
                extracted.append(category)
        
        if extracted:
            return extracted
    
    # 패턴 매칭 실패 시 텍스트에서 직접 검색
    found_categories = []
    for category in all_categories:
        if category in text:
            found_categories.append(category)
    
    # 중복 제거 및 최대 2개만 반환
    found_categories = list(set(found_categories))
    return found_categories[:2] if found_categories else ["한식"]  # 기본값: 한식


def get_all_universities():
    """
    모든 대학 정보를 반환하는 함수
    
    Returns:
        dict: 대학 정보 딕셔너리
    """
    return UNIVERSITIES