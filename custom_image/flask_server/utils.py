import time
from flask import flash, redirect, request, session, url_for
import os
import requests
import json
import pandas as pd
import re
from datetime import datetime
import pytz
from dotenv import load_dotenv
load_dotenv()

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
        with open(os.getenv("JSON_PATH"), 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print("Error: The file was not found.")
        return None
    except json.JSONDecodeError:
        print("Error: The file is not in proper JSON format.")
        return None

def get_program_list(url, year_semester_house):
    headers = {
        "Accept": "application/json"
    }
    params = {
        "year_semester_house": year_semester_house
    }

    response = requests.get(url, headers=headers, params=params)
    program_list = []

    if response.status_code == 200:
        data = response.json()
        for program in data:
            options = {"program_id":program['program_id'],
                       "program_name":program['program_name']}
            program_list.append(options)
        return program_list  # 반환 값은 JSON 데이터
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return program_list

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

def get_category_expenses():
    data = load_dict_code()
    category = data['category_expenses']
    new_category = [
        {
            'program_id': value['kor_name'],
            'program_name': value['kor_name']
        }
        for value in category if 'kor_name' in value
    ]
    return new_category

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
    url = "http://172.28.0.12:5000/api/ra_list"

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
    url = "http://172.28.0.12:5000/api/program"

    # 기본 설정
    house_code = str(set_data['house'])
    year = set_data['year']
    semester = set_data['semester']

    # 이 로직은 개요표를 통째로 등록하는 방식. 기존의 연도-학기-하우스에 해당하는 프로그램 모두 삭제하는 버튼 제작필요.
    success_list = []
    failure_list = []
    fail_text_list = []

    file_list = os.listdir(data_dir)
    for file_name in file_list:
        file_path = os.path.join(data_dir, file_name)
        try:
            data = pd.read_excel(file_path, sheet_name='프로그램 개요표', header=1, dtype=object)
            data = data.dropna(subset=['분류'])
            selected_col = ['분류', '프로그램명', '담당RA']
            data = data[selected_col]
        except:
            continue

        data_dict = data.to_dict(orient='records')
        i = 1
        for program in data_dict:
            if program['분류'] == get_house_name(house_code):
                year_semester_house = str(year) + '-' + str(semester) + '-' + house_code
                program_id = year_semester_house + '-' + str(i).zfill(2)
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
                time.sleep(0.1)
            else:
                print(f"하우스 분류가 맞지 않습니다. 제출: {house_code}, 파일: {program['분류']}")
                continue
        os.remove(os.path.join(data_dir, file_name))
        print(f'삭제된 파일 : {file_name}')

    flash(f"작업 완료. 총 {len(success_list)}건 성공, {len(failure_list)}건 실패.")
    return redirect(redirect_url)

def form(input_type, name, name_id, attribute, content, options=None, required=True):
    """폼 필드 생성 함수에 required 파라미터 추가"""
    attributes = f'{attribute}="{content}"'
    if required:
        attributes += ' required'  # 필수 입력 필드로 설정
    if input_type == 'select':
        return {'입력창': input_type, '항목명': name, 'name': name_id, 'options': options, 'attributes': attributes}
    else:
        return {'입력창': input_type, '항목명': name, 'name': name_id, 'attributes': attributes}

def form_post_receipt(year_semester_house):
    today = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%dT%H:%M')
    user_list = [{'program_id':2019122044,'program_name':'김대한'},{'program_id':2022124085,'program_name':'박지영'}]
    category_expenses = get_category_expenses()
    url_program = os.getenv('URL_PROGRAM')
    try:
        program_list = get_program_list(url_program, year_semester_house)
    except Exception as e:
        flash(e)
        return redirect("/ra")

    form_list = [
        form('select', '사용자명', 'user_id', '', '', options=user_list),
        form('checkbox', '주말, 법정 공휴일 및 심야 사용 여부', 'holiday_check', '', '', required=False),
        form('select', '계정항목', 'category_id','placeholder', '', options=category_expenses),
        form('select', '프로그램명','program_id', 'placeholder', '', options=program_list),
        form('text', '구매 핵심 사유', 'purchase_reason', 'placeholder', '운영물품 구매'),
        form('text', '핵심 품목 및 수량', 'key_items_quantity', 'placeholder', '콜라 등 5종'),
        form('text', '구매 내역(종류와 단가)', 'purchase_details', 'placeholder', ''),
        form('number', '인원', 'head_count', 'min', '1'),
        form('datetime-local', '결제일시', 'datetime', 'value', today),
        form('number', '초', 'sec', 'max', '99'),
        form('number', '금액', 'expenditure', 'placeholder', '숫자만'),
        form('text', '가맹점명', 'store_name', 'placeholder', '영수증에 나온 그대로'),
        form('checkbox', '기념품지급대장 작성여부', 'souvenir_record', 'placeholder', '', required=False),
        form('checkbox', '분반 프로그램 여부', 'division_program', 'placeholder', '', required=False),
        form('number', '분반', 'division_num', 'max', '12', required=False),
        form('text', '업체 선정 사유', 'reason_store', 'placeholder', 'ex) 최저가 업체'),
        form('checkbox', 'isp 사용여부', 'isp_check', 'placeholder', '', required=False)
    ]
    contents = '''<main>영수증 입력 양식</main>
                            <form action="/ra/post_receipt" method="POST">
                                <table>
                                    <thead>
                                        <tr>
                                          <th scope="col">항목명</th>
                                          <th scope="col">입력</th>
                                        </tr>
                                      </thead>
                                      <tbody>'''
    for data in form_list:
        if data['입력창'] == 'select':
            option_html = ''.join(
                [f'<option value="{opt["program_id"]}">{opt["program_name"]}</option>' for opt in data['options']])
            contents += f'''<tr>
                                                <th scope="row">{data['항목명']}</th>
                                                <td><select name="{data['name']}">{option_html}</select></td>
                                            </tr>'''
        else:
            contents = contents + f'''<tr>
                                            <th scope="row">{data['항목명']}</th>
                                            <td><input type="{data['입력창']}" name="{data['name']}" {data['attributes']}></td>
                                        </tr>'''

    contents = contents + '''</tbody>
                                    <tfoot>
                                        <tr>
                                            <th scope="row" colspan="2"><input type="submit" value="제출"></th>
                                        </tr>
                                    </tfoot></table></form>'''
    return template('영수증 입력', contents)