import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import pytz
from utils import upload_file, register_ra_list, register_program_list, form_post_reciept
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

@app.route('/logout')
def logout():
    session.clear()  # 세션 데이터 모두 제거
    flash('You have been successfully logged out.')
    return redirect("/")  # 홈 페이지나 로그인 페이지로 리디렉션

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        admin_password = os.getenv("ADMIN_PASSWORD")
        input_password = request.form['password']
        if input_password == admin_password:
            session['admin'] = True
            return render_template("admin.html")
        else:
            flash("Invalid password", "error")
            return redirect("/")
    elif request.method == "GET":
        if 'admin' in session and session['admin']:
            return render_template("admin.html")
        else:
            flash("You are not logged in", "error")
            return redirect("/")

@app.route('/upload/admin', methods=['POST'])
def handle_upload_admin():
    if 'admin' not in session or not session['admin']:
        flash('You are not logged in')
        return redirect(url_for('/'))  # 메인 페이지로 리다이렉션

    return upload_file(app.config["UPLOAD_FOLDER_ADMIN"], url_for("admin"))


@app.route("/manager")
def manager():
    return render_template("manager.html")

@app.route('/upload/manager', methods=['POST'])
def handle_upload_manager():
    # if 'admin' not in session or not session['admin']:
    #     flash('You are not logged in')
    #     return redirect(url_for('/'))  # 메인 페이지로 리다이렉션

    return upload_file(app.config["UPLOAD_FOLDER_TMP"], url_for("manager"))

@app.route('/register_ra_list', methods=['GET', 'POST'])
def handle_register_ra_list():
    set_data = request.form.to_dict()
    set_data['authority'] = False
    return register_ra_list(set_data, app.config["UPLOAD_FOLDER_TMP"], url_for("manager"))

@app.route('/register_program', methods=['GET', 'POST'])
def handle_register_program():
    set_data = request.form.to_dict()
    return register_program_list(set_data, app.config["UPLOAD_FOLDER_TMP"], url_for("manager"))

@app.route('/manager/process_accounting', methods=['POST'])
def process_accounting():
    data = request.get_json()
    month = data['month']
    session = data['session']
    # 월과 회차 데이터 처리 로직
    return jsonify(message=f"Month: {month}, Session: {session} processed successfully")

@app.route("/ra")
def ra():
    return render_template("ra.html")

@app.route('/upload/ra', methods=['POST'])
def handle_upload_ra():
    # if 'admin' not in session or not session['admin']:
    #     flash('You are not logged in')
    #     return redirect(url_for('/'))  # 메인 페이지로 리다이렉션

    return upload_file(app.config["UPLOAD_FOLDER_RA"], url_for("ra"))


@app.route("/ra/post_reciept", methods=['GET', 'POST'])
def post_reciept():
    if request.method == 'GET':
        today = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%dT%H:%M')
        return form_post_reciept(today,"2024-1-AVISON")

    elif request.method == 'POST':
        datas=''
        for data in request.form:
            datas = datas+data+': '+request.form[data]+'<br>'
        return datas+'<input type="button" value="돌아가기" onclick="location.href='+"'/ra/post_reciept'"+'">'

if __name__ == "__main__":
    app.run('0.0.0.0',port=8088)# 로컬에서 개발할 때 사용하는 디버거 모드. 운영 환경에서는 x