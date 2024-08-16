import os
import unicodedata
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from utils import get_program_list, update_ra_authority, get_ra_list_sorted, get_files, get_files_from_directory, process_files, ra_login, upload_file, register_ra_list, register_program_list, form_post_receipt, post_receipt_data, get_receipt_list, modify_and_save_excel, delete_receipt_data
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
    return render_template("main.html")

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
            session['userData'] = data['user_data']
            flash('Logged in as manager!', 'success')
        elif auth == 'ra':
            session['ra'] = True
            session['userId'] = user_id
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
    if session.get('manager') or session.get('admin') or session.get('ra'):
        year_semester_house = "2024-1-AVISON"
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

@app.route("/calendar/submit/create", methods=["POST"])
def submit_event():
    if session.get('manager') or session.get('admin') or session.get('ra'):
        data = request.get_json()  # JSON 데이터를 정확하게 받아옵니다.
        # 데이터 처리 로직 (예: 데이터베이스에 저장)
        flash(f"{str(data)} event submitted", "success")
        return jsonify({'success': True, 'message': f'{str(data)} Event successfully created'}), 200
    else:
        flash('You are not authorized to access this page', 'warning')
        return redirect("/")

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


@app.route("/manager")
def manager():
    if session.get('manager') or session.get('admin'):
        house_name = session['userData'].split('-')[-1]
        columns = ['date', 'user_name', 'time', 'expenditure', 'store_name', 'category_id', 'program_name',
                   'head_count', 'purchase_reason', 'key_items_quantity', 'purchase_details', 'reason_store']
        raw_data = get_receipt_list(os.getenv("URL_API") + 'receipts/house', house_name)

        if not raw_data:
            return render_template("manager.html", data=None, columns=columns)

        # Get current year and month
        now = datetime.now()
        year = now.year
        current_month = now.month

        # Get year and month from query parameters
        month = request.args.get('month', type=int)
        period = request.args.get('period', type=int)

        receipt_files = []
        minutes_files = []
        receipt_dir = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/receipts"
        minutes_dir = os.getenv("UPLOAD_FOLDER_RA") + f"/{house_name}/minutes"
        filtered_data = [item for item in raw_data if item['year'] == year]

        if period and month:
            filtered_data = [item for item in filtered_data if item['month'] == month]
            if period == 1:
                filtered_data = [item for item in filtered_data if int(item['day']) <= 15]
            elif period == 2:
                filtered_data = [item for item in filtered_data if int(item['day']) > 15]

            receipt_files = get_files(receipt_dir, month, period)
            minutes_files = get_files(minutes_dir, month, period)

        elif month:
            filtered_data = [item for item in filtered_data if item['month'] == month]
            for i in range(1, 3):
                receipt_files_period = get_files(receipt_dir, month, i)
                minutes_files_period = get_files(minutes_dir, month, i)
                receipt_files.extend(receipt_files_period)
                minutes_files.extend(minutes_files_period)
        else:
            receipt_files = get_files_from_directory(receipt_dir)
            minutes_files = get_files_from_directory(minutes_dir)

        for i in filtered_data:
            i['date'] = i['date'].split('T')[0]

        hwp_files = [f.split(".")[0] for f in minutes_files if f.endswith('.hwp')]
        pdf_files = [unicodedata.normalize('NFC', f.split(".")[0]) for f in minutes_files if f.endswith('.pdf')]
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
        return render_template("manager.html", data=filtered_data, columns=columns, current_period=period,
                               current_month=current_month, selected_month=month, file_pairs=file_pairs)
    elif session.get('ra'):
            flash("You do not have permission to access this page.", "warning")
            return redirect("/")
    else:
        flash("please login first", "warning")
        return redirect("/")

@app.route("/manager/delete_receipt", methods=["POST"])
def delete_receipt():
    if session.get('manager') or session.get('admin'):
        receipt_id = request.form.get('id')
        delete = delete_receipt_data(os.getenv("URL_API")+"receipts/", receipt_id)
        if delete:
            flash("Receipt deleted", "success")
        else:
            flash(f"Receipt with id {id} not deleted", "error")
        return redirect("/manager")
    else:
        flash("You do not have permission to access this button.", "error")
        return redirect("/")

@app.route('/upload/manager', methods=['POST'])
def handle_upload_manager():
    if session.get('manager') or session.get('admin'):
        return upload_file(app.config["UPLOAD_FOLDER_TMP"], url_for("manager"), "manager")
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/manager/download_file", methods=["POST"])
def download_file():
    file_type = request.form['type']
    filename = request.form['filename']
    pdf_filename = request.form['pdf']

    if file_type == 'receipt':
        directory = os.getenv("UPLOAD_FOLDER_RA") + "/AVISON/receipts"
    elif file_type == 'minute':
        directory = os.getenv("UPLOAD_FOLDER_RA") + "/AVISON/minutes"
        if pdf_filename:
            filename = filename + '.pdf'
        else:
            filename = filename + '.hwp'
    else:
        flash("Invalid file type.", "error")
        return redirect("/manager")
    file_path = os.path.join(directory, filename)
    return send_file(file_path, as_attachment=True)

@app.route("/manager/delete_file", methods=["POST"])
def delete_file():
    file_type = request.form['type']
    filename = request.form['filename']
    pdf_filename = request.form['pdf']

    if file_type == 'receipt':
        directory = os.getenv("UPLOAD_FOLDER_RA")+"/AVISON/receipts"
    elif file_type == 'minute':
        directory = os.getenv("UPLOAD_FOLDER_RA")+"/AVISON/minutes"
        if pdf_filename:
            filename = [filename + '.pdf', filename + '.hwp']
        else:
            filename = filename + '.hwp'
    else:
        flash("Invalid file type.", "error")
        return redirect("/manager")

    try:
        if type(filename) == list:
            for i in filename:
                os.remove(os.path.join(directory, i))
        else:
            os.remove(os.path.join(directory, filename))
        flash(f"{str(filename)} has been deleted.", "success")
    except FileNotFoundError:
        flash(f"{filename} not found.", "error")

    return redirect("/manager")

@app.route('/register_ra_list', methods=['GET', 'POST'])
def handle_register_ra_list():
    if session.get('manager') or session.get('admin'):
        set_data = request.form.to_dict()
        set_data['authority'] = False
        return register_ra_list(set_data, app.config["UPLOAD_FOLDER_TMP"], url_for("manager"))
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route('/register_program', methods=['GET', 'POST'])
def handle_register_program():
    if session.get('manager') or session.get('admin'):
        set_data = request.form.to_dict()
        return register_program_list(set_data, app.config["UPLOAD_FOLDER_TMP"], url_for("manager"))
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route('/manager/process_accounting', methods=['POST'])
def process_accounting():
    if session.get('manager') or session.get('admin'):
        data = request.form.to_dict()
        month = data['month']
        period = data['period']
        house_name = session['userData'].split('-')[-1]
        data_dir = os.getenv('UPLOAD_FOLDER_RA')+f'/{house_name}/'
        result_path = os.getenv("UPLOAD_FOLDER_MANAGER")+f"/{house_name}"
        trial, message = process_files(data_dir, result_path, month, period)
        if trial == "success":
            flash(f"{month}월_{period}차 processed successfully, file_path={message}", "success")
            return send_file(message, as_attachment=True)
        elif trial == "no_files":
            flash(f"{month}월_{period}차 파일이 존재하지 않습니다. 기간 선택을 확인하세요.", "info")
        else:
            flash(f"Processing failed, error: {message}", "error")
        return redirect("/manager")
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")



@app.route("/ra")
def ra():
    if session.get('ra') or session.get('manager') or session.get('admin'):
        user_id = session['userId']
        columns = ['date', 'user_name', 'time', 'expenditure', 'store_name', 'category_id', 'program_name',
                   'head_count', 'purchase_reason', 'key_items_quantity', 'purchase_details', 'reason_store']
        raw_data = get_receipt_list(os.getenv("URL_API")+'receipts/user', user_id)
        if not raw_data:
            return render_template("ra.html", data=None, columns=columns)
        data = raw_data
        for i in data:
            i['date'] = i['date'].split('T')[0]
        return render_template("ra.html", data=data, columns=columns)
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
    if session.get('ra') or session.get('manager') or session.get('admin'):
        house_name = session['userData'].split('-')[-1]
        return upload_file(app.config["UPLOAD_FOLDER_RA"]+'/'+house_name, url_for("ra"), "ra")
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/ra/post_receipt")
def post_receipt_form():
    if session.get('ra') or session.get('manager') or session.get('admin'):
        user_id = session['userId']
        # year_semester_house = session['userData']
        year_semester_house = '2024-1-AVISON'
        return form_post_receipt(year_semester_house, user_id)
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/ra/post_receipt_data", methods=['POST'])
def post_receipt():
    if session.get('ra') or session.get('manager') or session.get('admin'):
        datas = {}
        for data in request.form:
            datas[data] = request.form[data]
        return post_receipt_data(datas)
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

if __name__ == "__main__":
    app.run('0.0.0.0',port=8088, debug=True)# 로컬에서 개발할 때 사용하는 디버거 모드. 운영 환경에서는 x