# Dockerfile
FROM python:3.8-slim

# 필수 패키지 설치 및 로케일 설정
RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    libreoffice \
    libreoffice-writer \
    locales \
    fonts-noto-cjk \
    && echo "ko_KR.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen ko_KR.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 로케일 환경 변수 설정
ENV LANG=ko_KR.UTF-8
ENV LANGUAGE=ko_KR:ko
ENV LC_ALL=ko_KR.UTF-8

# 작업 디렉터리 설정
WORKDIR /app

# 필요한 패키지 설치
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

EXPOSE 8088 5000
CMD ["flask", "run", "--host=0.0.0.0", "--port=8088"]