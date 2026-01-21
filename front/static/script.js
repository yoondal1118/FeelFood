/* ==========================================
   JavaScript 파일
   ========================================== */

/* 
 * 이 파일은 최소한의 JavaScript만 사용합니다.
 * 대부분의 기능은 HTML의 onclick으로 처리됩니다.
 */


/* ==========================================
   함수: toggleEmotions()
   역할: "더 느끼기" 버튼을 누르면 나머지 감성지수를 보여주거나 숨깁니다
   사용 위치: detail.html의 "더 느끼기" 버튼
   ========================================== */

function toggleEmotions() {
    // id가 "other-emotions"인 요소를 찾아서 변수에 저장
    // document.getElementById()는 HTML에서 특정 id를 가진 요소를 찾는 함수
    var emotionDiv = document.getElementById('other-emotions');
    
    // 만약 요소를 찾지 못했다면 (null이면) 함수 종료
    if (!emotionDiv) {
        console.log('감성지수 영역을 찾을 수 없습니다.');
        return;  // 함수를 여기서 끝냄
    }
    
    // 현재 display 스타일 값을 가져옴
    // getComputedStyle()은 실제로 적용된 스타일을 가져오는 함수
    var currentDisplay = window.getComputedStyle(emotionDiv).display;
    
    // 현재 숨겨져 있으면 (display가 'none'이면)
    if (currentDisplay === 'none') {
        // 보이게 만들기
        emotionDiv.style.display = 'block';  // block으로 변경하면 표시됨
        console.log('나머지 감성지수를 표시합니다.');
    } else {
        // 보이고 있으면 숨기기
        emotionDiv.style.display = 'none';   // none으로 변경하면 숨겨짐
        console.log('나머지 감성지수를 숨깁니다.');
    }
}


/* ==========================================
   페이지 로드 완료 후 실행되는 코드
   ========================================== */

/* 
 * DOMContentLoaded 이벤트: HTML 문서가 완전히 로드된 후 실행
 * 이 부분은 페이지가 로드될 때 자동으로 실행됩니다
 */
document.addEventListener('DOMContentLoaded', function() {
    // 페이지가 로드되었다는 메시지를 콘솔에 출력
    // (개발자 도구의 Console 탭에서 확인 가능)
    console.log('페이지가 로드되었습니다.');
    
    // main_list 페이지용 대학교 드롭다운 초기화
    initUniversityDropdown();
});


/* ==========================================
   나중에 추가할 수 있는 함수들 (예시)
   ========================================== */

/* 
 * 아래는 나중에 기능을 확장할 때 사용할 수 있는 함수 예시입니다.
 * 현재는 사용하지 않으므로 주석 처리되어 있습니다.
 */

/*
// 예시 1: 검색 기능
function searchRestaurant(keyword) {
    console.log('검색어:', keyword);
    // 검색 로직 추가
}

// 예시 2: 즐겨찾기 추가
function addToFavorites(restaurantName) {
    console.log('즐겨찾기 추가:', restaurantName);
    // 즐겨찾기 로직 추가
}

// 예시 3: 리뷰 작성
function writeReview(restaurantName, rating, comment) {
    console.log('리뷰 작성:', restaurantName, rating, comment);
    // 리뷰 저장 로직 추가
}
*/


/* ==========================================
   디버깅용 함수
   ========================================== */

/*
 * 개발 중에 문제가 생기면 아래 함수를 사용하여 디버깅할 수 있습니다.
 */

// 모든 버튼 요소를 찾아서 콘솔에 출력하는 함수
function debugButtons() {
    var buttons = document.querySelectorAll('button');
    console.log('페이지의 모든 버튼:', buttons);
    console.log('버튼 개수:', buttons.length);
}

// 특정 요소의 스타일을 확인하는 함수
function checkElementStyle(elementId) {
    var element = document.getElementById(elementId);
    if (element) {
        console.log('요소 ID:', elementId);
        console.log('현재 스타일:', window.getComputedStyle(element));
    } else {
        console.log('요소를 찾을 수 없습니다:', elementId);
    }
}


/* ==========================================
   주석 설명
   ========================================== */

/*
 * JavaScript 기본 개념 정리:
 * 
 * 1. 변수 선언:
 *    - var: 함수 스코프 변수 (오래된 방식)
 *    - let: 블록 스코프 변수 (현대적 방식)
 *    - const: 상수 (변경 불가능)
 * 
 * 2. 함수 선언:
 *    function 함수명(매개변수) {
 *        // 실행할 코드
 *    }
 * 
 * 3. DOM 조작:
 *    - document.getElementById(): ID로 요소 찾기
 *    - document.querySelector(): CSS 선택자로 요소 찾기
 *    - element.style.display: 요소의 표시/숨김 제어
 * 
 * 4. 이벤트 리스너:
 *    - addEventListener(): 이벤트 발생 시 함수 실행
 *    - 'DOMContentLoaded': 페이지 로드 완료
 *    - 'click': 클릭 이벤트
 * 
 * 5. 조건문:
 *    if (조건) {
 *        // 참일 때 실행
 *    } else {
 *        // 거짓일 때 실행
 *    }
 */

/* ==========================================
   index.html - 대학교 선택 관련 함수들
   ========================================== */

/**
 * 함수: checkUniversity()
 * 역할: 대학교가 선택되었는지 확인
 * 반환: 선택된 대학교 이름 또는 false
 */
function checkUniversity() {
    // 드롭다운에서 선택된 값 가져오기
    var university = document.getElementById('universitySelect').value;
    
    // 선택되지 않았으면
    if (!university) {
        showUniversityAlert();  // 경고 메시지 표시
        return false;
    }
    
    // 선택되었으면 대학교 이름 반환
    return university;
}

/**
 * 함수: showUniversityAlert()
 * 역할: "대학교를 먼저 선택해주세요" 경고 메시지 표시
 */
function showUniversityAlert() {
    var alertDiv = document.getElementById('universityAlert');
    
    // 경고 메시지 보이기
    alertDiv.style.display = 'block';
    
    // 3초 후 자동으로 숨기기
    setTimeout(function() {
        alertDiv.style.display = 'none';
    }, 3000);
    
    // 드롭다운으로 스크롤 이동
    document.getElementById('universitySelect').scrollIntoView({ 
        behavior: 'smooth',  // 부드럽게 이동
        block: 'center'      // 화면 중앙에 배치
    });
}

/**
 * 함수: selectEmotion(emotion)
 * 역할: 감정 버튼 클릭 시 대학교 확인 후 페이지 이동
 * 매개변수: emotion - 선택한 감정 (희, 노, 애(슬픔), 애(사랑), 락)
 */
function selectEmotion(emotion) {
    // 1. 대학교 선택 확인
    var university = checkUniversity();
    if (!university) {
        return;  // 선택 안 됐으면 여기서 종료
    }
    
    // 2. 대학교 선택됐으면 main_list로 이동
    // encodeURIComponent: URL에 안전하게 전달하기 위한 인코딩
    window.location.href = '/main_list?emotion=' + emotion + 
                          '&location=' + encodeURIComponent(university);
}

/**
 * 함수: selectWeather()
 * 역할: 날씨 버튼 클릭 시 바로 weather_select로 이동
 * 참고: weather_select 페이지에서 직접 대학교를 선택할 수 있음
 */
function selectWeather() {
    // 대학교 선택 확인 없이 바로 이동
    window.location.href = '/weather_select';
}


/* ==========================================
   main_list.html - 대학교 변경 관련 함수들 (🔥 새로 추가)
   ========================================== */

/**
 * 함수: changeUniversity()
 * 역할: main_list 페이지에서 대학교를 변경하면 
 *       현재 URL의 파라미터를 유지한 채로 location만 변경
 * 사용 위치: main_list.html의 대학교 드롭다운
 */
function changeUniversity() {
    // 선택된 대학교 값 가져오기
    var newUniversity = document.getElementById('universityChangeSelect').value;
    
    console.log('선택된 대학교:', newUniversity);  // 디버깅용
    
    // 대학교를 선택하지 않았으면 아무것도 안 함
    if (!newUniversity) {
        return;
    }
    
    // 현재 URL의 파라미터들을 가져오기
    // 예: ?emotion=희&location=전북대 → URLSearchParams로 파싱
    var urlParams = new URLSearchParams(window.location.search);
    
    console.log('변경 전 파라미터:', urlParams.toString());  // 디버깅용
    
    // location 파라미터만 새로운 대학교로 변경
    // emotion이나 categories 같은 다른 파라미터는 그대로 유지됨!
    urlParams.set('location', newUniversity);
    
    console.log('변경 후 파라미터:', urlParams.toString());  // 디버깅용
    
    // 변경된 파라미터로 페이지 새로고침
    window.location.href = '/main_list?' + urlParams.toString();
}

/**
 * 함수: initUniversityDropdown()
 * 역할: 페이지 로드 시 현재 선택된 대학교를 드롭다운에 표시
 * 사용 위치: main_list.html 로드 시 자동 실행
 */
function initUniversityDropdown() {
    // universityChangeSelect 요소가 있는지 확인 (main_list.html에만 있음)
    var dropdown = document.getElementById('universityChangeSelect');
    
    // 드롭다운이 없으면 (다른 페이지면) 함수 종료
    if (!dropdown) {
        return;
    }
    
    // URL에서 현재 location 파라미터 가져오기
    var urlParams = new URLSearchParams(window.location.search);
    var currentLocation = urlParams.get('location');
    
    console.log('URL에서 가져온 location:', currentLocation);  // 디버깅용
    
    // 드롭다운에 현재 대학교 선택 상태로 표시
    if (currentLocation) {
        dropdown.value = currentLocation;
        console.log('드롭다운에 설정된 대학교:', currentLocation);
    }
}

/**
 * 함수: selectFortune()
 * 역할: 운세 버튼 클릭 시 대학교 확인 후 운세 페이지로 이동
 */
function selectFortune() {
    var location = checkUniversity();
    if (!location) {
        return;
    }

    // 🔥 fortune_result / fortune_login 구분하지 말고
    // fortune 하나로만 보냄
    window.location.href = '/fortune?location=' + encodeURIComponent(location);
}

/* ==========================================
   지도 팝업 관련 함수들
   ========================================== */

// 전역 변수로 지도 객체 저장
var kakaoMapInstance = null;

/**
 * 함수: openMapPopup(address)
 * 역할: 지도 팝업을 열고 카카오맵 표시
 * 매개변수: address - 표시할 주소
 */
function openMapPopup(address, name) {
    var popup = document.getElementById('mapPopup');
    if (!popup) {
        console.error('팝업 요소를 찾을 수 없습니다.');
        return;
    }
    
    // 팝업 열기
    popup.classList.add('active');
    
    // 주소 표시
    document.getElementById('popupAddress').textContent = address || '주소 정보 없음';
    
    // 카카오맵 로드
    loadKakaoMap(address, name);
    
    console.log('지도 팝업을 열었습니다. 주소:', address);
}

/**
 * 함수: closeMapPopup()
 * 역할: 지도 팝업을 닫기
 */
function closeMapPopup() {
    var popup = document.getElementById('mapPopup');
    if (popup) {
        popup.classList.remove('active');
        console.log('지도 팝업을 닫았습니다.');
    }
}

/* 메뉴 팝업 열기 */
function openMenuPopup() {
    var popup = document.getElementById('menuPopup');
    if (!popup) {
        console.error('팝업 요소를 찾을 수 없습니다.');
        return;
    }
    
    // 팝업 열기
    popup.classList.add('active');
    
}

/**
 * 함수: closeMapPopup()
 * 역할: 지도 팝업을 닫기
 */
function closeMenuPopup() {
    var popup = document.getElementById('menuPopup');
    if (popup) {
        popup.classList.remove('active');
        console.log('메뉴 팝업을 닫았습니다.');
    }
}

/**
 * 함수: loadKakaoMap(address)
 * 역할: 카카오맵 API를 사용하여 지도 표시
 * 매개변수: address - 검색할 주소
 */
function loadKakaoMap(address, name) {
    // 카카오맵 API가 로드되지 않았으면 에러
    if (typeof kakao === 'undefined') {
        console.error('카카오맵 API가 로드되지 않았습니다.');
        alert('지도를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.');
        return;
    }
    
    var mapContainer = document.getElementById('kakaoMap');
    
    // 주소로 좌표 검색
    var geocoder = new kakao.maps.services.Geocoder();
    
    geocoder.addressSearch(address, function(result, status) {
        // 정상적으로 검색이 완료됐으면
        if (status === kakao.maps.services.Status.OK) {
            var coords = new kakao.maps.LatLng(result[0].y, result[0].x);
            
            // 지도 옵션
            var mapOption = {
                center: coords, // 지도의 중심좌표
                level: 2 // 지도의 확대 레벨 (1~14, 숫자가 작을수록 확대)
            };
            
            // 지도 생성
            kakaoMapInstance = new kakao.maps.Map(mapContainer, mapOption);
            
            // 마커 생성
            var marker = new kakao.maps.Marker({
                map: kakaoMapInstance,
                position: coords
            });
            
            // 중앙 정렬 + 자동 크기 조정
            var customOverlay = new kakao.maps.CustomOverlay({
                position: coords,
                content: '<div style="' +
                    'padding: 10px 16px;' +
                    'font-size: 14px;' +
                    'font-weight: bold;' +
                    'text-align: center;' +
                    'color: #333;' +
                    'background: white;' +
                    'border-radius: 8px;' +
                    'box-shadow: 0 2px 8px rgba(0,0,0,0.15);' +
                    'white-space: nowrap;' +
                    'transform: translate(-50%, -100%);' +
                    'margin-top: -15px;' +
                '">' + name + '</div>',
                xAnchor: 0.5,
                yAnchor: 1
            });
            customOverlay.setMap(kakaoMapInstance);
            
            console.log('지도를 성공적으로 로드했습니다.');

        } else {
            console.error('주소 검색에 실패했습니다:', status);
            alert('주소를 찾을 수 없습니다: ' + address);
        }
    });
}

function addUniversityData(form) {
    const universitySelect = document.getElementById('universitySelect');
    const universityValue = universitySelect.value;
    
    // 대학교 선택 안 했을 때 경고
    if (!universityValue) {
        document.getElementById('universityAlert').style.display = 'block';
        setTimeout(() => {
            document.getElementById('universityAlert').style.display = 'none';
        }, 3000);
        return false; // 폼 제출 중단
    }
    
    // hidden input에 값 설정
    document.getElementById('universityHidden').value = universityValue;
    return true; // 폼 제출 진행
}