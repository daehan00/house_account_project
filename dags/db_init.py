import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import psycopg2


def init(postgres_conn_id, **kwargs):
    # PostgreSQL에 연결
    try:
        postgres_hook = PostgresHook(postgres_conn_id)
        conn = postgres_hook.get_conn()
        print("PostgreSQL에 연결되었습니다.")
    except psycopg2.Error as e:
        print("PostgreSQL 연결 오류:", e)
        exit()

    # 커서 생성
    cur = conn.cursor()

    # 테이블 생성 쿼리
    # program_id : ex) 2024-1-AV-01 (년도-학기-하우스코드-일련번호)
    create_program_list_table = """
        CREATE TABLE IF NOT EXISTS program_list_table (
            program_id TEXT PRIMARY KEY,
            program_name TEXT NOT NULL,
            house_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            semester integer NOT NULL,
            register_check BOOLEAN,
            year_semester_house TEXT NOT NULL
        );"""

    create_ra_list_table = """
            CREATE TABLE IF NOT EXISTS ra_list_table (
                user_id BIGINT PRIMARY KEY,
                user_name TEXT NOT NULL,
                user_num TEXT NOT NULL,
                division_num INTEGER,
                email_address TEXT NOT NULL,
                year INTEGER NOT NULL,
                semester BOOLEAN NOT NULL,
                house_name TEXT NOT NULL,
                authority BOOLEAN DEFAULT false
            );"""

    create_category_list_table = """
                CREATE TABLE IF NOT EXISTS category_list_table (
                    category_id TEXT PRIMARY KEY,
                    category_name TEXT NOT NULL,
                    description TEXT
                );"""

    # trigger 생성
    create_trigger_function = """
            CREATE OR REPLACE FUNCTION update_modified_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();  -- 현재 시간을 updated_at 필드에 설정
                RETURN NEW;              -- 수정된 레코드 반환
            END;
            $$ LANGUAGE plpgsql;
            """
    # create_trigger = """
    #         CREATE TRIGGER update_updated_at_before_update
    #         BEFORE UPDATE ON order_test_table
    #         FOR EACH ROW
    #         EXECUTE FUNCTION update_modified_column();
    #         """

    # 데이터 삽입
    try:
        cur.execute(create_program_list_table)
        # cur.execute(create_ra_list_table)
        # cur.execute(create_category_list_table)


        # cur.execute(create_trigger_function)
        conn.commit()
        # SQL 쿼리 작성
        # query = "SELECT * FROM order_test_table WHERE channel = 'Naver';"

        # 쿼리 실행
        # cur.execute(query)

        # 결과 패치
        # results = cur.fetchall()

        # # 결과 출력
        # for row in results:
        #     print(row)
        # print("모든 실행 코드가 막혀 있습니다. ")
        print("데이터가 성공적으로 추가되었습니다. ")
    except psycopg2.Error as e:
        conn.rollback()
        print("데이터 추가 오류:", e)

    # 연결 종료
    conn.close()


with DAG(
        dag_id="dags_init",
        tags=['99_환경설정'],
        schedule=None,
        start_date=pendulum.datetime(2024, 7, 1, tz="Asia/Seoul"),
        catchup=False
) as dag:
    set_startDate_task = PythonOperator(
        task_id='init_db',
        python_callable=init,
        op_kwargs={'postgres_conn_id': 'conn-db-postgre-accountingdb'}
    )