import time
from flask import flash, redirect, request, url_for
import os
import openpyxl
import subprocess
from PyPDF2 import PdfMerger
import requests
import json
import pandas as pd
import re
from datetime import datetime
import pytz
from dotenv import load_dotenv
import tempfile
import unicodedata
load_dotenv()

def template(title, contents):
    return f'''<!doctype html>
            <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{title}</title>
                    <link rel="stylesheet" href=" { url_for('static', filename='css/table.css') }">
                    <script>
                        window.onload = function() '''+'''{
                            {% with messages = get_flashed_messages() %}
                            {% if messages %}
                                {% for message in messages %}
                                alert("{{ message }}");
                                {% endfor %}
                            {% endif %}
                            {% endwith %}
                        }
                    </script>
                </head>
                <body>'''+f'''
                    {contents}
                </body>
            </html>
            '''

def load_dict_code():
    try:
        with open(os.getenv("DATA_PATH")+'dict_code.json', 'r', encoding='utf-8') as file:
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

def get_ra_list(url):
    headers = {
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)
    ra_list = []

    if response.status_code == 200:
        data = response.json()
        for ra in data:
            options = {"program_id": ra['user_id'],
                       "program_name": ra['user_name']}
            ra_list.append(options)
        return ra_list  # 반환 값은 JSON 데이터
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return ra_list

def get_ra_list_sorted():
    headers = {"Accept": "application/json"}

    response = requests.get(os.getenv("URL_API")+'ra_list', headers=headers)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)

        df_sorted = df.sort_values(by='user_name')

        auth_true = df_sorted[df_sorted['authority']]
        auth_false = df_sorted[~df_sorted['authority']]

        return auth_true.to_dict(orient='records'), auth_false.to_dict(orient='records')
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None, None

def update_ra_authority(user_id, authority):
    url = os.getenv("URL_API") + 'ra_list/update/' + str(user_id)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    data = {
        "authority": authority
    }

    response = requests.put(url, headers=headers, data=data)

    if response.status_code == 200:
        if authority:
            return 'success', f'{user_id} 권한 부여되었습니다.'
        else:
            return 'success', f'{user_id} 권한 삭제되었습니다.'
    else:
        return 'error', response.text

def ra_login(url, user_id):
    headers = {
        "Accept": "application/json"
    }
    response = requests.get(url+str(user_id), headers=headers)

    data = response.json()
    if response.status_code == 200:
        if data['authority']:
            return 'manager', data
        else :
            return 'ra', data
    elif response.status_code == 404:
        return 'wrongid', data
    else:
        return 'error', data

def get_receipt_list(url, search_id):
    headers = {
        "Accept": "application/json"
    }

    response = requests.get(f"{url}/{search_id}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        sorted_data = sorted(data, key=lambda x: datetime.fromisoformat(x['date']))
        return sorted_data  # 반환 값은 JSON 데이터
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def delete_receipt_data(url, id):
    headers = {
        "Accept": "application/json"
    }
    response = requests.delete(f"{url}/{id}", headers=headers)
    if response.status_code == 204:
        return True
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return False

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

def allowed_file(upload_folder, filename, div):
    file_extensions = ['.pdf', '.hwp', '.xlsx', '.xls']  # 확장자 앞에 점 추가
    filename_lower = filename.lower()  # 파일 이름을 소문자로 변환

    if any(filename_lower.endswith(ext) for ext in file_extensions):
        if div == "manager":
            if not filename_lower.endswith('.xlsx'):
                return None, None, 'error'
            return upload_folder, filename, 'success'
        if div == "ra":
            try:
                date_str = filename[:6]
                date = datetime.strptime(date_str, '%y%m%d')
                if filename_lower.endswith('.xlsx'):
                    return upload_folder+'/receipts', filename, 'success'
                if filename_lower.endswith('.pdf'):
                    file_list = [unicodedata.normalize('NFC', f.split('.')[0]) for f in os.listdir(upload_folder+'/minutes') if f.endswith('.hwp')]
                    file_name = unicodedata.normalize('NFC', filename.split('.')[0])
                    if not file_name in file_list:
                        return upload_folder, filename, 'pdf_error'

            except ValueError:
                return upload_folder, filename, 'name_error'
            return upload_folder+'/minutes', filename, 'success'
    else:
        return None, None, 'error'

def upload_file(upload_folder, redirect_url, div):
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)

    upload_folder_, filename, error_type = allowed_file(upload_folder, file.filename, div)
    if error_type == 'success':
        try:
            file.save(os.path.join(upload_folder_, filename))
            flash('File successfully uploaded', 'success')
        except IOError as e:
            flash('File save error: ' + str(e), 'error')
            return redirect(request.url)
    elif error_type == 'name_error':
        flash('파일명 설정이 잘못되었습니다. 파일명을 확인해주세요.', 'error')
    elif error_type == 'pdf_error':
        flash('한글 파일이 없습니다. 영수증 한글 파일을 먼저 업로드해주세요.', 'error')
    else:
        flash('Invalid file type', 'error')

    return redirect(redirect_url)

def get_files_from_directory(directory_path):
    try:
        files = os.listdir(directory_path)
        return sorted(files)
    except FileNotFoundError:
        return []

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
    url = os.getenv('URL_API')+'ra_list'

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

    flash(f"작업 완료. 총 {len(success_list)}건 성공, {len(failure_list)}건 실패. 실패 목록은 다음과 같습니다. {fail_text_list}", 'info')
    return redirect(redirect_url)

def register_program_list(set_data, data_dir, redirect_url):
    # API 엔드포인트 주소
    url = os.getenv("URL_API")+"program"

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

    flash(f"작업 완료. 총 {len(success_list)}건 성공, {len(failure_list)}건 실패.", 'info')
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

def form_post_receipt(year_semester_house, user_id):
    today = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%dT%H:%M')
    user_list = get_ra_list(os.getenv('URL_API')+'ra_list/get')
    category_expenses = get_category_expenses()
    url_program = os.getenv('URL_API')+'program'
    try:
        program_list = get_program_list(url_program, year_semester_house)
    except Exception:
        return redirect("/ra")

    form_list = [
        form('select', '사용자명', 'user_id', '', '', options=user_list),
        form('checkbox', '주말, 법정 공휴일 및 심야 사용 여부', 'holiday_check', '', '', required=False),
        form('select', '계정항목', 'category_id','placeholder', '', options=category_expenses),
        form('select', '프로그램명','program_id', '', '', options=program_list),
        form('text', '구매 핵심 사유', 'purchase_reason', 'placeholder', '운영물품 구매'),
        form('text', '핵심 품목 및 수량', 'key_items_quantity', 'placeholder', '콜라 등 5종'),
        form('text', '구매 내역(종류와 단가)', 'purchase_details', 'placeholder', ''),
        form('number', '인원', 'head_count', 'min', '1'),
        form('datetime-local', '결제일시', 'datetime', 'value', today),
        form('number', '초', 'sec', 'max', '60'),
        form('number', '금액', 'expenditure', 'placeholder', '숫자만'),
        form('text', '가맹점명', 'store_name', 'placeholder', '영수증에 나온 그대로'),
        form('checkbox', '기념품지급대장 작성여부', 'souvenir_record', 'placeholder', '', required=False),
        form('checkbox', '분반 프로그램 여부', 'division_program', 'placeholder', '', required=False),
        form('number', '분반', 'division_num', 'max', '12', required=False),
        form('text', '업체 선정 사유', 'reason_store', 'placeholder', 'ex) 최저가 업체'),
        form('checkbox', 'isp 사용여부', 'isp_check', 'placeholder', '', required=False)
    ]
    contents = '''<main>영수증 입력 양식</main>
                            <form action="/ra/post_receipt_data" method="POST">
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
                [f'<option value="{opt["program_id"]}" {"selected" if str(opt["program_id"]) == str(user_id) else ""}>{opt["program_name"]}</option>' for opt in data['options']])
            contents += f'''<tr>
                                                <th scope="row">{data['항목명']}</th>
                                                <td><select name="{data['name']}" {data['attributes']}>{option_html}</select></td>
                                            </tr>'''
        else:
            contents = contents + f'''<tr>
                                            <th scope="row">{data['항목명']}</th>
                                            <td><input type="{data['입력창']}" name="{data['name']}" {data['attributes']}></td>
                                        </tr>'''

    contents = contents + '''</tbody>
                                    <tfoot>
                                        <tr>
                                            <th scope="row" colspan="2"><input type="submit" value="제출"><input type="button" value="돌아가기" onclick="location.href='/ra'"></th>
                                        </tr>
                                    </tfoot></table></form>'''
    return template('영수증 입력', contents)

def post_receipt_data(request_data):
    url = os.getenv('URL_API')+'receipts'
    int_data_list = ['user_id', 'head_count', 'expenditure', 'division_num']
    bool_data_list = ['holiday_check', 'souvenir_record', 'division_program', 'isp_check']
    request_data['house_name'] = 'AVISON'
    request_data['id'] = request_data['program_id'] + str(request_data['datetime'])
    for data in request_data:
        if data in int_data_list:
            request_data[data] = int(request_data[data]) if request_data[data]!='' else None
        if data in bool_data_list:
            request_data[data] = True
        if data == 'datetime':
            sec = f"{int(request_data['sec']):02d}"
            request_data[data] = datetime.strptime(request_data[data] + ':' + sec, "%Y-%m-%dT%H:%M:%S")
            request_data[data] = pytz.timezone("Asia/Seoul").localize(request_data[data])

    # API 요청에 사용할 데이터 변환
    api_request_data = {
        "id": request_data['id'],
        "year": request_data['datetime'].year,
        "month": request_data['datetime'].month,
        "day": request_data['datetime'].day,
        "time": request_data['datetime'].strftime("%H:%M:%S"),
        "date": request_data['datetime'].isoformat(),
        "house_name": request_data['house_name'],
        "user_id": request_data['user_id'],
        "program_id": request_data['program_id'],
        "category_id": request_data['category_id'],
        "division_num": request_data.get('division_num', None),
        "division_program": request_data.get('division_program', False),
        "expenditure": request_data['expenditure'],
        "head_count": request_data['head_count'],
        "holiday_check": request_data.get('holiday_check', False),
        "isp_check": request_data.get('isp_check', False),
        "key_items_quantity": request_data['key_items_quantity'],
        "purchase_details": request_data['purchase_details'],
        "purchase_reason": request_data['purchase_reason'],
        "reason_store": request_data['reason_store'],
        "souvenir_record": request_data.get('souvenir_record', False),
        "store_name": request_data['store_name'],
        "warning_division": request_data.get('warning_division', None),
    }

    code, response_text = api_post_data(url, api_request_data)
    if code == 201:
        flash('성공적으로 처리되었습니다.', 'success')
        return redirect(url_for("ra"))
    else:
        flash(f"에러 발생 : {response_text}", 'error')
        return redirect(url_for("ra/post_receipt"))


def modify_and_save_excel(data):
    try:
        date = datetime.strptime(data['date'], '%Y-%m-%d')

        file_name = date.strftime('%y%m%d')+f"(영)_{data['user_name']}RA_{data['program_name']}.xlsx"

        # 엑셀 파일 열기
        workbook = openpyxl.load_workbook(os.getenv("DATA_PATH")+'영수증_양식_파일.xlsx')
        sheet = workbook.active

        # 데이터 수정
        sheet['B3'] = data['house_name']
        sheet['D3'] = data['user_name']
        sheet['B4'] = data['program_name']
        sheet['B5'] = date.strftime('%Y. %m. %d')
        sheet['B6'] = int(data['expenditure'])
        sheet['B7'] = data['reason_store']
        sheet['D5'] = int(data['head_count'])

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            workbook.save(tmp.name)
            tmp_path = tmp.name

        print(f"Temporary file created at {tmp_path}")
        return tmp_path, file_name

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None




def get_files(input_directory, month, period):
    file_extensions = ['.xlsx', '.xls', '.hwp', '.hwpx', '.pdf']
    files = [f for f in os.listdir(input_directory) if any(f.endswith(ext) for ext in file_extensions)]
    year = datetime.now().year

    selected_files = []
    for file in files:
        try:
            date_str = file[:6]
            date = datetime.strptime(date_str, '%y%m%d')
            if date.year == year and date.month == int(month) and (
                    (int(period) == 1 and 1 <= date.day <= 15) or (int(period) == 2 and 16 <= date.day)):
                selected_files.append(file)
        except ValueError:
            print(f"파일명에서 날짜를 추출할 수 없습니다: {file}")
    return sorted(selected_files)


def convert_to_pdf(input_directory, file_path, output_directory):
    if not output_directory:
        os.makedirs(output_directory)

    env = os.environ.copy()
    env['LANG'] = 'ko_KR.UTF-8'
    env['LC_ALL'] = 'ko_KR.UTF-8'
    output_file = os.path.join(output_directory,
                               file_path.replace('.xlsx', '.pdf').replace('.xls', '.pdf'))

    try:
        subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', output_directory,
                        os.path.join(input_directory, file_path)], check=True, env=env)
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error converting {file_path} to PDF: {e}")


def merge_pdfs(pdf_list, output_path):
    merger = PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output_path)
    merger.close()


def process_files(input_directory, output_directory, month, period):
    try:
        receipt_dir = input_directory+'receipts'
        minutes_dir = input_directory+'minutes'
        pdf_files = []
        receipt_files = get_files(receipt_dir, month, period)
        for file in receipt_files:
            pdf_path = convert_to_pdf(receipt_dir, file, output_directory)
            if pdf_path:
                pdf_files.append(pdf_path)
        minutes_pdf = [os.path.join(minutes_dir, f) for f in get_files(minutes_dir, month, period) if f.endswith('.pdf')]
        if minutes_pdf:
            pdf_files.extend(minutes_pdf)

        if not pdf_files:
            return "no_files", None

        merged_pdf_path = os.path.join(output_directory, f"{month}월_{period}차.pdf")
        merge_pdfs(pdf_files, merged_pdf_path)

        for pdf_path in pdf_files:
            os.remove(pdf_path)

        print(f"Merged PDF saved as {merged_pdf_path}")
        return "success", merged_pdf_path
    except Exception as e:
        return "error", e