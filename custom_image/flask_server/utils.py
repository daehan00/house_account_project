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

def load_dict_code():
    try:
        with open('/app/static/data/dict_code.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print("Error: The file was not found.")
        return None
    except json.JSONDecodeError:
        print("Error: The file is not in proper JSON format.")
        return None

def get_house_code(house_name):
    # Open the JSON file and load data
    data = load_dict_code()

    # Loop through the list of house names to find a match
    for house in data['house_names']:
        if house['kor_name'] == house_name:
            return house['en_name']

    # Handle the case where the house name is not found
    print(f"Error: '{house_name}' not found in the list.")
    return None

def get_house_name(house_code):
    # Open the JSON file and load data
    data = load_dict_code()

    # Loop through the list of house names to find a match
    for house in data['house_names']:
        if house['en_name'] == house_code:
            return house['kor_name']

    # Handle the case where the house name is not found
    print(f"Error: '{house_code}' not found in the list.")
    return None

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


def api_post_data(url, data):
    # 헤더 설정
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    json_data = json.dumps(data)
    response = requests.post(url, headers=headers, data=json_data)
    # 응답 출력
    return response.status_code, response.text

def register_ra_list(set_data, data_dir, redirect_url):
    # API 엔드포인트 주소
    url = "http://localhost:5000/api/ra_list"

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
            house_name = get_house_code(data['면접결과'])
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

            code, response_text = api_post_data(url, ra_data)
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


def register_program_list(set_data, data_dir, redirect_url):
    # API 엔드포인트 주소
    url = "http://localhost:5000/api/program"

    # 기본 설정
    house_code = set_data['house_code']
    year = set_data['year']
    semester = set_data['semester']

    # 이 로직은 개요표를 통째로 등록하는 방식. 기존의 연도-학기-하우스에 해당하는 프로그램 모두 삭제하는 버튼 제작필요.
    success_list = []
    failure_list = []
    fail_text_list = []

    file_list = os.listdir(data_dir)
    for file_name in file_list:
        file_path = os.path.join(data_dir, file_name)
        data = pd.read_excel(file_path, sheet_name='프로그램 개요표', header=1, dtype=object)

        # col_list = ['분류','카테고리','프로그램명','RC인정시간','인원(명)','담당RM','담당RA','예산(안)','기획','실행','환류','학습목표','6대 핵심역량','LLC 유무','사전 조사	방식']
        # if all(col in data.columns for col in col_list):
        #     print("All columns in col_list are present in DataFrame columns.")
        # else:
        #     print("Some columns in col_list are missing from DataFrame columns.")
        #     continue

        data = data.dropna(subset=['분류'])
        selected_col = ['분류', '프로그램명', '담당RA']
        data = data[selected_col]

        data_dict = data.to_dict(orient='records')
        i =1
        for program in data_dict:
            if program['분류'] == get_house_name(house_code):
                year_semester_house = str(year)+'-'+str(semester)+'-'+house_code
                program_id = year_semester_house+'-'+str(i).zfill(2)
                program_name = re.sub(r'\s+', ' ', program['프로그램명']).strip()

                program_data = {
                  "house_name": house_code,
                  "program_id": program_id,
                  "program_name": program_name,
                  "register_check": True,
                  "semester": semester,
                  "year": year,
                  "year_semester_house": year_semester_house
                }

                code, response_text = api_post_data(url, program_data)

                # 결과 처리
                if code == 201:
                    print(f"{program_id}: {code}")
                    success_list.append(program_id)
                else:
                    print(f"failure: {program_id}, code: {code}")
                    failure_list.append(f"{program_id}, {code}")
                    fail_text_list.append(response_text)
                i += 1

        # os.remove(os.path.join(data_dir, file_name))
        # print(f'삭제된 파일 : {file_name}')

    flash(f"작업 완료. 총 {len(success_list)}건 성공, {len(failure_list)}건 실패.")
    return redirect(redirect_url)