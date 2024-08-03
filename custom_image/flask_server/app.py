import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

from utils import ra_login, upload_file, register_ra_list, register_program_list, form_post_receipt, post_receipt_data, get_receipt_list, modify_and_save_excel
from dotenv import load_dotenv
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
        columns = ['date', 'time', 'expenditure', 'store_name', 'category_id', 'program_name', 'purchase_reason', 'key_items_quantity', 'purchase_details']
        data = get_receipt_list(os.getenv("URL_API")+'receipts/house', house_name)
        if not data:
            return render_template("manager.html", data=None, columns=columns)
        return render_template("manager.html", data=data, columns=columns)
    elif session.get('ra'):
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")
    else:
        flash("please login first", "warning")
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
        data = request.get_json()
        month = data['month']
        data_session = data['session']
        # 월과 회차 데이터 처리 로직
        return jsonify(message=f"Month: {month}, Session: {data_session} processed successfully")
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/ra")
def ra():
    if session.get('ra') or session.get('manager') or session.get('admin'):
        user_id = session['userId']
        columns = ['user_name', 'date', 'time', 'expenditure', 'store_name', 'category_id', 'program_name', 'head_count', 'purchase_reason', 'key_items_quantity', 'purchase_details', 'reason_store']
        raw_data = get_receipt_list(os.getenv("URL_API")+'receipts/user', user_id)
        if not raw_data:
            return render_template("ra.html", data=None, columns=columns)
        data = raw_data
        for i in raw_data:
            i['date'] = i['date'].split('T')[0]
        return render_template("ra.html", data=data, columns=columns)
    else:
        flash("Please login first.", "warning")
        return redirect("/")

@app.route('/ra/create_xlsx', methods=['POST'])
def create_xlsx():
    data = request.form.to_dict()
    data['house_name'] = session['userData'].split('-')[-1]
    save_path, error = modify_and_save_excel(data, os.getenv("UPLOAD_FOLDER_TMP"))
    if save_path:
        flash(f"{save_path}file created", "success")
    else:
        flash(f"file not created. error:{error}", "error")
    return redirect("/ra")
    # flash(f"{data}")
    # return redirect("/ra")
    # return modify_and_save_excel(data, os.getenv("UPLOAD_FOLDER_TMP"))

@app.route('/upload/ra', methods=['POST'])
def handle_upload_ra():
    if session.get('ra') or session.get('manager') or session.get('admin'):
        return upload_file(app.config["UPLOAD_FOLDER_RA"], url_for("ra"))
    else:
        flash("You do not have permission to access this page.", "warning")
        return redirect("/")

@app.route("/ra/post_receipt")
def post_receipt_form():
    if session.get('ra') or session.get('manager') or session.get('admin'):
        return form_post_receipt("2024-1-AVISON")
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