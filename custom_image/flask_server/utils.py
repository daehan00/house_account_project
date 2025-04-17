import os
import re
import time
import json
import pytz
import openpyxl
import requests
import tempfile
import subprocess
import unicodedata
import pandas as pd

from datetime import datetime
from PyPDF2 import PdfMerger

from flask import flash, redirect, request
from multiprocessing import Pool
from dotenv import load_dotenv
load_dotenv()

def load_dict_code():
    try:
        with open(os.getenv("DATA_PATH")+'dict_code.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

def get_calendar_event(url):
    try:
        response = requests.get(url)
        if response.status_code == 404:
            return []  # 404 Not Found 에러 발생 시 빈 목록 반환
        response.raise_for_status()  # 다른 HTTP 에러 발생 시 예외를 발생시킴
        return response.json()  # 정상적인 경우, 응답 JSON 반환
    except requests.RequestException as e:
        return []  # 예외 발생 시 빈 목록 반환


def post_calendar_event(url, data):
    try:
        response = requests.post(url, json=data)

        if response.status_code == 201:
            return f"{data['program_id']} 예약 제출되었습니다.", 201
        else:
            return response.text, 400
    except requests.RequestException as e:
        return f"알 수 없는 에러가 발생했습니다.", 500

def put_calendar_event(url, data):
    try:
        response = requests.put(url, json=data)

        if response.status_code == 200:
            return '수정 성공했습니다.', 200
        else:
            return '수정 실패했습니다.', 400
    except requests.RequestException as e:
        return f"알 수 없는 에러가 발생했습니다.", 500

def delete_calendar_event(url):
    try:
        headers = {
            "Accept": "application/json"
        }
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            return "삭제되었습니다.", 200
        elif response.status_code == 404:
            return '찾을 수 없습니다.', 404
        else:
            return '삭제 실패했습니다.', 400
    except requests.RequestException as e:
        return "알 수 없는 에러가 발생했습니다.", 500

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
            options = {"program_id": program['program_id'],
                       "program_name": program['program_name']}
            program_list.append(options)
        return program_list  # 반환 값은 JSON 데이터
    else:
        return program_list

def get_ra_list(year_semester_house):
    data = fetch_ra_list(year_semester_house)
    ra_list = []
    if type(data) == type([]):
        for ra in data:
            options = {"program_id": ra['user_id'],
                       "program_name": ra['user_name']}
            ra_list.append(options)
    return ra_list  # 반환 값은 JSON 데이터

def get_ra_list_sorted():
    headers = {"Accept": "application/json"}

    response = requests.get(os.getenv("URL_API")+'ra_list/get', headers=headers)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)

        df_sorted = df.sort_values(by='user_name')

        auth_true = df_sorted[df_sorted['authority']]
        auth_false = df_sorted[~df_sorted['authority']]

        return auth_true.to_dict(orient='records'), auth_false.to_dict(orient='records')
    else:
        return None, None

def fetch_ra_list(year_semester_house):
    url = os.getenv("URL_API")+'ra_list/search'

    params = {
        'house_name': year_semester_house.split('-')[-1],
        'year': int(year_semester_house.split('-')[0]),
        'semester': int(year_semester_house.split('-')[1])
    }

    # 요청을 보내고 응답을 받음
    response = requests.get(url, params=params)

    # 응답 코드가 200 OK인 경우
    if response.status_code == 200:
        ra_list = response.json()  # JSON 응답을 파싱
        return ra_list
    elif response.status_code == 404:
        return []
    else:
        # 서버 에러 또는 데이터 없음 등의 문제 처리
        error_message = response.json().get('message', 'An error occurred')
        return {'error': error_message, 'status_code': response.status_code}

def update_ra_authority(user_id, authority):
    url = os.getenv("URL_API") + 'ra_list/update/' + str(user_id)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    data = json.dumps({
        "authority": authority
    })

    response = requests.put(url, headers=headers, data=data)

    if response.status_code == 200:
        if authority:
            return 'success', f'{user_id} 권한 부여되었습니다.'
        else:
            return 'success', f'{user_id} 권한 삭제되었습니다.'
    else:
        return 'error', f"{user_id}, {response.text}"

def ra_login(url, user_id, password):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    body = {
        "user_id" : user_id,
        "password" : password
    }
    response = requests.post(url, headers=headers, json=body)

    data = response.json()
    if response.status_code == 200:
        if data.get('authority'):
            return 'manager', data
        else :
            return 'ra', data
    elif response.status_code == 404:
        return 'Wrong Id', None
    elif response.status_code == 401:
        return 'Invalid password', None
    else:
        return 'error', None
    
def set_password(url, user_id, user_name, password):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    body = {
        "user_id" : user_id,
        "user_name" : user_name,
        "password" : password
    }
    response = requests.post(url=url, headers=headers, json=body)
    data = response.json()
    result = True if response.status_code == 200 else False
    message = "등록 성공했습니다." if response.status_code == 200 else '등록 실패했습니다.'

    return result, message

def get_receipt_list(url, search_id=None):
    headers = {
        "Accept": "application/json"
    }
    if search_id:
        response = requests.get(f"{url}/{search_id}", headers=headers)
    else:
        response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        sorted_data = sorted(data, key=lambda x: (datetime.fromisoformat(x['date']).date(), not (x.get('isp_check') == True), datetime.strptime(x['time'], "%H:%M:%S").time()))
        # sorted_data = sorted(data, key=lambda x: datetime.fromisoformat(x['date']))
        return sorted_data  # 반환 값은 JSON 데이터
    else:
        return None

def delete_receipt_data(url, id):
    headers = {
        "Accept": "application/json"
    }
    response = requests.delete(f"{url}/{id}", headers=headers)
    if response.status_code == 204:
        return True
    else:
        return False

def get_house_code(house_name):
    # Open the JSON file and load data
    data = load_dict_code()

    # Loop through the list of house names to find a match
    for house in data['house_names']:
        if house['kor_name'] == house_name:
            return house['en_name']

    # Handle the case where the house name is not found
    return None

def get_house_name(house_code):
    # Open the JSON file and load data
    data = load_dict_code()

    # Loop through the list of house names to find a match
    for house in data['house_names']:
        if house['en_name'] == house_code:
            return house['kor_name']

    # Handle the case where the house name is not found
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
                    normalized_filename = unicodedata.normalize('NFC', filename)
                    if "(영)" in normalized_filename:
                        return upload_folder+'/receipts', filename, 'success'
                    else:
                        return upload_folder+'/etc', filename, 'success'
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

EXT_PRIORITY = {
    'xls': 1,
    'xlsx': 1,
    'hwp': 2,
    'pdf': 3
}

def get_priority(filename):
    """파일명으로부터 우선순위(정수)를 구하는 헬퍼 함수"""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return EXT_PRIORITY.get(ext, 999)

def upload_file(upload_folder, redirect_url, div):
    files = request.files.getlist('file')
    if not files:
        flash('파일이 없습니다.', 'error')
        return redirect(request.url)
    
    # -----------------------------------------------------
    # [1] "확장자 우선순위" 기준으로 정렬
    # -----------------------------------------------------
    sorted_files = sorted(files, key=lambda f: get_priority(f.filename))

    # -----------------------------------------------------
    # [2] 정렬된 순서대로 "검증 + 저장" 시도
    #     → 하나라도 실패 시 전체 롤백 (원자화)
    # -----------------------------------------------------
    saved_paths = []  # 성공적으로 저장된 파일 경로 리스트 (롤백용)
    try:
        for file_obj in sorted_files:
            # 2-1) 검증 (allowed_file)
            upload_folder_, filename, result = allowed_file(
                upload_folder, file_obj.filename, div
            )

            # 검증 실패 → 전체 업로드 중단 & 롤백
            if result != 'success':
                if result == 'pdf_error':
                    flash(f'업로드가 취소되었습니다.\n"{filename}" 회의록 한글 파일이 없습니다. 한글 파일을 업로드해주세요.', 'error')
                elif result == 'name_error':
                    flash(f'업로드가 취소되었습니다.\n"{filename}" 파일명 설정이 잘못되었습니다. 파일명을 확인해주세요.', 'error')
                else:
                    flash(f'업로드가 취소되었습니다.\n"{filename}" 유효하지 않은 파일 타입입니다.', 'error')
                
                # 이미 저장된 파일 삭제
                for path in saved_paths:
                    if os.path.exists(path):
                        os.remove(path)
                return redirect(redirect_url)
            
            # 2-2) 저장 시도
            #      - IOError 발생 시 롤백
            if not os.path.exists(upload_folder_):
                os.makedirs(upload_folder_, exist_ok=True)
            
            save_path = os.path.join(upload_folder_, filename)
            file_obj.save(save_path)  # 여기서 IOError 등 발생 가능
            saved_paths.append(save_path)
    
    except IOError:
        # 저장 중 문제가 생기면 롤백
        for path in saved_paths:
            if os.path.exists(path):
                os.remove(path)
        flash('파일 저장 중 오류가 발생하여 업로드를 취소했습니다.', 'error')
        return redirect(request.url)

    # -----------------------------------------------------
    # [3] 모든 파일 저장 성공 시
    # -----------------------------------------------------
    flash('모든 파일이 정상 업로드되었습니다.', 'success')
    return redirect(redirect_url)

def get_files_from_directory(directory_path):
    try:
        files = os.listdir(directory_path)
        files = [file for file in files if not file.startswith('.')]
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
    house_code = set_data['house']
    authority = set_data['authority']
    success_list = []
    failure_list = []
    fail_text_list = []

    file_list = os.listdir(data_dir)
    for file_name in file_list:
        file_path = os.path.join(data_dir, file_name)
        try:
            data = pd.read_excel(file_path, header=1, dtype=object)
        except ValueError as e:
            continue  # 다음 파일로 넘어갑니다.

        col_list = ['학번', '이름', '이메일', '연락처']
        if not all(col in data.columns for col in col_list):
            continue

        data_dict = data.to_dict(orient='records')

        for data in data_dict:
            division_num = data.get('분반', None)
            email_address = data['이메일']
            house_name = house_code
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
                success_list.append(user_id)
            else:
                failure_list.append(f"{user_id}, {code}")
                fail_text_list.append(response_text)


        os.remove(os.path.join(data_dir, file_name))

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
            data = data.dropna(subset=['하우스'])
            selected_col = ['하우스', '프로그램명', '카테고리']
            data = data[selected_col]
        except:
            continue

        data_dict = data.to_dict(orient='records')
        i = 1
        for program in data_dict:
            if program['하우스'] == get_house_name(house_code):
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
                    success_list.append(program_id)
                else:
                    failure_list.append(f"{program_id}, {code}")
                    fail_text_list.append(response_text)
                i += 1
                time.sleep(0.1)
            else:
                continue
        os.remove(os.path.join(data_dir, file_name))

    flash(f"작업 완료. 총 {len(success_list)}건 성공, {len(failure_list)}건 실패.", 'info')
    return redirect(redirect_url)

def form(input_type, name, name_id, attribute, content, options=None, required=True):
    """폼 필드 생성 함수에 required 파라미터 추가"""
    attributes = f'{attribute}="{content}"' if content else ''
    if required:
        attributes += ' required'  # 필수 입력 필드로 설정
    if input_type == 'select':
        return {'입력창': input_type, '항목명': name, 'name': name_id, 'options': options, 'attributes': attributes}
    else:
        return {'입력창': input_type, '항목명': name, 'name': name_id, 'attributes': attributes}

def form_mul(input_type, name, name_id, attribute, content, options=None, required=True):
    """attribute와 content를 리스트로 받아 여러 속성을 가진 입력창 생성"""
    attributes = ''
    if content:
        attributes = ' '.join(f'{attribute[i]}="{content[i]}"' for i in range(len(attribute)))
    if required:
        attributes += ' required'  # 필수 입력 필드로 설정
    if input_type == 'select':
        return {'입력창': input_type, '항목명': name, 'name': name_id, 'options': options, 'attributes': attributes}
    else:
        return {'입력창': input_type, '항목명': name, 'name': name_id, 'attributes': attributes}

def generate_form_data(year_semester_house, user_id):
    today = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%dT%H:%M')
    user_list = get_ra_list(year_semester_house)
    for user in user_list:
        if int(user['program_id']) == int(user_id):
            user.update({'selected': 'selected'})
            break
    category_expenses = get_category_expenses()
    url_program = os.getenv('URL_API')+'program'
    try:
        program_list = get_program_list(url_program, year_semester_house)
    except Exception:
        return redirect("/ra")

    form_data = [
        form('select', '사용자명', 'user_id', '', '', options=user_list),
        form('checkbox', '주말, 법정 공휴일 및 심야 사용 여부', 'holiday_check', '', '', required=False),
        form('select', '계정항목', 'category_id','placeholder', '', options=category_expenses),
        form('select', '프로그램명', 'program_id', '', '', options=program_list),
        form('text', '구매 핵심 사유', 'purchase_reason', 'placeholder', 'ex) 운영물품 구매'),
        form('text', '핵심 품목 및 수량', 'key_items_quantity', 'placeholder', 'ex) 콜라 등 5종'),
        form('textarea', '구매 내역(종류와 단가)', 'purchase_details', 'placeholder', '실물의 경우에는 정확하게 작성하세요.\n쿠팡의 경우에는 간단하게 요약 작성하세요.'),
        form('number', '인원', 'head_count', 'min', '1'),
        form('datetime-local', '결제일시', 'datetime', 'value', today),
        form_mul('number', '초', 'sec', ['min', 'max'], ['0', '60']),
        form('number', '금액', 'expenditure', 'step', '10'),
        form('text', '가맹점명', 'store_name', 'placeholder', '영수증에 나온 그대로'),
        form('checkbox', '기념품지급대장 작성여부', 'souvenir_record', 'placeholder', '', required=False),
        form('checkbox', '분반 프로그램 여부', 'division_program', 'placeholder', '', required=False),
        form_mul('number', '분반', 'division_num', ['min', 'max'], ['1', '12'], required=False),
        form('text', '업체 선정 사유', 'reason_store', 'placeholder', 'ex) 최저가 업체'),
        form('checkbox', 'isp 사용여부', 'isp_check', 'placeholder', '', required=False)
    ]
    return form_data

def post_receipt_data(request_data):
    url = os.getenv('URL_API')+'receipts'
    int_data_list = ['user_id', 'head_count', 'expenditure', 'division_num']
    bool_data_list = ['holiday_check', 'souvenir_record', 'division_program', 'isp_check']
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
        return redirect("/ra/check_ra_list")
    elif code == 400 and 'duplicate' in response_text:
        flash('이미 제출된 내용입니다.', 'warning')
        return redirect("/ra/post_receipt")
    else:
        flash(f"에러 발생 : {response_text}", 'error')
        return redirect("/ra/post_receipt")


def modify_and_save_excel(data, ftype):
    try:
        date = datetime.strptime(data['date'], '%Y-%m-%d')

        file_name = date.strftime('%y%m%d')+f"(영)_{data['user_name']}RA_{data['program_name']}.xlsx"

        # 엑셀 파일 열기
        given_file_name = "영수증_양식_파일_가로.xlsx" if ftype == "wid" else "영수증_양식_파일_세로.xlsx"
        workbook = openpyxl.load_workbook(os.getenv("DATA_PATH")+given_file_name)
        sheet = workbook.active

        # 데이터 수정
        sheet['B3'] = data['house_name']
        sheet['D3'] = data['user_name']
        sheet['B4'] = data['program_name']
        sheet['B5'] = date.strftime('%Y. %m. %d')
        sheet['B6'] = int(data['expenditure'])
        sheet['B7'] = data['category_id']
        sheet['D5'] = int(data['head_count'])

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            workbook.save(tmp.name)
            tmp_path = tmp.name

        return tmp_path, file_name

    except Exception as e:
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
            pass
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
        return None


def merge_pdfs(pdf_list, output_path):
    merger = PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output_path)
    merger.close()


# 병렬처리 함수
def delete_file(file):
    try:
        os.remove(file)
    except Exception as e:
        pass

def terminate_libreoffice():
    try:
        subprocess.run(['pkill', '-f', 'soffice.bin'], check=True)
    except subprocess.CalledProcessError as e:
        pass

def process_files(house_name, input_directory, output_directory, month, period):
    try:
        receipt_dir = os.path.join(input_directory, 'receipts')
        minutes_dir = os.path.join(input_directory, 'minutes')
        etc_dir = os.path.join(input_directory, 'etc')
        pdf_files = []
        del_pdf_files = []

        # 파일 리스트 가져오기
        receipt_files = get_files(receipt_dir, month, period)
        etc_files = get_files(etc_dir, month, period)

        # 병렬 처리할 파일 리스트 생성
        all_files = [(receipt_dir, file, output_directory) for file in receipt_files] + \
                    [(etc_dir, file, output_directory) for file in etc_files]

        # 병렬로 convert_to_pdf 실행
        with Pool(processes=2) as pool:
            results = pool.starmap(convert_to_pdf, all_files)

        # 변환된 파일 중 유효한 파일만 pdf_files 리스트에 추가
        for result in results:
            if result:
                pdf_files.append(result)
                del_pdf_files.append(result)

        # 회의록 파일 추가 (이미 PDF이므로 병렬처리 불필요)
        minutes_pdf = [os.path.join(minutes_dir, f) for f in get_files(minutes_dir, month, period) if f.endswith('.pdf')]
        if minutes_pdf:
            pdf_files.extend(minutes_pdf)

        if not pdf_files:
            return "no_files", None, None

        # PDF 병합
        merged_pdf_path = os.path.join(output_directory, f"{house_name}_영수증 및 회의록 등_{month}월{period}차.pdf")
        merge_pdfs(pdf_files, merged_pdf_path)

        # 병렬로 파일 삭제
        with Pool(processes=os.cpu_count()) as pool:
            pool.map(delete_file, del_pdf_files)

        return "success", f"{house_name}_영수증 및 회의록 등_{month}월{period}차.pdf", merged_pdf_path
    except Exception as e:
        return "error", e, None
    finally:
        terminate_libreoffice()

def post_minute_data(data):
    try:
        headers = {'Content-Type': 'application/json'}
        url = os.getenv("URL_API") + 'report_details'
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 201:
            return 'success', "보고사항 제출 완료"
        else:
            return 'warning', "보고사항 제출 실패."
    except requests.RequestException as e:
        return 'error', "알 수 없는 에러가 발생했습니다."

def fetch_minutes_data(year_semester_house, week):
    headers = {"Accept": "application/json"}
    base_url = os.getenv("URL_API") + 'report_details/week'

    # 쿼리 파라미터를 URL에 추가
    params = {
        'year_semester_house': year_semester_house,
        'week': week
    }

    response = requests.get(base_url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return data, 200  # 성공한 경우 데이터와 상태 코드를 반환
    elif response.status_code == 404:
        return [], 404  # 리포트가 없는 경우
    else:
        return None, response.status_code  # 에러 처리

def delete_minutes_detail(minute_id):
    try:
        url = os.getenv("URL_API") + 'report_details/'+str(minute_id)
        headers = {"Accept": "application/json"}
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            return 'success', "삭제 성공했습니다."
        elif response.status_code == 404:
            return 'warning', "삭제 실패했습니다."
        else:
            return 'error', response.text
    except requests.RequestException as e:
        return 'error', "알 수 없는 에러가 발생했습니다."

def process_minutes(datas, user_id, year_semester_house, week):
    user_data = None
    other_datas = []
    if datas:
        for data in datas:
            if data['user_id'] == user_id:
                user_data = data
            else:
                other_datas.append(data)

    if not user_data:
        user_data = {
            'submit': True,
            'year_semester_house': year_semester_house,
            'user_id': user_id,
            'week': week,
            'common': False,
            'category_contents': [
                {"category": 1, "content": "미제출"},
                {"category": 2, "content": "미제출"},
                {"category": 3, "content": "미제출"},
                {"category": 4, "content": "미제출"}
            ]
        }

    processed_data = []
    ra_list = fetch_ra_list(year_semester_house)
    for ra in ra_list:
        if ra['user_id'] != user_id:
            ra_found = next((item for item in other_datas if item['user_id'] == ra['user_id']), None)
            if not ra_found:
                ra_data = {'year_semester_house': year_semester_house,
                           'user_id': ra['user_id'],
                           'user_name': ra['user_name'],
                           'week': week,
                           'division_num': ra['division_num'],
                           'common': False,
                           'category_contents': [
                               {"category": 1, "content": "미제출"},
                               {"category": 2, "content": "미제출"},
                               {"category": 3, "content": "미제출"},
                               {"category": 4, "content": "미제출"}
                           ]}
                processed_data.append(ra_data)
            else:
                ra_data = ra_found
                ra_data['user_name'] = ra['user_name']
                ra_data['division_num'] = ra['division_num']  # division_num 추가
                processed_data.append(ra_data)
    sorted_processed_data = sorted(processed_data, key=lambda k: k['division_num'])
    return user_data, sorted_processed_data

def get_minutes_data(year_semester_house, week):
    data, code = fetch_minutes_data(year_semester_house, week)
    ra_list = fetch_ra_list(year_semester_house)

    ra_dict = {ra['user_id']: {'user_name': ra['user_name'], 'division_num': ra['division_num']} for ra in ra_list}
    for item in data:
        user_id = item['user_id']
        if user_id in ra_dict:
            item['user_name'] = ra_dict[user_id]
            item['division_num'] = ra_dict[user_id]['division_num']
        else:
            item['user_name'] = 'Unknown'  # 혹시 user_id가 없는 경우
            item['division_num'] = float('inf')
    data_user_ids = {item['user_id'] for item in data}  # data에 있는 모든 user_id 집합
    not_yet = [ra['user_name'] for ra in ra_list if ra['user_id'] not in data_user_ids]  # data에 없는 ra_name 리스트
    not_yet_str = ', '.join(sorted(not_yet))

    sorted_data = sorted(data, key=lambda k: k['division_num'])
    text1 = ''
    text2 =''
    for item in sorted_data:
        text1 += f"({str(item['user_name']['division_num'])}분반) {item['user_name']['user_name']}\n" + f"""  - 완료사항: {item['category_contents'][0]['content']}\n""" + f"""  - 예정사항: {item['category_contents'][1]['content']}\n"""
        if item['category_contents'][2].get('content'):
            text1 += f"  - 건의사항: {item['category_contents'][2]['content']}\n"
        text1 += "\n"
        if item['category_contents'][3].get('content'):
            text2 += f"{item['user_name']['user_name']} - {item['category_contents'][3]['content']}\n"

    return sorted_data, not_yet_str, text1.rstrip(), text2.rstrip()

def calculate_week_of_month(month=None, week=None):
    import pendulum
    if month and week:
        year = pendulum.now('Asia/Seoul').year
        # 해당 연도, 월, 주차의 첫 번째 월요일을 계산하고, 수요일로 이동
        first_day_of_month = pendulum.datetime(year, month, 1, tz='Asia/Seoul')
        first_monday_offset = (7 - first_day_of_month.day_of_week) % 7
        first_monday = first_day_of_month.add(days=first_monday_offset)
        seoul_time = first_monday.add(weeks=week - 1, days=-1)  # 주의 수요일
    else:
        # month와 week가 없는 경우 현재 시간을 설정
        seoul_time = pendulum.now('Asia/Seoul')

    # 이번 달의 첫 번째 월요일을 계산
    first_day_of_month = seoul_time.start_of('month')
    first_monday_offset = (7 - first_day_of_month.day_of_week) % 7
    first_monday = first_day_of_month.add(days=first_monday_offset)
    korean_weekdays = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
    first_formatted_date = first_monday.format('YYYY-MM-DD') + ' ' + korean_weekdays[first_monday.day_of_week]

    # 오늘이 첫 번째 월요일 이후 몇 주째인지 계산
    if seoul_time < first_monday:
        return seoul_time.month, 1, first_formatted_date  # 첫 번째 월요일 이전이면 1주차
    else:
        week_of_month = ((seoul_time - first_monday).days // 7) + 2
        current_monday = first_monday.add(weeks=week_of_month - 1)  # 해당 주차의 월요일 계산
        formatted_date = current_monday.format('YYYY-MM-DD') + ' ' + korean_weekdays[current_monday.day_of_week]
        return seoul_time.month, week_of_month, formatted_date


def manager_create_xlsx(month, period, house_name, year_semester_house):
    year = datetime.now().year
    url = os.getenv("URL_API")
    rec_url = url + f"receipts/house/{str(house_name)}/year/{str(year)}/month/{str(month)}"
    receipt_list = get_receipt_list(rec_url)
    if not receipt_list:
        return None, None

    try:
        col_list = ["No", "결제일자", "금액", "가맹점명", "주말휴일심야사용여부", "신규프로그램여부", "계정항목", "하우스", "프로그램명", "구매핵심사유&핵심품목및수량", "사용인원",
                    "적요통합", "비고"]
        rows_list = []

        for idx, receipt in enumerate(receipt_list, start=1):
            purchase_reason = receipt['purchase_reason'] + "/" + receipt['key_items_quantity']
            new_row = {
                'No': idx,
                "결제일자": receipt['date'].split("T")[0],
                "금액": receipt['expenditure'],
                "가맹점명": receipt['store_name'],
                "주말휴일심야사용여부": "사용" if receipt['holiday_check'] else "미사용",
                "신규프로그램여부": "기존",
                "계정항목": receipt['category_id'],
                "하우스": get_house_name(receipt['house_name']),
                "프로그램명": receipt['program_name'],
                "구매핵심사유&핵심품목및수량": f"{str(receipt.get('division_num'))}분반 " + purchase_reason if receipt.get('division_program') else purchase_reason,
                "사용인원": receipt['head_count'],
                "적요통합": "",
                "비고": "기념품지급대장 작성" if receipt['souvenir_record'] else receipt.get('purchase_details', "")
            }
            rows_list.append(new_row)

        data_receipts = pd.DataFrame(rows_list, columns=col_list)

        rec_data = get_receipt_list(url + f"receipts/house/", house_name)
        selected_data = []
        for data in rec_data:
            if data['month'] < month:
                selected_data.append(data)
            elif data['month'] == month:
                if period == 1:
                    if int(data['day']) <= 15:
                        selected_data.append(data)
                if period == 2:
                    selected_data.append(data)

        df = pd.DataFrame(selected_data, columns=['program_name', 'category_id', 'expenditure'])
        pivot_df = df.pivot_table(index='program_name', columns='category_id', values='expenditure', aggfunc='sum', fill_value=0)
        pro_url = url + "program"
        program_data = get_program_list(pro_url, year_semester_house)
        program_list = []
        for program in program_data:
            program_list.append(program['program_name'])
        # 열 순서 정의
        data = load_dict_code()
        category = data['category_expenses']
        columns_order = [x['kor_name'] for x in category]
        # columns_order = ['운영비', '기념품', '상품', '소모품', '인건비', '식비/다과비', '인쇄비']

        final_df = pivot_df.reindex(program_list, columns=columns_order, fill_value=0).reset_index()
        file_name = f'{house_name}_{str(month)}월_{str(period)}차.xlsx'
        file_path = os.getenv("UPLOAD_FOLDER_TMP") + file_name
        writer = pd.ExcelWriter(file_path, engine='openpyxl')

        # 데이터프레임을 각각의 시트에 저장
        data_receipts.to_excel(writer, sheet_name='월간정산자료', index=False)
        final_df.to_excel(writer, sheet_name='사용내역', index=False)

        # 파일 저장
        writer.close()

        return file_path, file_name
    except Exception as e:
        return None, f"unexpected exception: {e}"
    

def get_filtered_data(raw_data, period, month):
    if not raw_data:
        return []
    filtered_data = [item for item in raw_data if item['year'] == datetime.now().year]

    period = '' if period == 100 else period
    month = '' if month == 100 else month
    
    if period and month:
        filtered_data = [item for item in filtered_data if item['month'] == month]
        if period == 1:
            filtered_data = [item for item in filtered_data if int(item['day']) <= 15]
        elif period == 2:
            filtered_data = [item for item in filtered_data if int(item['day']) > 15]
    elif month:
        filtered_data = [item for item in filtered_data if item['month'] == month]
    else:
        pass
    for item in filtered_data:
        item['date'] = item['date'].split('T')[0]
    
    return filtered_data

def get_file_pairs_and_etc(house_name, period, month):
    receipt_files = []
    minutes_files = []
    etc_files = []
    receipt_dir = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/receipts"
    minutes_dir = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/minutes"
    etc_dir = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/etc"
    
    period = '' if period == 100 else period
    month = '' if month == 100 else month

    if period and month:
        receipt_files = get_files(receipt_dir, month, period)
        minutes_files = get_files(minutes_dir, month, period)
        etc_files = get_files(etc_dir, month, period)
    elif month:
        for i in range(1, 3):
            receipt_files_period = get_files(receipt_dir, month, i)
            minutes_files_period = get_files(minutes_dir, month, i)
            etc_files_period = get_files(etc_dir, month, i)
            receipt_files.extend(receipt_files_period)
            minutes_files.extend(minutes_files_period)
            etc_files.extend(etc_files_period)
    else:
        receipt_files = get_files_from_directory(receipt_dir)
        minutes_files = get_files_from_directory(minutes_dir)
        etc_files = get_files_from_directory(etc_dir)

    hwp_files = [f.replace('.hwp', '') for f in minutes_files if f.endswith('.hwp')]
    pdf_files = [unicodedata.normalize('NFC', f.replace('.pdf', '')) for f in minutes_files if f.endswith('.pdf')]
    minutes_data = []
    for i in hwp_files:
        if unicodedata.normalize('NFC', i) in pdf_files:
            i = {'filename': i, 'pdf': '제출'}
        else:
            i = {'filename': i, 'pdf': '미제출'}
        minutes_data.append(i)
    
    # 두 리스트를 zip하고, 만약 길이가 다르면 None으로 채우기
    max_len = max(len(receipt_files), len(minutes_data))
    receipt_files.extend([{'filename': None, 'pdf': None}] * (max_len - len(receipt_files)))
    minutes_data.extend([{'filename': None, 'pdf': None}] * (max_len - len(minutes_data)))

    file_pairs = zip(receipt_files, minutes_data)

    return file_pairs, etc_files