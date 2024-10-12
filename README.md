# House Accounting Project

## 프로젝트 설명
이 프로젝트는 하우스 내 회계처리를 간편하게 모두 처리할 수 있는 시스템입니다.
회계처리의 어려움은 복잡한 처리 구조와 단순 반복 작업에서의 실수에 있습니다. 따라서 사용자의 작업을 최소화/단순화 하는 것이 목표입니다.

## 주요 기능
1. 일반 RA
  - 카드사용 예약(달력)
  - 카드사용내역 제출
  - 양식파일 다운로드 및 제출
2. 회계담당 RA
  - RA 및 프로그램 등록
  - 월별 정산자료 제작
  - 학기말 정산자료 제작
3. 공통
  - 정례회의록 수합

## 링크
- 웹페이지 : https://houseaccounting.rlaeogks4682.com
- pgAdmin : http://3.24.242.85:5050/

## 기술
 - 언어: python
 - 서버: aws ec2(1년 무료)
 - 호스팅: aws route 53(도메인 14달러ㅠ)
 - 가상환경: docker
 - 웹 & API: flask
 - DB: postgreSQL
 - DB 웹: pgAdmin
 - API문서화: swagger