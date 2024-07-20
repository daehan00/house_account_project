FROM apache/airflow:2.9.2
ENV TZ Asia/Seoul
COPY requirements.txt /
RUN pip install --upgrade pip
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt