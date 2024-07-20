from flask import flash, redirect, request, session, url_for
import os
import requests
import json
import pandas as pd
import re

def template(title, contents):
    return f'''<!doctype html>
            <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{title}</title>
                    <link rel="stylesheet" href=" { url_for('static', filename='css/table.css') }">
                </head>
                <body>
                    {contents}
                </body>
            </html>
            '''

# 허용되는 파일 확장자 목록
ALLOWED_EXTENSIONS = {'pdf', 'hwp', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file(upload_folder, redirect_url):
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if allowed_file(file.filename):
        filename = file.filename
        file.save(os.path.join(upload_folder, filename))
        flash('File successfully uploaded')
    else:
        flash('Invalid file type')

    return redirect(redirect_url)


def api_ra_list_post(data):
    # API 엔드포인트 URL
    url = "http://localhost:5000/api/ra_list"

    # 헤더 설정
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    # # 보낼 데이터
    # data = {
    #     "authority": None,
    #     "division_num": None,
    #     "email_address": "pzr2001@naver.com",
    #     "house_name": "AVISON",
    #     "semester": False,
    #     "user_id": 2022124082,
    #     "user_name": "박지영",
    #     "user_num": "010-4359-9993",
    #     "year": 2024
    # }

    json_data = json.dumps(data)
    response = requests.post(url, headers=headers, data=json_data)
    # 응답 출력
    return response.status_code, response.text

def register_ra_list(set_data, data_dir, redirect_url):
    # 입력값 없는 기본설정
    semester = set_data['semester']
    year = set_data['year']
    division_num = None
    authority = set_data['authority']
    success_list = []
    failure_list = []
    fail_text_list = []

    file_list = os.listdir(data_dir)
    for file_name in file_list:
        file_path = os.path.join(data_dir, file_name)
        data = pd.read_excel(file_path, header=1, dtype=object)

        col_list = ['번호', '면접결과', '하우스', '학번', '이름', '이메일', '연락처', '성별', '학년', '전공']
        if all(col in data.columns for col in col_list):
            print("All columns in col_list are present in DataFrame columns.")
        else:
            print("Some columns in col_list are missing from DataFrame columns.")
            continue

        data = data.drop([0, 1])
        data_dict = data.to_dict(orient='records')

        for data in data_dict:
            email_address = data['이메일']
            house_name = data['면접결과']
            user_id = int(data['학번'])
            user_name = re.sub(r"\(.*?\)", "", data['이름']).strip()
            user_num = data['연락처']
            ra_data = {
                "authority": authority,
                "division_num": division_num,
                "email_address": email_address,
                "house_name": house_name,
                "semester": semester,
                "user_id": user_id,
                "user_name": user_name,
                "user_num": user_num,
                "year": year
            }

            code, response_text = api_ra_list_post(ra_data)
            # 결과 처리

            if code == 201:
                print(f"{user_id}: {code}")
                success_list.append(user_id)
            else:
                print(f"failure: {user_id}, code: {code}")
                failure_list.append(f"{user_id}, {code}")
                fail_text_list.append(response_text)

        os.remove(os.path.join(data_dir, file_name))
        print(f'삭제된 파일 : {file_name}')

    flash(f"작업 완료. 총 {len(success_list)}건 성공, {len(failure_list)}건 실패. 실패 목록은 다음과 같습니다. {fail_text_list}")
    return redirect(redirect_url)
