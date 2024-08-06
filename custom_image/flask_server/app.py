import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from utils import convert_and_merge_excel_to_pdf, ra_login, upload_file, register_ra_list, register_program_list, form_post_receipt, post_receipt_data, get_receipt_list, modify_and_save_excel, delete_receipt_data
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
            return render_template("admin.html")
        else:
            flash("You are not logged in", "error")
            return redirect("/")  # 홈 페이지로 리디렉션

@app.route('/upload/admin', methods=['POST'])
def handle_upload_admin():
    if 'admin' not in session or not session['admin']:
        flash('You are not logged in', "error")
        return redirect(url_for('/'))  # 메인 페이지로 리다이렉션

    return upload_file(app.config["UPLOAD_FOLDER_ADMIN"], url_for("admin"))


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
        current_year = now.year
        current_month = now.month

        # Get year and month from query parameters
        year = request.args.get('year', default=current_year, type=int)
        month = request.args.get('month', type=int)

        if year and month:
            filtered_data = [item for item in raw_data if item['year'] == year and item['month'] == month]
        elif year:
            filtered_data = [item for item in raw_data if item['year'] == year]
        else:
            filtered_data = raw_data

        for i in filtered_data:
            i['date'] = i['date'].split('T')[0]

        return render_template("manager.html", data=filtered_data, columns=columns, current_year=current_year,
                               current_month=current_month)
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
        return upload_file(app.config["UPLOAD_FOLDER_TMP"], url_for("manager"))
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

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
        data_dir = os.getenv('UPLOAD_FOLDER_RA')+'/'+house_name
        result_path = os.getenv("UPLOAD_FOLDER_MANAGER")+f"/{house_name}"
        trial, message = convert_and_merge_excel_to_pdf(data_dir, result_path, month, period)
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
        columns = ['date', 'time', 'expenditure', 'store_name', 'category_id', 'program_name', 'head_count', 'purchase_reason', 'key_items_quantity', 'purchase_details', 'reason_store']
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
        return upload_file(app.config["UPLOAD_FOLDER_RA"]+'/'+house_name, url_for("ra"))
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