import os
import unicodedata

import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from utils import get_house_name, manager_create_xlsx, calculate_week_of_month, get_minutes_data, process_minutes, delete_minutes_detail, fetch_minutes_data, post_minute_data, fetch_ra_list, delete_calendar_event, put_calendar_event, post_calendar_event, get_calendar_event, get_program_list, update_ra_authority, get_ra_list_sorted, get_files, get_files_from_directory, process_files, ra_login, upload_file, register_ra_list, register_program_list, form_post_receipt, post_receipt_data, get_receipt_list, modify_and_save_excel, delete_receipt_data
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()



app = Flask(__name__)
secret_key = os.getenv("SECRET_KEY")
app.secret_key = secret_key  # Needed for session management and flash messages
app.config['UPLOAD_FOLDER_ADMIN'] = os.getenv('UPLOAD_FOLDER_ADMIN')  # 업로드 파일을 저장할 서버 내 경로
app.config['UPLOAD_FOLDER_RA'] = os.getenv('UPLOAD_FOLDER_RA')  # 업로드 파일을 저장할 서버 내 경로
app.config['UPLOAD_FOLDER_TMP'] = os.getenv('UPLOAD_FOLDER_TMP')  # 업로드 파일을 저장할 서버 내 경로
app.config['UPLOAD_FOLDER_MANAGER'] = os.getenv('UPLOAD_FOLDER_MANAGER')
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 최대 파일 크기 제한(예: 16MB)

@app.route("/", methods=["GET"])
def home():
    if session.get('manager') or session.get('admin') or session.get('ra'):
        return render_template("03_info.html", tab_id="main")
    else:
        return render_template("03_info.html", tab_id="main", login='login')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        user_id = request.form["userId"]
        auth, data = ra_login(os.getenv("URL_API")+"check_user/", user_id)
        if auth == 'manager':
            session['manager'] = True
            session['userId'] = user_id
            session['userName'] = data['user_name']
            session['userData'] = data['user_data']
            flash('Logged in as manager!', 'success')
        elif auth == 'ra':
            session['ra'] = True
            session['userId'] = user_id
            session['userName'] = data['user_name']
            session['userData'] = data['user_data']
            flash('Logged in as RA', 'success')
        elif auth == 'worngid':
            flash("Invalid id", 'error')
        else:
            flash('Invalid login', 'warning')
        return redirect("/")

@app.route('/logout')
def logout():
    session.clear()  # 세션 데이터 모두 제거
    flash('You have been successfully logged out.', 'info')
    return redirect("/")  # 홈 페이지로 리디렉션

@app.route("/calendar")
def calendar():
    # Check user role from session
    if session.get('manager') or session.get('ra'):
        year_semester_house = session['userData']
        # year_semester_house = "2024-1-AVISON"
        url_program = os.getenv('URL_API') + 'program'
        try:
            programs = get_program_list(url_program, year_semester_house)
            return render_template("calendar.html", programs=programs)
        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'error')
            return redirect("/")
    else:
        flash('You are not authorized to access this page', 'warning')
        return redirect("/")

@app.route("/calendar/get/events")
def get_events():
    url = os.getenv('URL_API') + 'calendar/house/'+session['userData'].split('-')[-1]
    datas = get_calendar_event(url)
    events = []
    if datas is None:
        return jsonify([])
    for data in datas:
        date_start = datetime.strptime(data['start_datetime'], "%Y-%m-%dT%H:%M:%S.%f")
        date_end = datetime.strptime(data['end_datetime'], "%Y-%m-%dT%H:%M:%S.%f")

        start_date = date_start.strftime("%Y-%m-%dT%H:%M:%S")
        end_date = date_end.strftime("%Y-%m-%dT%H:%M:%S")

        event = {
            'id': data['id'],
            'title': data['program_id'],
            'start': start_date,
            'end': end_date,
            'type': 'isp' if data['isp_card'] == True else 'card',
            'backgroundColor': '#28a745' if data['isp_card'] else '#007bff',
            'extendedProps': {
                'user': data['user_id']
            }
        }
        events.append(event)
    return jsonify(events)

@app.route("/calendar/submit/create", methods=["POST"])
def submit_event():
    if session.get('manager') or session.get('ra'):
        data = request.get_json()
        date_start = datetime.strptime(data['start_datetime'], "%Y-%m-%dT%H:%M")
        date_end = datetime.strptime(data['end_datetime'], "%Y-%m-%dT%H:%M")
        data['start_datetime'] = date_start.strftime("%Y-%m-%dT%H:%M:%S")+'.000001'
        data['end_datetime'] = date_end.strftime("%Y-%m-%dT%H:%M:%S")+'.000001'

        data['user_id'] = session.get('userName')
        data['house_name'] = session['userData'].split('-')[-1]

        url = os.getenv("URL_API")+"calendar/create"  # Replace with your actual API URL
        message, code = post_calendar_event(url, data)
        if code == 201:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'message': message+str(data)}), code
    else:
        flash('You are not authorized to access this page', 'warning')
        return redirect("/")


@app.route("/calendar/submit/update", methods=["POST"])
def update_event():
    if session.get('manager') or session.get('ra'):

        if session.get('ra'):
            event_id = request.json['event_id']
            userid = session.get('userName')
            verify_url = os.getenv('URL_API') + f'calendar/verify/{str(event_id)}?user_id={userid}'
            response = requests.get(verify_url)
            if response.status_code != 200:
                return jsonify({'success': False, 'message': response.json().get('message')}), 403

        data = request.get_json()  # Get data from the client
        date_start = datetime.strptime(data['start_datetime'], "%Y-%m-%dT%H:%M")
        date_end = datetime.strptime(data['end_datetime'], "%Y-%m-%dT%H:%M")
        data['start_datetime'] = date_start.strftime("%Y-%m-%dT%H:%M:%S") + '.000001'
        data['end_datetime'] = date_end.strftime("%Y-%m-%dT%H:%M:%S") + '.000001'

        # Build the URL and make the request
        url = os.getenv("URL_API") + "calendar/update/" + str(data['event_id'])
        body = {key: data[key] for key in data.keys() if key != 'event_id'}  # Exclude the event_id from the data sent
        message, code = put_calendar_event(url, body)
        if code == 200:
            return jsonify({'success': True, 'message': message}), code
        else:
            return jsonify({'success': False, 'message': message+str(body)}), code
    else:
        return jsonify({'success': False, 'message': 'Not authorized'}), 403

@app.route("/calendar/submit/delete", methods=["POST"])
def delete_event():
    if session.get('manager') or session.get('ra'):
        del_id = request.json['event_id']
        if session.get('ra'):
            userid = session.get('userName')
            verify_url = os.getenv('URL_API') + f'calendar/verify/{str(del_id)}?user_id={userid}'
            response = requests.get(verify_url)
            if response.status_code != 200:
                return jsonify({'success': False, 'message': response.json().get('message')}), 403

        url = os.getenv("URL_API") + "calendar/delete/" + str(del_id)
        message, code = delete_calendar_event(url)
        if code == 200:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'message': message}), code
    else:
        return jsonify({'success': False, 'message': 'Not authorized'}), 403

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        admin_password = os.getenv("ADMIN_PASSWORD")
        input_password = request.form['password']
        if input_password == admin_password:
            session['admin'] = True
            flash('Logged in successfully', 'success')
            return redirect("/admin")  # 리디렉션하여 GET 요청 처리
        else:
            flash("Invalid password", "error")
            return redirect("/")
    elif request.method == "GET":
        if 'admin' in session and session['admin']:
            auth_true, auth_false = get_ra_list_sorted()
            columns = ['year', 'semester', 'house_name', 'user_name', 'user_id', 'email_address']
            return render_template("admin.html", auth_true=auth_true, auth_false=auth_false, columns=columns)
        else:
            flash("You are not logged in", "error")
            return redirect("/")  # 홈 페이지로 리디렉션

@app.route("/admin/authority/create", methods=["POST"])
def create_authority():
    if session.get('admin'):
        user_id = request.form['userId']
        category, message = update_ra_authority(user_id, True)
        flash(message, category)
        return redirect("/admin")
    else:
        flash("You do not have permission to create authority", "error")
        return redirect("/")

@app.route("/admin/authority/delete", methods=["POST"])
def delete_authority():
    if session.get('admin'):
        user_id = request.form.get('userId')
        category, message = update_ra_authority(user_id, False)
        flash(message, category)
        return redirect("/admin")
    else:
        flash("You do not have permission to create authority", "error")
        return redirect("/")

@app.route('/upload/admin', methods=['POST'])
def handle_upload_admin():
    if 'admin' not in session or not session['admin']:
        flash('You are not logged in', "error")
        return redirect(url_for('/'))  # 메인 페이지로 리다이렉션

    return upload_file(app.config["UPLOAD_FOLDER_ADMIN"], url_for("admin"), "admin")


@app.route("/manager/check_list")
def manager():
    if session.get('manager'):
        house_name = session['userData'].split('-')[-1]
        columns = ['date', 'user_name', 'time', 'expenditure', 'store_name', 'category_id', 'program_name',
                   'head_count', 'purchase_reason', 'key_items_quantity', 'purchase_details', 'reason_store']
        raw_data = get_receipt_list(os.getenv("URL_API") + 'receipts/house', house_name)

        # Get current year and month
        now = datetime.now()
        year = now.year
        current_month = now.month

        if not raw_data:
            return render_template("03_check_list.html", tab_id="check_list", columns=columns, current_period=1,
                                   current_month=current_month)

        # Get year and month from query parameters
        month = request.args.get('month', type=int)
        period = request.args.get('period', type=int)

        receipt_files = []
        minutes_files = []
        etc_files = []
        receipt_dir = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/receipts"
        minutes_dir = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/minutes"
        etc_dir = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/etc"
        filtered_data = [item for item in raw_data if item['year'] == year]

        if period and month:
            filtered_data = [item for item in filtered_data if item['month'] == month]
            if period == 1:
                filtered_data = [item for item in filtered_data if int(item['day']) <= 15]
            elif period == 2:
                filtered_data = [item for item in filtered_data if int(item['day']) > 15]

            receipt_files = get_files(receipt_dir, month, period)
            minutes_files = get_files(minutes_dir, month, period)
            etc_files = get_files(etc_dir, month, period)

        elif month:
            filtered_data = [item for item in filtered_data if item['month'] == month]
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

        for i in filtered_data:
            i['date'] = i['date'].split('T')[0]

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
        return render_template("03_check_list.html", data=filtered_data, tab_id="check_list", columns=columns, current_period=period,
                               current_month=current_month, selected_month=month, file_pairs=file_pairs, etc_files=etc_files)
    elif session.get('ra'):
            flash("You do not have permission to access this page.", "warning")
            return redirect("/")
    else:
        flash("please login first", "warning")
        return redirect("/")

@app.route("/manager/setup")
def manager_setup():
    if session.get('manager'):
        files = get_files_from_directory(os.getenv("UPLOAD_FOLDER_TMP"))
        year_semester_house = session['userData']
        ra_list = []
        ra_list_raw = fetch_ra_list(year_semester_house)
        for item in ra_list_raw:
            ra_data = '학번: '+str(item['user_id'])+' / 이름: '+item['user_name']+' / 관리자 권한: '+str(item['authority'])
            ra_list.append(ra_data)
        programs = get_program_list(os.getenv('URL_API') + 'program', year_semester_house)
        return render_template("03_setup.html", tab_id="setup", data=files, ras=ra_list, programs=programs)
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/manager/accounting")
def manager_accounting():
    if session.get('manager'):
        now = datetime.now()
        current_month = now.month
        return render_template("03_accounting.html", tab_id="accounting", current_month=current_month)
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/manager/delete_receipt", methods=["POST"])
def delete_receipt():
    if session.get('manager'):
        receipt_id = request.form.get('id')
        delete = delete_receipt_data(os.getenv("URL_API")+"receipts/", receipt_id)
        if delete:
            flash("Receipt deleted", "success")
        else:
            flash(f"Receipt with id {id} not deleted", "error")
        return redirect("/manager/check_list")
    else:
        flash("You do not have permission to access this button.", "error")
        return redirect("/")

@app.route('/upload/manager', methods=['POST'])
def handle_upload_manager():
    if session.get('manager'):
        return upload_file(app.config["UPLOAD_FOLDER_TMP"], '/manager/setup', "manager")
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/manager/download_file", methods=["POST"])
def download_file():
    file_type = request.form['type']
    filename = request.form['filename']
    pdf_filename = request.form['pdf']
    house_name = session['userData'].split('-')[-1]
    if file_type == 'receipt':
        directory = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/receipts"
    elif file_type == 'etc':
        directory = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/etc"
    elif file_type == 'minute':
        directory = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/minutes"
        # if pdf_filename:
        #     filename = filename + '.pdf'
        # else:
        #     filename = filename + '.hwp'
        filename = filename + '.hwp'
    elif file_type == 'setup':
        directory = os.getenv("UPLOAD_FOLDER_TMP")
    else:
        flash("Invalid file type.", "error")
        return redirect("/manager/check_list")
    file_path = os.path.join(directory, filename)
    return send_file(file_path, as_attachment=True)

@app.route("/manager/delete_file", methods=["POST"])
def delete_file():
    file_type = request.form['type']
    filename = request.form['filename']
    pdf_filename = request.form['pdf']
    house_name = session['userData'].split('-')[-1]

    if file_type == 'receipt':
        directory = os.getenv("UPLOAD_FOLDER_RA")+f"/{house_name}/receipts"
    elif file_type == 'etc':
        directory = os.getenv("UPLOAD_FOLDER_RA")+f"/{house_name}/etc"
    elif file_type == 'minute':
        directory = os.getenv("UPLOAD_FOLDER_RA")+f"/{house_name}/minutes"
        if pdf_filename:
            filename = [filename + '.pdf', filename + '.hwp']
        else:
            filename = filename + '.hwp'
    elif file_type == 'setup':
        directory = os.getenv("UPLOAD_FOLDER_TMP")
    else:
        flash("Invalid file type.", "error")
        return redirect("/manager/check_list")

    try:
        if type(filename) == list:
            for i in filename:
                try:
                    os.remove(os.path.join(directory, i))
                except OSError:
                    continue
        else:
            os.remove(os.path.join(directory, filename))
        flash(f"{str(filename)} has been deleted.", "success")
    except FileNotFoundError:
        flash(f"{filename} not found.", "error")

    if file_type == 'setup':
        return redirect("/manager/setup")
    else:
        return redirect("/manager/check_list")

@app.route('/register_ra_list', methods=['GET', 'POST'])
def handle_register_ra_list():
    if session.get('manager'):
        set_data = request.form.to_dict()
        set_data['authority'] = False
        return register_ra_list(set_data, app.config["UPLOAD_FOLDER_TMP"], '/manager/setup')
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route('/register_program', methods=['GET', 'POST'])
def handle_register_program():
    if session.get('manager'):
        set_data = request.form.to_dict()
        return register_program_list(set_data, app.config["UPLOAD_FOLDER_TMP"], "/manager/setup")
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route('/manager/process_accounting', methods=['POST'])
def process_accounting():
    if session.get('manager'):
        data = request.form.to_dict()
        month = data['month']
        period = data['period']
        house_name = session['userData'].split('-')[-1]
        data_dir = os.getenv('UPLOAD_FOLDER_RA')+f'/{house_name}/'
        result_path = os.getenv("UPLOAD_FOLDER_MANAGER")+f"/{house_name}"
        trial, message, merged_pdf_path = process_files(get_house_name(house_name), data_dir, result_path, month, period)
        if trial == "success":
            try:
                response = send_file(
                    merged_pdf_path,
                    as_attachment=True,
                    download_name=merged_pdf_path.split('/')[-1],
                    mimetype="application/pdf"
                )
                os.remove(merged_pdf_path)
                flash(f"{month}월_{period}차 processed successfully, file_path={message}", "success")
                return response
            except Exception as e:
                flash(f"An error occurred while downloading the file: {e}", "error")
                return redirect("/manager/accounting")
        elif trial == "no_files":
            flash(f"{month}월_{period}차 파일이 존재하지 않습니다. 기간 선택을 확인하세요.", "info")
        else:
            flash(f"Processing failed, error: {message}", "error")
        return redirect("/manager/accounting")
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route('/manager/process_xlsx', methods=['POST'])
def manager_process_xlsx():
    if session.get('manager'):
        data = request.form.to_dict()
        month = int(data['month'])
        period = int(data['period'])
        house_name = session['userData'].split('-')[-1]
        tmp_path, file_name = manager_create_xlsx(month, period, house_name, year_semester_house=session['userData'])
        if tmp_path and file_name:
            try:
                response = send_file(
                    tmp_path,
                    as_attachment=True,
                    download_name=file_name,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                os.remove(tmp_path)  # 파일 전송 후 임시 파일 삭제
                return response
            except Exception as e:
                flash(f"An error occurred while downloading the file: {e}", "error")
                return redirect("/manager/accounting")
        elif file_name:
            flash(file_name, "error")
        else:
            flash("No data to process", "info")
        return redirect("/manager/accounting")
    else:
        flash("You do not have permission to access this job.", "warning")
        return redirect("/")

@app.route('/manager/check_minutes')
def check_minutes():
    if session.get('manager'):
        year_semester_house = session['userData']

        if request.args.get("month"):
            selected_month = request.args.get('month', type=int)
            selected_week = request.args.get('week', type=int)
            month, week, date = calculate_week_of_month(selected_month, selected_week)
        else:
            month, week, date = calculate_week_of_month()

        content, not_yet, text1, text2 = get_minutes_data(year_semester_house, f'{str(month)}-{str(week)}')

        return render_template('03_check_minutes.html', tab_id='minutes', data=content, text1=text1, text2=text2, month=month, week=week, date=date, not_yet=not_yet)
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")


@app.route("/ra/check_ra_list")
def ra():
    if session.get('ra') or session.get('manager'):
        user_id = session['userId']
        columns = ['date', 'user_name', 'time', 'expenditure', 'store_name', 'category_id', 'program_name',
                   'head_count', 'purchase_reason', 'key_items_quantity', 'purchase_details', 'reason_store']
        raw_data = get_receipt_list(os.getenv("URL_API")+'receipts/user', user_id)

        if not raw_data:
            return render_template("03_check_ra_list.html", data=None, columns=columns, tab_id="check_ra_list")
        data = raw_data
        for i in data:
            i['date'] = i['date'].split('T')[0]
        return render_template("03_check_ra_list.html", data=data, columns=columns, tab_id='check_ra_list')
    else:
        flash("Please login first.", "warning")
        return redirect("/")

@app.route("/ra/upload_ra")
def upload_ra():
    if session.get('ra') or session.get('manager'):
        house_name = session['userData'].split('-')[-1]
        receipt_dir = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/receipts"
        minutes_dir = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/minutes"
        etc_dir = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/etc"

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

        return render_template("03_upload_ra.html", tab_id='upload_ra', file_pairs=file_pairs, etc_files=etc_files)
    else:
        flash("Please login first.", "warning")
        return redirect("/")

@app.route('/ra/create_xlsx', methods=['POST'])
def create_xlsx():
    data = request.form.to_dict()
    data['house_name'] = session['userData'].split('-')[-1]
    tmp_path, file_name = modify_and_save_excel(data)
    if tmp_path and file_name:
        try:
            response = send_file(
                tmp_path,
                as_attachment=True,
                download_name=file_name,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            os.remove(tmp_path)  # 파일 전송 후 임시 파일 삭제
            return response
        except Exception as e:
            flash(f"An error occurred while downloading the file: {e}", "error")
            return redirect("/")
    else:
        flash("Unexpected error", "error")
    return redirect("/")

@app.route('/upload/ra', methods=['POST'])
def handle_upload_ra():
    if session.get('ra') or session.get('manager'):
        house_name = session['userData'].split('-')[-1]
        return upload_file(app.config["UPLOAD_FOLDER_RA"]+'/'+house_name, "/ra/upload_ra", "ra")
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/ra/post_receipt")
def post_receipt_form():
    if session.get('ra') or session.get('manager'):
        user_id = session['userId']
        year_semester_house = session['userData']
        title, contents = form_post_receipt(year_semester_house, user_id)
        return render_template('03_post_receipt.html', contents=contents, tab_id='post_receipt')
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/ra/post_receipt_data", methods=['POST'])
def post_receipt():
    if session.get('ra') or session.get('manager'):
        datas = {}
        for data in request.form:
            datas[data] = request.form[data]
        datas['house_name'] = session['userData'].split('-')[-1]
        return post_receipt_data(datas)
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/ra/minutes")
def minutes_form():
    if session.get('ra') or session.get('manager'):
        year_semester_house = session['userData']

        if request.args.get("month"):
            selected_month = request.args.get("month", type=int)
            selected_week = request.args.get("week", type=int)
            month, week, date = calculate_week_of_month(selected_month, selected_week)
        else:
            month, week, date = calculate_week_of_month()

        datas, code = fetch_minutes_data(year_semester_house, f'{str(month)}-{str(week)}')
        user_id = int(session['userId'])

        user_data, processed_data = process_minutes(datas, user_id, year_semester_house, str(month)+"-"+str(week))
        return render_template("03_minute.html", user=user_data, data=processed_data, tab_id='minutes', month=month, week=week)
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/ra/minutes/post", methods=['POST'])
def post_minutes():
    if session.get('ra') or session.get('manager'):
        user_id = int(request.form['user_id'])
        year_semester_house = request.form['year_semester_house']
        week = request.form['week']
        common = request.form['common'] == 'true'

        category_contents = []
        for i in range(1, 5):
            content = request.form.get(str(i), '')
            category_contents.append({
                "category": i,
                "content": content
            })

        data = {
            'year_semester_house': year_semester_house,
            'user_id': user_id,
            'week': week,
            'common': common,
            'category_contents': category_contents
        }

        category, message = post_minute_data(data)
        flash(str(message), category)
        return redirect("/ra/minutes")
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/ra/minutes/delete", methods=['POST'])
def delete_minutes():
    if session.get('ra') or session.get('manager'):
        minute_id = request.form['id']
        category, message = delete_minutes_detail(minute_id)
        flash(message, category)
        return redirect("/ra/minutes")
    else:
        flash("You do not have permission to access this page.", "warning")

@app.route("/ra/download/template", methods=['POST']) #양식파일 다운로드
def download_template():
    if session.get('ra') or session.get('manager'):
        category = request.form.get('category')
        data_dir = os.getenv("DATA_PATH")
        if category == 'receipt':
            file_name = "241001(영)_000RA_프로그램명_심야.xlsx"
        elif category == 'minutes':
            file_name = "240000(회)_OOORA_AVISON 프로그램명.hwp"
        elif category == 'gift':
            file_name = "240902(기)_000RA_프로그램명.xlsx"
        else:
            flash("잘못된 요청입니다.", 'error')
            return redirect("/")
        return send_file(os.path.join(data_dir, file_name), as_attachment=True)


if __name__ == "__main__":
    app.run('0.0.0.0',port=8088)# 로컬에서 개발할 때 사용하는 디버거 모드. 운영 환경에서는 x