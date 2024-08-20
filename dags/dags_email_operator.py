from airflow import DAG
import pendulum
from airflow.operators.email import EmailOperator
from airflow.operators.python import PythonOperator
from common.common_functions import common_func, excel_files
from airflow.utils.email import send_email_smtp
from airflow.models import Variable

def custom_send_email(**kwargs):
    ti = kwargs['ti']
    logis_id = "unointer"
    file_paths = ti.xcom_pull(task_ids='create_order_unointer', key='file_list')
    send_email_smtp(to=ti.xcom_pull(task_ids='create_order_unointer', key='to_email'), cc=Variable.get('cc_email'), subject=f"{logis_id} 파일 전송 테스트",
                    html_content="파일 여러개 전송 성공", files=file_paths)



with DAG(
    dag_id = 'dags_email_operator',
    schedule = None,
    start_date = pendulum.datetime(2024, 4, 12, tz = 'Asia/Seoul'),
    catchup = False
) as dag :
    create_order_unointer = PythonOperator(
        task_id = 'create_order_unointer',
        python_callable = excel_files,
        provide_context = True
    )
    send_email_task = PythonOperator(
        task_id='send_email',
        python_callable=custom_send_email,
        provide_context=True,
    )

create_order_unointer >> send_email_task