import os
def common_func():
    print('This is common function')

def excel_files(**kwargs):
    data_dir = "/opt/airflow/storage/RA/AVISON/receipts"
    print(data_dir)
    file_list = os.listdir(data_dir)
    print(file_list)

    file_list = [os.path.join(data_dir, file_name) for file_name in file_list]
    print(file_list)
    ti = kwargs['ti']
    ti.xcom_push(key='file_list', value=file_list)
    ti.xcom_push(key='to_email', value="2000daehan@naver.com")
    ti.xcom_push(key='cc_email', value="2000daehan@yonsei.ac.kr")