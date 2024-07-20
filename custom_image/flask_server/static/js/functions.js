function linksSetColor(color) {
    var links = document.querySelectorAll('a');
    var i = 0;
    while (i < links.length) {
        links[i].style.color = color;
        i = i + 1
    }
}
function nightDayShift(self){
    var target = document.querySelector('body');
    if(self.value === 'night'){
        target.style.backgroundColor='black';
        target.style.color='white';
        self.value = 'day';
        linksSetColor('powderblue');

    } else{
        target.style.backgroundColor='white';
        target.style.color='black';
        self.value = 'night';
        linksSetColor('blue');
    }
}

function verifyPassword(callback) {
    var password = prompt("Please enter the admin password:");
    if (password != null && password !== "") {
        callback(password);
    }
}

function goToAdmin(password) {
    window.location.href = '/admin?password=' + encodeURIComponent(password);
}

function promptForPassword() {
    var password = prompt("Please enter the admin password:");
    if (password != null && password !== "") {
        var form = document.createElement("form");
        form.setAttribute("method", "post");
        form.setAttribute("action", "/admin");

        var hiddenField = document.createElement("input");
        hiddenField.setAttribute("type", "hidden");
        hiddenField.setAttribute("name", "password");
        hiddenField.setAttribute("value", password);

        form.appendChild(hiddenField);
        document.body.appendChild(form);
        form.submit();
    }
}

function logoutUser() {
    window.location.href = '/logout';  // Flask 로그아웃 라우트로 이동
}

// functions.js
function showAccountingPopup() {
    // 팝업에 표시할 폼 생성
    const formHtml = `
        <form id="accountingForm" style="padding: 20px; background: white; border-radius: 5px; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1000;">
            <label for="month">Month:</label>
            <select id="month" name="month">
                <option value="1">January</option>
                <option value="2">February</option>
                <option value="3">March</option>
                <option value="4">April</option>
                <option value="5">May</option>
                <option value="6">June</option>
                <option value="7">July</option>
                <option value="8">August</option>
                <option value="9">September</option>
                <option value="10">October</option>
                <option value="11">November</option>
                <option value="12">December</option>
            </select>
            <label for="session">Session:</label>
            <select id="session" name="session">
                <option value="1">1</option>
                <option value="2">2</option>
            </select>
            <button type="button" onclick="submitAccountingForm()">Submit</button>
            <button type="button" onclick="closePopup()">Close</button>
        </form>
        <div id="overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.5); z-index: 999;"></div>
    `;

    // 팝업 폼을 문서에 추가
    document.body.insertAdjacentHTML('beforeend', formHtml);
}

function closePopup() {
    // 폼과 오버레이 제거
    document.getElementById('accountingForm').remove();
    document.getElementById('overlay').remove();
}

function submitAccountingForm() {
    const month = document.getElementById('month').value;
    const session = document.getElementById('session').value;

    // AJAX를 사용하여 서버에 데이터 전송
    fetch('/manager/process_accounting', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ month, session }),
    })
    .then(response => response.json())
    .then(data => {
        alert('Data processed: ' + data.message);
        closePopup();
    })
    .catch(error => console.error('Error:', error));
}
