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

function fetchCSRFToken() {
    return fetch('/get_csrf_token')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch CSRF token');
            }
            return response.json();
        })
        .then(data => data.csrf_token)
        .catch(error => {
            console.error('Error fetching CSRF token:', error);
            return null;  // Return null if there's an error
        });
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
            <label for="month">월:</label>
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
            <label for="period">기간:</label>
            <select id="period" name="period">
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

async function submitAccountingForm() {
    const month = document.getElementById('month').value;
    const period = document.getElementById('period').value;

    try {
        const response = await fetch('/manager/process_accounting', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ month, period })
        });
        const data = await response.json();
        alert('Data processed: ' + data.message);
        closePopup();
    } catch (error) {
        console.error('Error:', error);
    }
}

function createModalOverlay() {
    var formOverlay = document.createElement('div');
    formOverlay.id = 'formOverlay';
    formOverlay.style.cssText = 'position: fixed; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 1000;';
    return formOverlay;
}

function fetchDataAndRenderForm(formType) {
    fetch('/static/data/dict_code.json')  // 데이터 파일 경로 확인
        .then(response => response.json())
        .then(data => renderForm(data, formType))
        .catch(error => {
            console.error(`Error loading data for ${formType}:`, error);
            const formOverlay = document.getElementById('formOverlay');
            formOverlay.innerHTML = '<p>Error loading form!</p>';
        });
}

function renderForm(data, formType) {
    var houseOptions = data.house_names.map(house => `<option value="${house.en_name}">${house.kor_name}</option>`).join('');
    var formContent = createFormContent(houseOptions, formType);
    var formOverlay = document.getElementById('formOverlay');
    formOverlay.innerHTML = formContent;
    document.body.appendChild(formOverlay);
}

function createFormContent(houseOptions, formType) {
    var formDetails = {
        'RA List Registration': {
            title: 'RA List Registration',
            action: '/register_ra_list'
        },
        'Program Registration': {
            title: 'Program Registration',
            action: '/register_program'
        }
    };

    var { title, action } = formDetails[formType];
    return `
        <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 15px rgba(0,0,0,0.5);">
            <h2>${title}</h2>
            <form action="${action}" method="post">
                <label for="semester">Semester:</label>
                <select id="semester" name="semester" required>
                    <option value=1>Spring</option>
                    <option value=2>Fall</option>
                </select><br><br>
                <label for="year">Year:</label>
                <input type="number" id="year" name="year" min="2000" max="2099" step="1" value="${new Date().getFullYear()}" required><br><br>
                <label for="house">House Name:</label>
                <select id="house" name="house" required>
                    ${houseOptions}
                </select><br><br>
                <input type="submit" value="Submit">
                <button type="button" onclick="closeForm()">Cancel</button>
            </form>
        </div>
    `;
}

function closeForm() {
    var formOverlay = document.getElementById('formOverlay');
    document.body.removeChild(formOverlay);
}

function showForm(formType) {
    var formOverlay = createModalOverlay();
    document.body.appendChild(formOverlay);
    fetchDataAndRenderForm(formType);
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

document.addEventListener("DOMContentLoaded", function() {
    const numberCells = document.querySelectorAll("td.number");
    numberCells.forEach(function(cell) {
        cell.textContent = formatNumber(cell.textContent);
    });
});

