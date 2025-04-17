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

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

COPY . .

EXPOSE 8088 5000

# gunicorn은 app.py 파일의 app 객체를 실행
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8088", "app:app"]