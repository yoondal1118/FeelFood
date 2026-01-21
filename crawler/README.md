# crawler
크롤링 관련 파일

+ naver_review.py 파일과 store_list.py 파일을 새로운 폴더(예: 크롤링 작업장)를 생성하여 그 안에 함께 놓는다 (매우 중요)
  + C:\Users\MYCOM\Desktop\크롤링 작업장 (이런식으로, 두개의 .py 파일를 새로운 폴더에 넣어야함)
+ store_list.py 파일을 열어 206번 라인 lc 변수 수정 lc = "한양대" (이런식으로 가게 리스트 수집 할 상권 하나만)
+ store_list.py 파일이 실행되면, 자동으로 DBMS에 연결되어 데이터를 저장함
+ 가게 수집 완료 후, naver_review.py 파일을 열어 바로 실행하면, 자동으로 store 테이블에서 필요한 데이터 가져다 저장하거나
+ 필요시, 548번째 라인에서 uni_list = ['한양대', '고려대'] 와 같이, 원하는 상권의 리뷰만 수집하게 설정 가능
+ 실행하게 되면, store의 s_img, s_location을 저장한 후, 중복체크를 하면서 menu, review 테이블을 저장하기 시작함
+ review는 최신순으로 수집하고, 최신 데이터를 수집했을 때, review 테이블의 값과 비교해서, 같은값이면 다음 가게로 넘어간다

+ VS CODE 에디터로 저 두 파일 있는 **폴더** 열어야 정상적으로 작동됩니다
+ 필요한 라이브러리
  + pip install selenium
  + pip install pandas
  + pip install pymysql
  + pip install python-dotenv
  + pip install mysql-connector-python
  + pip install cryptography (필요시 설치)
 
+ 크롤링으로 수집 완료된 대학교 상권이 있다면, 팀장에게 전달해주세요. 따로 체크하고 있습니다

+ DB에서 데이터를 삭제할 일이 잇다면, 리뷰, 메뉴, 스토어 순으로 삭제 해야합니다
```bash
DELETE FROM review WHERE s_idx = 43;
DELETE FROM menu   WHERE s_idx = 43;
DELETE FROM store  WHERE s_idx = 43;
```

+ DB 백업 명령어
  + mysqldump -u root -p bigdata > DB_backup_2025_12_19.sql
+ DB 백업파일 로드 명령어
  + CREATE DATABASE bigdata (필요시)
  + mysql -u root -p bigdata < DB_backup_2025_12_19.sql