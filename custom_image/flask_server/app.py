import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
from pytz import timezone
from utils import template, upload_file, register_ra_list
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = 'sckey'  # Needed for session management and flash messages
app.config['UPLOAD_FOLDER_ADMIN'] = os.getenv('UPLOAD_FOLDER_ADMIN')  # 업로드 파일을 저장할 서버 내 경로
app.config['UPLOAD_FOLDER_RA'] = os.getenv('UPLOAD_FOLDER_RA')  # 업로드 파일을 저장할 서버 내 경로
app.config['UPLOAD_FOLDER_TMP'] = os.getenv('UPLOAD_FOLDER_TMP')  # 업로드 파일을 저장할 서버 내 경로
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

@app.route("/post_reciept", methods=['GET', 'POST'])
def post_reciept():
    if request.method == 'GET':
        today = datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%dT%H:%M')

        def form(format, name, attribute, content):
            return {'입력창': format, '항목명': name, 'attribute': attribute, 'content': content}

        form_list = [
            form('text', '사용자명', 'placeholder', '홍길동'),
            form('checkbox', '주말, 법정 공휴일 및 심야 사용 여부', '', ''),
            form('text', '계정항목', 'placeholder', '변경예정'),
            form('text', '프로그램명', 'placeholder', ''),
            form('text', '구매 핵심 사유&핵심 품목 및 수량', 'placeholder', ''),
            form('text', '구매 내역(종류와 단가)', 'placeholder', ''),
            form('number', '인원', 'min', '1'),
            form('datetime-local', '결제일시', 'value', today),
            form('number', '결제초', 'max', '99'),
            form('number', '금액', 'placeholder', '200000'),
            form('text', '가맹점명', 'placeholder', '영수증에 나온 그대로 입력'),
            form('checkbox', '기념품지급대장 작성여부', 'placeholder', ''),
            form('checkbox', '분반 프로그램 여부', 'placeholder', ''),
            form('number', '분반', 'max', '12'),
            form('text', '업체 선정 사유', 'placeholder', 'ex) 최저가 업체'),
            form('checkbox', 'isp 여부', 'placeholder', '')
        ]
        contents = '''<main>영수증 입력 양식</main>
                        <form action="/post_reciept" method="POST">
                            <table>
                                <thead>
                                    <tr>
                                      <th scope="col">항목명</th>
                                      <th scope="col">입력</th>
                                    </tr>
                                  </thead>
                                  <tbody>'''
        for data in form_list:
            contents = contents + f'''<tr>
                                        <th scope="row">{data['항목명']}</th>
                                        <td><input type="{data['입력창']}" name="{data['항목명']}" {data['attribute']}="{data['content']}"></td>
                                    </tr>'''
        contents = contents + '''</tbody>
                                <tfoot>
                                    <tr>
                                        <th scope="row" colspan="2"><input type="submit" value="제출"></th>
                                    </tr>
                                </tfoot></table></form>'''
        return template('영수증 입력',contents)
    elif request.method == 'POST':
        datas=''
        for data in request.form:
            datas = datas+data+': '+request.form[data]+'<br>'
        return datas+'<input type="button" value="돌아가기" onclick="location.href='+"'/post_reciept'"+'">'

if __name__ == "__main__":
    app.run('0.0.0.0',port=8088)# 로컬에서 개발할 때 사용하는 디버거 모드. 운영 환경에서는 x