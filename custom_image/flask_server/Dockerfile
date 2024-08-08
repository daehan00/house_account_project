# Dockerfile
FROM python:3.8-slim

# 필수 패키지 설치 및 로케일 설정
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    locales \
    && apt-get clean

# 로케일 설정
RUN locale-gen=ko_KR.UTF-8
ENV LANG=ko_KR.UTF-8
ENV LANGUAGE=ko_KR:ko
ENV LC_ALL=ko_KR.UTF-8

# 작업 디렉터리 설정
WORKDIR /app

# 필요한 패키지 설치
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

EXPOSE 8088 5000
# 컨테이너 시작 시 실행될 명령
# CMD ["flask", "run", "--host=0.0.0.0", "--port=8088"]