# Flask 라이브러리에서 필요한 기능들을 가져옵니다
from flask import Flask, render_template, request, redirect, session, jsonify
import random
import gemini_api
import service
import user_service
import random
import reco_based_on_weather
import os
from DBManager import DBManager
# ======================
# 회원 기능용 모듈
# ======================
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

# ==========================================
# 라우팅 함수들 (URL 경로별 처리)
# ==========================================

@app.route("/")
def index():
    userid = session.get('userid')   # 로그인 안 했으면 None
    return render_template("index.html", userid=userid)


@app.route('/main_list', methods=['POST', 'GET'])
def main_list():
    """메인 리스트 페이지를 보여주는 함수"""

    # POST와 GET 모두에서 location 가져오기
    if request.method == 'POST':
        s_location = request.form.get('university', '전북대')
        request_type = request.form.get('type')
    else:
        s_location = request.args.get('location', '전북대')
        request_type = request.args.get('type')

    if s_location == '서울대' :
        s_location = '서울대 입구역'

    if s_location == '경상대' :
        s_location = '경상국립대'

    # Weather 기반 추천
    if request_type == 'weather':
        categories_param = request.args.get('categories')  # "한식|고기/구이/치킨|..."

        if categories_param :
            # 날씨 기반 추천
            ordered_categories = categories_param.split('|')
            restaurant_list = service.weather_store(s_location, ordered_categories)

            # 순서대로 recommendations 생성
            recommendations = {}
            for category in ordered_categories :
                for restaurant in restaurant_list :
                    if restaurant.get('cat') == category :
                        store_list = restaurant.get('store_list', [])
                        recommendations[category] = (
                            random.sample(store_list, 3) if len(store_list) >= 3 else store_list
                        )
                        break

            return render_template(
                'main_list.html',
                selected_type="weather",
                selected_value=None,
                recommendations=recommendations,
                ordered_categories=ordered_categories,
                location=s_location
            )
    
    # 2. Fortune 기반 추천
    if request_type == 'fortune':
        categories_param = request.args.get('categories')
        
        if categories_param:
            ordered_categories = categories_param.split('|')
            restaurant_list = service.find_store_by_fortune(s_location, ordered_categories)
            
            recommendations = {}
            for category in ordered_categories:
                for restaurant in restaurant_list:
                    if restaurant.get('cat') == category:
                        store_list = restaurant.get('store_list', [])
                        recommendations[category] = (
                            random.sample(store_list, 3) if len(store_list) >= 3 else store_list
                        )
                        break
            
            return render_template(
                'main_list.html',
                selected_type="fortune",
                recommendations=recommendations,
                ordered_categories=ordered_categories,
                location=s_location
            )

    # Emotion 기반 추천
    emotion = None
    if request.method == 'POST':
        emotion_text = request.form.get('selection')
        emotion = gemini_api.emotion_analyze(emotion_text)
        if emotion is None or emotion == '기':
            # 에러 메시지를 쿼리 파라미터로 전달하면서 index로 리다이렉트
            return redirect('/?error=emotion_analysis_failed')
        emotion_map = {'슬': '애(슬픔)', '사': '애(사랑)'}
        emotion = emotion_map.get(emotion, emotion)

        return redirect(f'/main_list?emotion={emotion}&location={s_location}')
    else:
        emotion = request.args.get("emotion")
    if emotion :
        cat_list = ["한식", "일식", "카페/디저트", "양식/브런치", "고기/구이/치킨", "중식/아시아", "술집/이자카야", "기타"]
        restaurant_list = service.find_store(emotion, s_location, cat_list, 3, 20)
        
        recommendations = {
            cat: random.sample(store_list, 3) if len(store_list) >= 3 else store_list
            for restaurant in restaurant_list
            if (cat := restaurant.get('cat')) and (store_list := restaurant.get('store_list'))
        }

        return render_template(
            'main_list.html',
            selected_type="emotion",
            recommendations=recommendations,
            selected_value=emotion,
            location = s_location
        )
    
    # 아무 조건도 안맞으면 기본 페이지
    return render_template(
    'main_list.html', 
    location=s_location,
    recommendations={},
    selected_type=None,
    selected_value=None,
    ordered_categories=[]
)

@app.route('/sub_list')
def sub_list():
    """서브 리스트 페이지를 보여주는 함수"""
    category = request.args.get('category')
    emotion = request.args.get('emotion')

    # URL에서 location 받기, 없으면 전북대
    s_location = request.args.get('location', '전북대')
    if s_location == '서울대' :
        s_location = '서울대 입구역'

    if s_location == '경상대' :
        s_location = '경상국립대'

    cat_list = [category]
    if emotion :
        restaurant_list = service.find_store(emotion, s_location, cat_list, 100, 0)
    else :
        restaurant_list = service.weather_store(s_location, cat_list)
    return render_template(
        'sub_list.html',
        category=category,
        restaurants=restaurant_list[0]['store_list'],
        location = s_location
    )


@app.route('/detail')
def detail():
    kakao_api_key = os.environ.get('KAKAO_API_KEY')

    """가게 상세 페이지를 보여주는 함수"""
    category = request.args.get('category')
    restaurant_name = request.args.get('name')
    
    # URL에서 location 받기, 없으면 전북대
    s_location = request.args.get('location', '전북대')
    if s_location == '서울대' :
        s_location = '서울대 입구역'
    
    if s_location == '경상대' :
        s_location = '경상국립대'


    print(f"\n{'='*50}")
    print(f"🔍 Detail 페이지 디버깅 시작")
    print(f"카테고리: {category}")
    print(f"가게 이름: {restaurant_name}")
    print(f"{'='*50}\n")

    # 기존 가게 정보 가져오기
    restaurant_info = service.detail_store(restaurant_name)

    # 가게를 찾지 못한 경우 에러 처리
    if not restaurant_info:
        return "가게를 찾을 수 없습니다.", 404

    print(f"✅ 가게 정보 찾음: {restaurant_info.get('name')}")

    # s_idx 가져오기
    s_idx = restaurant_info.get('s_idx')
    print(f"✅ s_idx: {s_idx}")

    # s_idx가 없으면 조회
    if not s_idx:
        print("⚠️ s_idx가 없어서 다시 조회합니다.")
        s_idx = service.get_store_idx(restaurant_name)
        print(f"✅ 조회된 s_idx: {s_idx}")

    # 월별 감정 데이터 가져오기
    # monthly_data = service.get_monthly_emotion_data(s_idx)

    # print(f"\n{'='*50}")
    # print(f"📊 월별 데이터 결과:")
    # print(f"months: {monthly_data['months']}")
    # print(f"review_counts: {monthly_data['review_counts']}")
    # print(f"emotions 희: {monthly_data['emotions']['희']}")
    # print(f"emotions 노: {monthly_data['emotions']['노']}")
    # print(f"emotions 애(슬픔): {monthly_data['emotions']['애(슬픔)']}")
    # print(f"emotions 애(사랑): {monthly_data['emotions']['애(사랑)']}")
    # print(f"emotions 락: {monthly_data['emotions']['락']}")
    # print(f"{'='*50}\n")

    # 최대 리뷰 개수 계산
    # max_review_count = 1
    # if monthly_data['review_counts']:
    #     max_review_count = max(monthly_data['review_counts'])

    # print(f"✅ max_review_count: {max_review_count}")

    # 가게의 현재 감성 중 최고 점수
    scores = restaurant_info.get("emotion_score", {})
    max_score = max(scores.values()) if scores else 0

    print(f"✅ max_score: {max_score}")
    print(f"\n{'='*50}\n")

    return render_template(
        'detail.html',
        max_score=max_score,
        restaurant=restaurant_info,
        # monthly_data=monthly_data,
        # max_review_count=max_review_count,
        kakao_api_key=kakao_api_key
    )

@app.route('/api/monthly_emotion/<int:s_idx>')
def get_monthly_emotion_api(s_idx):
    """월별 감정 데이터를 JSON으로 반환하는 API"""
    try:
        monthly_data = service.get_monthly_emotion_data(s_idx)
        
        return jsonify({
            'success': True,
            'data': {
                'months': monthly_data['months'],
                'review_counts': monthly_data['review_counts'],
                'emotions': monthly_data['emotions']
            }
        })
    except Exception as e:
        print(f"API 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ==========================================
# 🔮 운세 관련 라우팅 (새로 추가된 기능)
# ==========================================

@app.route('/fortune')
def fortune():
    location = request.args.get('location')

    # 로그인 세션이 있으면
    if 'u_idx' in session:
        # 👉 운세 결과 페이지로
        return redirect(f'/fortune_result?location={location}')

    # 로그인 안 되어 있으면
    return redirect(f'/fortune_login')

@app.route('/fortune_login', methods=['GET', 'POST'])
def fortune_login():
    """운세 조회를 위한 로그인 안내 또는 자동 리다이렉트"""

    # 1. 이미 로그인 세션(user_idx)이 있는 경우 바로 처리
    if 'user_idx' in session:
        u_idx = session.get('user_idx')
        user_data = user_service.get_user_birthdate(u_idx)

        if user_data:
            # 세션 정보를 운세 서비스용 키에 맞춤 (필요시)
            session['u_idx'] = u_idx
            session['u_name'] = user_data['u_name']
            session['u_dob'] = user_data['u_dob'].strftime("%Y%m%d")
            return redirect('/fortune_result')

    # 2. POST 요청 (fortune_login.html에서 직접 번호를 입력한 경우 - 현재 구조에선 드묾)
    if request.method == 'POST':
        u_idx = request.form.get('u_idx')
        user_data = user_service.get_user_birthdate(u_idx)

        if not user_data:
            return render_template('fortune_login.html', error="존재하지 않는 회원입니다.")

        session['u_idx'] = u_idx
        session['u_name'] = user_data['u_name']
        session['u_dob'] = user_data['u_dob'].strftime("%Y%m%d")
        return redirect('/fortune_result')

    # 3. 로그인 안 된 상태면 안내 페이지(fortune_login.html) 보여주기
    return render_template('fortune_login.html')

@app.route('/fortune_result')
def fortune_result():
    # user_idx나 u_idx 중 하나라도 없으면 로그인 페이지로
    if 'user_idx' not in session and 'u_idx' not in session:
        return redirect('/fortune_login')
    
    location = request.args.get('location')
    u_name = session.get('u_name')
    birth_date = session.get('u_dob')

    # AI로부터 운세 텍스트와 카테고리 리스트를 동시에 받음
    fortune_text, categories = gemini_api.generate_fortune_and_food(birth_date)
    print(categories)
    categories_encoded = "|".join(categories)
    print("운세 카테고리 리스트:", categories)
    print("운세 카테고리 encoded:", categories_encoded)

    # HTML로 데이터 전달
    return render_template(
        'fortune_result.html',
        u_name=u_name,
        fortune_text=fortune_text,
        categories_encoded=categories_encoded,
        location=location
    )



# ==========================================
# 🌤️ 날씨 기반 추천 라우팅 (새로 추가)
# ==========================================

@app.route('/weather_select')
def weather_select():
    """날씨 기반 추천을 위한 지역(대학) 선택 페이지"""
    try:
        universities = reco_based_on_weather.get_all_universities()
        return render_template('weather_select.html', universities=universities)
    except Exception as e:
        app.logger.error(f"대학 목록 로드 오류: {str(e)}")
        return render_template('weather_select.html',
                               universities={}, error="대학 목록을 불러올 수 없습니다.")


@app.route('/weather_result')
def weather_result():
    """선택한 지역의 날씨 조회 및 음식 추천 페이지"""
    university = request.args.get('location')

    # 파라미터 검즘
    if not university:
        return render_template('weather_result.html', error="지역을 선택해주세요.")

    try :
        # 대학교 이름에서 지역명 추출 (서울대학교 -> 서울대)
        universities = reco_based_on_weather.get_all_universities()
        location = universities.get(university, {}).get('short_name', '')

        if not location:
            return render_template('weather_result.html',
                                 error="해당 대학의 위치 정보를 찾을 수 없습니다.")

        # OpenWeather API로 실시간 날씨 조회
        weather_data = reco_based_on_weather.get_weather_by_university(university)

        if not weather_data.get('success'):
            return render_template('weather_result.html',
                                error=weather_data.get('error', '날씨 정보를 가져올 수 없습니다.'))

        # Rule-Based 음식 카테고리 추천 (우선순위 순으로 정렬)
        recommendation = reco_based_on_weather.get_food_recommendation_by_weather(weather_data)

        # 음식 추천 실패 시 에러 처리
        if not recommendation.get('success'):
            return render_template('weather_result.html', weather=weather_data,
                                error=recommendation.get('error', '음식 추천을 생성할 수 없습니다.'))

        # 이미 우선순위 순으로 정렬된 카테고리 리스트 (1위 -> 7위)
        categories = recommendation.get('categories', [])
        categories_encoded = "|".join(categories)

        print(f"🎯 Rule-Based 추천 카테고리 (우선순위 순): {categories}")
        print(f"📍 지역: {location}")

        # 템플릿에 전달
        return render_template('weather_result.html',
                             weather=weather_data,
                             recommendation_text=recommendation.get('recommendation_text', ''),
                             categories=categories,  # ✅ 1위부터 7위까지 순서대로
                             categories_encoded=categories_encoded,
                             location=location)
    except Exception as e:
        # 오류를 콘솔에 출력 (디버깅용)
        print(f"❌ 오류 발생: {e}")

        # 사용자에게 오류 페이지 표시
        return render_template('weather_result.html',
                            error="처리 중 오류가 발생했습니다. 다시 시도해주세요.")


# ==========================================
# Flask 앱 실행
# ==========================================

# ================= DB 초기화 =================
dbm = DBManager()

host = os.environ.get('host')
port = int(os.environ.get('port', 3306))
id = os.environ.get('user')
pw = os.environ.get('passwd')
dbName = os.environ.get('dbname')


@app.route("/login")
def login_page():
    return render_template("login.html") # 로그인 화면

@app.route("/signup")
def signup_page():
    return render_template("signup.html") # 회원가입 화면

# ==========================================
# 마이페이지 관련 라우팅
# ==========================================

@app.route("/mypage")
def mypage():
    """마이페이지 - 로그인 필수"""
    # 로그인 체크
    if 'user_idx' not in session:
        return redirect('/login')

    return render_template("mypage.html")


@app.route("/api/user/profile", methods=["GET"])
def get_user_profile():
    """사용자 프로필 정보 조회 API"""
    # 로그인 체크
    if 'user_idx' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."})

    user_idx = session.get('user_idx')

    if not dbm.DBOpen(host, id, pw, dbName):
        return jsonify({"success": False, "message": "DB 연결 실패"})

    try:
        sql = "SELECT u_name, u_email, u_dob FROM user WHERE u_idx = %s"
        if dbm.OpenSQL(sql, (user_idx,)):
            user_data = dbm.getData(0)

            if user_data:
                # 생년월일 포맷 변환
                birth_str = user_data['u_dob'].strftime("%Y-%m-%d") if user_data['u_dob'] else ""

                return jsonify({
                    "success": True,
                    "name": user_data['u_name'],
                    "email": user_data['u_email'],
                    "birth": birth_str
                })

        return jsonify({"success": False, "message": "사용자 정보를 찾을 수 없습니다."})

    except Exception as e:
        print(f"Profile Error: {e}")
        return jsonify({"success": False, "message": "서버 오류"})
    finally:
        dbm.DBClose()


@app.route("/api/user/change_password", methods=["POST"])
def change_password():
    """비밀번호 변경 API"""
    # 로그인 체크
    if 'user_idx' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."})

    user_idx = session.get('user_idx')
    data = request.get_json()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    # 비밀번호 유효성 검사
    if len(new_password) < 6:
        return jsonify({"success": False, "message": "비밀번호는 6자 이상이어야 합니다."})

    count = sum([
        bool(re.search(r'[A-Za-z]', new_password)),
        bool(re.search(r'[0-9]', new_password)),
        bool(re.search(r'[!~@#]', new_password))
    ])

    if count < 2 or re.search(r'[^A-Za-z0-9!~@#]', new_password):
        return jsonify({"success": False, "message": "비밀번호 조건을 만족하지 않습니다."})

    if not dbm.DBOpen(host, id, pw, dbName):
        return jsonify({"success": False, "message": "DB 연결 실패"})

    try:
        # 현재 비밀번호 확인
        sql = "SELECT u_pw FROM user WHERE u_idx = %s"
        if dbm.OpenSQL(sql, (user_idx,)):
            user_data = dbm.getData(0)

            if not user_data:
                return jsonify({"success": False, "message": "사용자를 찾을 수 없습니다."})

            # 현재 비밀번호 검증
            if not check_password_hash(user_data['u_pw'], current_password):
                return jsonify({"success": False, "message": "현재 비밀번호가 올바르지 않습니다."})

            # 새 비밀번호로 업데이트
            hashed_new_pw = generate_password_hash(new_password)
            update_sql = "UPDATE user SET u_pw = %s WHERE u_idx = %s"

            if dbm.RunSQL(update_sql, (hashed_new_pw, user_idx)):
                print(f"Success: 사용자 {user_idx} 비밀번호 변경 완료")
                return jsonify({"success": True, "message": "비밀번호가 변경되었습니다."})
            else:
                return jsonify({"success": False, "message": "비밀번호 변경에 실패했습니다."})

        return jsonify({"success": False, "message": "사용자 정보를 찾을 수 없습니다."})

    except Exception as e:
        print(f"Change Password Error: {e}")
        return jsonify({"success": False, "message": "서버 오류"})
    finally:
        dbm.DBClose()


@app.route("/favorites")
def favorites():
    """찜한 맛집 페이지"""
    # 로그인 체크
    if 'user_idx' not in session:
        return redirect('/login')

    # TODO: 찜한 맛집 데이터 조회 로직 추가
    return render_template("favorites.html")

@app.route("/check_userid", methods=["POST"])
def check_userid():
    userid = request.json.get("userid")

    if dbm.DBOpen(host, id, pw, dbName, port):
        # 테이블의 u_id 컬럼에서 중복 확인
        sql = "SELECT 1 FROM user WHERE u_id = %s"
        exists = dbm.CheckDuplicate(sql, (userid,))
        dbm.DBClose()
        return jsonify({"exists": exists})
    dbm.DBClose()

    print("Error: 아이디 중복 확인 중 DB 연결 실패")
    return jsonify({"exists": False, "error": "DB 연결 실패"})

# ================= 기능 2: 회원가입 처리 =================
@app.route("/signup_process", methods=["POST"])
def signup_process():
    # 폼 데이터 가져오기
    name = request.form.get("name", "").strip()
    userid = request.form.get("userid", "").strip()
    password = request.form.get("password", "")
    email = request.form.get("email", "").strip()
    birth = request.form.get("birth", "")

    # 유효성 검사 (Regex)
    if not re.fullmatch(r"[a-z0-9]+", userid):
        return jsonify(success=False, field="userid", msg="아이디 형식이 올바르지 않습니다.")

    # DB 연결 시도
    if not dbm.DBOpen(host, id, pw, dbName, port):
        print("Error: 회원가입 처리 중 DB 연결 실패")
        return jsonify(success=False, msg="서버 연결 실패")

    try:
        # 아이디 중복 최종 확인
        check_sql = "SELECT 1 FROM user WHERE u_id = %s"
        if dbm.CheckDuplicate(check_sql, (userid,)):
            return jsonify(success=False, field="userid", msg="이미 사용 중인 아이디입니다.")

        # 비밀번호 해싱 및 데이터 삽입
        hashed_pw = generate_password_hash(password)
        # u_idx는 auto_increment이므로 제외, is_active는 기본값 1
        insert_sql = """
            INSERT INTO user (u_name, u_id, u_pw, u_email, u_dob, is_active)
            VALUES (%s, %s, %s, %s, %s, 1)
        """
        success = dbm.RunSQL(insert_sql, (name, userid, hashed_pw, email, birth))

        if success:
            print(f"Success: 새 사용자 가입 완료 ({userid})")
            return jsonify(success=True)
        else:
            print("Error: 회원정보 저장 실패 (RunSQL 반환값 False)")
            return jsonify(success=False, msg="회원가입 처리 중 오류가 발생했습니다.")

    except Exception as e:
        print(f"Exception: 회원가입 중 예외 발생: {e}")
        return jsonify(success=False, msg="알 수 없는 오류가 발생했습니다.")
    finally:
        dbm.DBClose()

# ================= 기능 3: 로그인 처리 =================
@app.route("/login_process", methods=["POST"])
def login_process():
    userid = request.form.get("userid", "").strip()
    password = request.form.get("password", "")

    if not dbm.DBOpen(host, id, pw, dbName, port):
        return jsonify(success=False, msg="DB 연결 실패")

    try:
        # 1. SQL에 u_dob(생년월일) 추가
        sql = "SELECT u_idx, u_id, u_pw, u_name, u_dob FROM user WHERE u_id = %s"
        if dbm.OpenSQL(sql, (userid,)):
            user_data = dbm.getData(0)

            if not user_data:
                return jsonify(success=False, msg="아이디 또는 비밀번호가 일치하지 않습니다.")

            if check_password_hash(user_data['u_pw'], password):
                # 2. 세션에 필요한 모든 정보 저장
                session["user_idx"] = user_data['u_idx']
                session["u_idx"] = user_data['u_idx']
                session["userid"] = user_data['u_id']
                session["username"] = user_data['u_name']
                session["u_name"] = user_data['u_name']

                # 3. 생년월일을 "YYYYMMDD" 문자열 형식으로 세션에 저장
                if user_data['u_dob']:
                    session["u_dob"] = user_data['u_dob'].strftime("%Y%m%d")

                return jsonify(success=True)
            else:
                return jsonify(success=False, msg="아이디 또는 비밀번호가 일치하지 않습니다.")
    # (이하 동일)
    except Exception as e:
        print(f"Login Error: {e}") # 에러 내용 출력
        return jsonify(success=False, msg="서버 오류")
    finally:
        dbm.DBClose()

# ================= 기능 4: 로그아웃 =================
@app.route("/logout", methods=["POST", "GET"])
def logout():
    """로그아웃 - 세션 클리어 후 메인으로"""
    user_id = session.get("userid")
    session.clear()  # 세션 완전 삭제
    print(f"Logout: 사용자 로그아웃 ({user_id})")
    return redirect("/")  # 메인 페이지로 리다이렉트

if __name__ == '__main__':
    # app.run(host='0.0.0.0', debug=True)
    app.run(debug=True)