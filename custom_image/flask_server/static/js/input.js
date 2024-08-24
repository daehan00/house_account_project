function getCookie (name) {
	var nameOfCookie = name + "=";
	var x=0;
	while (x <= document.cookie.length) {
		var y=(x+nameOfCookie.length);
		if (document.cookie.substring(x,y)==nameOfCookie) {
			if ( (endOfCookie = document.cookie.indexOf(";",y)) == -1)
				endOfCookie = document.cookie.length;
			return unescape(document.cookie.substring(y, endOfCookie));
		}
		x = document.cookie.indexOf(" ", x) + 1;
		if (x == 0) break;
	}
	return "";
}

function setCookie (name, value, expiredays) {
	var todayDate = new Date();
	todayDate.setDate(todayDate.getDate() + expiredays);
	document.cookie = name + "=" + escape(value) + "; path=/; expires=" + todayDate.toGMTString() + ";"
}

function open_cwindow(name, url, left, top, width, height, toolbar, menubar, statusbar, scrollbar, resizable) {
	toolbar_str = toolbar ? 'yes' : 'no';
	menubar_str = menubar ? 'yes' : 'no';
	statusbar_str = statusbar ? 'yes' : 'no';
	scrollbar_str = scrollbar ? 'yes' : 'no';
	resizable_str = resizable ? 'yes' : 'no';
	var windowOuterHeight = 5;
	var centerLeft = parseInt((window.screen.availWidth - width) / 2);
	var centerTop = parseInt(((window.screen.availHeight - height) / 2) - windowOuterHeight);
	window.open(url, name, 'left='+centerLeft+',top='+centerTop+',width='+width+',height='+height+',toolbar='+toolbar_str+',menubar='+menubar_str+',status='+statusbar_str+',scrollbars='+scrollbar_str+',resizable='+resizable_str);
}

function open_window(name, url, left, top, width, height, toolbar, menubar, statusbar, scrollbar, resizable) {
	toolbar_str = toolbar ? 'yes' : 'no';
	menubar_str = menubar ? 'yes' : 'no';
	statusbar_str = statusbar ? 'yes' : 'no';
	scrollbar_str = scrollbar ? 'yes' : 'no';
	resizable_str = resizable ? 'yes' : 'no';
	window.open(url, name, 'left='+left+',top='+top+',width='+width+',height='+height+',toolbar='+toolbar_str+',menubar='+menubar_str+',status='+statusbar_str+',scrollbars='+scrollbar_str+',resizable='+resizable_str);
}

function phone_format(num) {
	num = String(num).replace(/-/g, "");
	return num.replace(/(^02.{0}|^01.{1}|[0-9]{3})([0-9]+)([0-9]{4})/,"$1-$2-$3");
}

function regno_format(num) {
	//사업자등록번호
	num = String(num).replace(/-/g, "");
	return num.replace(/([0-9]{3})([0-9]{2})([0-9]{5})/,"$1-$2-$3");
}

function onlyFloat(input) {
	//OnKeyPress="Javascript: return onlyFloat(this);"
    var chars = ".,0123456789"; //입력가능한 문자 지정
    return containsCharsOnly(input, chars);
}

function onlyEng(input) {
	//OnKeyPress="Javascript: return onlyEng(this);"
    var chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"; //입력가능한 문자 지정
    return containsCharsOnly(input, chars);
}

function onlyNum(input) {
	//OnKeyPress="Javascript: return onlyNum(this);"
    var chars = "-,0123456789"; //입력가능한 문자 지정
    return containsCharsOnly(input, chars);
}

function onlyPlusNum(input) {
	//OnKeyPress="Javascript: return onlyNum(this);"
    var chars = ",0123456789"; //입력가능한 문자 지정
    return containsCharsOnly(input, chars);
}

function onlyTelNum(input) {
	//OnKeyPress="Javascript: return onlyTelNum(this);"
    var chars = "-0123456789"; //입력가능한 문자 지정
    return containsCharsOnly(input, chars);
}

function onlyDate(input) {
	//OnKeyPress="Javascript: return onlyDate(this);"
    var chars = "-0123456789"; //입력가능한 문자 지정
    return containsCharsOnly(input, chars);
}

function containsCharsOnly(input, chars) {
    for (var inx = 0; inx <= input.value.length; inx++) {
        if (inx == 0) {//최초입력한 문자
            e = window.event;
            if (window.event) {
                key = e.keyCode;
            } else if (e) {
                key = e.which;
            } else {
                return true;
            }
            keychar = String.fromCharCode(key);
            if (chars.indexOf(keychar) == -1)// window.event 에서 받은 keychar 로 유효성 검사.
                return false;
        }
        else {//최초입력 문자가 아니면, input 의 text를 읽어서 처리한다.
            if (chars.indexOf(input.value.charAt(inx)) == -1) {
                return false;
            }
        }
    }
    return true;
}

function number_format(input) {
	//OnKeyUp="Javascript: this.value=number_format(this.value);
	input = String(input).replace(/,/g, "");
	var input = String(input);
	var reg = /(\-?\d+)(\d{3})($|\.\d+)/;
	if (reg.test(input)) {
		return input.replace(reg, function(str, p1, p2, p3) {
			return number_format(p1) + "," + p2 + "" + p3;
		});
	} else {
		return input;
	}
}

function getTextLength(s) {
	var len = 0;
	for (var i = 0; i < s.length; i++) {
		var code = s.charCodeAt(i);
		if (code <= 0x7f) {
			len += 1;
		} else if (code <= 0x7ff) {
			len += 1;
		} else if (code >= 0xd800 && code <= 0xdfff) {
			len += 1;
			i++;
		} else if (code < 0xffff) {
			len += 1;
		} else {
			len += 1;
		}
	}
	return len;
}

function getLength(s) {
	var len = 0;
	for (var i = 0; i < s.length; i++) {
		var code = s.charCodeAt(i);
		if (code <= 0x7f) {
			len += 1;
		} else if (code <= 0x7ff) {
			len += 2;
		} else if (code >= 0xd800 && code <= 0xdfff) {
			len += 2;
			i++;
		} else if (code < 0xffff) {
			len += 2;
		} else {
			len += 2;
		}
	}
	return len;
}

function showLoader() {
	jQuery('#loading-image').show();
	document.body.style.cursor = 'wait';
}

function hideLoader() {
	document.body.style.cursor = 'default';
	jQuery('#loading-image').hide();
}

function replaceAll(str, orgStr, repStr) {
	return str.split(orgStr).join(repStr);
}

function removeSpan (tableId, cellIndex){
	var table = $("#" + tableId);
	table.find("tr:not(:first)").each(function(){
		var current = $(this);
		var currentCell = current.find("td:eq(" + cellIndex + ")");
		if (currentCell.css('display')=='none') {
			currentCell.remove();
		}
	});
}

function RowSpan(tableId, cellIndex){
	//Copryright GEOMJE, http://geomje.tistory.com
	var table = $("#" + tableId);
	var prev = table.find("tr:first");
	var prevCell = prev.find("td:eq(" + cellIndex + ")");
	SetRowSpan(prevCell,1);

	table.find("tr:not(:first)").each(function(){
		var current = $(this);
		var currentCell = current.find("td:eq(" + cellIndex + ")");
		if(currentCell.html() == prevCell.html() && currentCell.html() != ''){
			var prevRowSpan = GetRowSpan(prevCell);
			SetRowSpan(prevCell,prevRowSpan + 1);
			currentCell.hide();
		} else {
			prev = current;
			prevCell = prev.find("td:eq(" + cellIndex + ")");
			SetRowSpan(prevCell,1);
			SetRowSpan(currentCell,1);
		}
	});
}

function GetRowSpan(cell){
	var prevRowSpan = cell.attr("rowSpan");
	if(cell.attr("rowSpan") == "undifined" || cell.attr("rowSpan") == window.undifined)
		prevRowSpan = cell[0].getAttribute("rowSpan");
	if(prevRowSpan == "undifined" || prevRowSpan == window.undifined)
		return 0;
	return parseInt(prevRowSpan);
}

function SetRowSpan(cell,rowSpan) {
	cell.attr("rowSpan",rowSpan);
	if(cell.attr("rowSpan") == "undifined" || cell.attr("rowSpan") == window.undifined)
		cell[0].setAttribute("rowSpan",1);
}

function LoadUserPopUp(varURL, varSubmit) {
	$('#user_pop_up').bPopup({
		content: "iframe",
		contentContainer: ".user_pop_content",
		loadUrl: varURL,
		iframeAttr: "scrolling='yes'",
		position : ['auto', 'auto'],
		modalClose: false,
		amsl : 0,
		zIndex: 900,
		onClose: function() {
			$('.user_pop_content').empty();
			if (varSubmit == "y") {
				showLoader();
				document.ffsearch.submit();
			}
		}
	});
}

function LoadUserPopUp2(varURL, varSubmit) {
	$('#user_pop_up2').bPopup({
		content: "iframe",
		contentContainer: ".user_pop_content2",
		loadUrl: varURL,
		iframeAttr: "scrolling='yes'",
		position : ['auto', 'auto'],
		modalClose: false,
		amsl : 0,
		zIndex: 1000,
		onClose: function() {
			$('.user_pop_content2').empty();
			if (varSubmit == "y") {
				showLoader();
				document.ffsearch.submit();
			}
		}
	});
}

function LoadPopUp(varURL, varSubmit) {
	$('#pop_up').bPopup({
		content: "iframe",
		contentContainer: ".pop_content",
		loadUrl: varURL,
		iframeAttr: "scrolling='yes'",
		position : ['auto', 'auto'],
		modalClose: false,
		amsl : 0,
		zIndex: 900,
		onClose: function() {
			$('.pop_content').empty();
			if (varSubmit == "y") {
				showLoader();
				document.ffsearch.submit();
			}
		}
	});
}

function LoadPopUp2(varURL, varSubmit) {
	$('#pop_up2').bPopup({
		content: "iframe",
		contentContainer: ".pop_content2",
		loadUrl: varURL,
		iframeAttr: "scrolling='yes'",
		position : ['auto', 'auto'],
		modalClose: false,
		amsl : 0,
		zIndex: 1000,
		onClose: function() {
			$('.pop_content2').empty();
			if (varSubmit == "y") {
				showLoader();
				document.ffsearch.submit();
			}
		}
	});
}

function LoadPopUp3(varURL, varSubmit) {
	$('#pop_up3').bPopup({
		content: "iframe",
		contentContainer: ".pop_content3",
		loadUrl: varURL,
		iframeAttr: "scrolling='yes'",
		position : ['auto', 'auto'],
		modalClose: false,
		amsl : 0,
		zIndex: 1000,
		onClose: function() {
			$('.pop_content3').empty();
			if (varSubmit == "y") {
				showLoader();
				document.ffsearch.submit();
			}
		}
	});
}

function validateFloat(value, digit) {
	if (digit == "2") {
		var filter = /^[0-9]{1,3}[.]{0,1}[0-9]{0,2}$/;
	} else {
		var filter = /^[0-9]{1,3}[.]{0,1}[0-9]{0,1}$/;
	}
	if(filter.test(value)){
		return true;
	} else {
		return false;
	}
 }

function validateEmail(StrID, mOpt, mMsg) {
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var filter = /^\s*(([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5}){1,25})+([;.](([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5}){1,25})+)*\s*$/;
	if (filter.test(a) || (a == "" && mOpt == "N")) {
		return true;
	} else {
		alert(mMsg);
		$("#"+StrID).focus();
		return false;
	}
}

function validateInput(StrID, mOpt, mMsg) {
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	if (a != "" || (a == "" && mOpt == "N")) {
		return true;
	} else {
		alert(mMsg);
		$("#"+StrID).focus();
		return false;
	}
}

function validateInputEtc(StrID, mValue, mOpt, mMsg) {
	var a = $("#"+StrID).val();
	var b = $("#"+StrID+"_etc").val();
	a = jQuery.trim(a);
	b = jQuery.trim(b);
	if (mOpt == "N") {
		return true;
	} else {
		if (a == mValue && b == "") {
			alert(mMsg);
			$("#"+StrID+"_etc").focus();
			return false;
		} else {
			return true;
		}
	}
}

function validateDate(StrID, mOpt, mMsg) {
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var filter = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/;
	if (filter.test(a) || (a == "" && mOpt == "N")) {
		if (a != "") {
			var ds = a.split('-');
			var d = new Date(ds[0], parseInt(ds[1])-1, parseInt(ds[2]));
			if (!!(d && (d.getMonth() + 1) == parseInt(ds[1]) && d.getDate() == parseInt(ds[2])) == true) {
				return true;
			} else {
				alert(mMsg);
				setTimeout(function(){$("#"+StrID).focus();}, 1);
				return false;
			}
		} else {
			return true;
		}
	} else {
		alert(mMsg);
		setTimeout(function(){$("#"+StrID).focus();}, 1);
		return false;
	}
}

function validateYear(StrID, mOpt, mMsg) {
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var filter = /^[0-9]{4}$/;
	if (filter.test(a) || (a == "" && mOpt == "N")) {
		return true;
	} else {
		alert(mMsg);
		setTimeout(function(){$("#"+StrID).focus();}, 1);
		return false;
	}
}

function validateNumber(StrID, mOpt, mMsg) {
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var filter = /^([0-9]|[,\-])*$/;
	if (filter.test(a) || (a == "" && mOpt == "N")) {
		return true;
	} else {
		alert(mMsg);
		setTimeout(function(){$("#"+StrID).focus();}, 1);
		return false;
	}
}

function validateContact(StrID, mOpt, mMsg) {
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var filter = /^[0-9]{2,3}-[0-9]{2,4}-[0-9]{4}$/;
	if (filter.test(a) || ((a == "--" || a == "") && mOpt == "N")) {
		return true;
	} else{
		alert(mMsg);
		$("#"+StrID).focus();
		return false;
	}
}

function validateMobile(StrID, mOpt, mMsg) {
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var filter = /^[0-9]{3}-[0-9]{3,4}-[0-9]{4}$/;
	if (filter.test(a) || ((a == "--" || a == "") && mOpt == "N")) {
		return true;
	} else{
		alert(mMsg);
		$("#"+StrID).focus();
		return false;
	}
}

function validateZip(StrID, mOpt, mMsg) {
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var filter = /^[0-9]{5}$/;
	if (filter.test(a) || ((a == "--" || a == "") && mOpt == "N")) {
		return true;
	} else{
		alert(mMsg);
		$("#"+StrID).focus();
		return false;
	}
}


function validateRegNo(StrID, mOpt, mMsg) {
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var filter = /^[0-9]{3}-[0-9]{2}-[0-9]{5}$/;
	if (filter.test(a) || ((a == "--" || a == "") && mOpt == "N")) {
		return true;
	} else{
		alert(mMsg);
		$("#"+StrID).focus();
		return false;
	}
}

function FileUploadCheck(mLang, StrID, mOpt, mCnt, mType, sizeLimit) {
	var errCheck = "s";

	if (mType == "image" || mType == "photo") {
		var filterStr = new Array("jpg","jpeg","gif","png");
	} else if (mType == "userphoto") {
		var filterStr = new Array("jpg","jpeg");
	} else if (mType == "pdf") {
		var filterStr = new Array("pdf");
	} else if (mType == "imagepdf") {
		var filterStr = new Array("jpg", "jpeg", "pdf");
	} else if (mType == "hwp") {
		var filterStr = new Array("hwp", "hwpx");
	} else if (mType == "xlsx") {
		var filterStr = new Array("xlsx");
	} else if (mType == "request") {
		var filterStr = new Array("hwp","hwpx","doc","docx","ppt","pptx","xls","xlsx","jpg","jpeg","gif","png","pdf","zip","mp4","avi");
	} else {
		var filterStr = new Array("ai","psd","hwp","hwpx","dwg","doc","docx","ppt","pptx","xls","xlsx","jpg","jpeg","gif","png","zip","alz","rar","bmp","avi","wmv","mp3","mdb","mov","mdbx","mpeg","mpg","wav","vsd","txt","pdf");
	}

	if (parseInt(mCnt) > 1) {
		for (idx=1; idx <= 5 ; idx++) {
			var fileformname = StrID + idx;
			var filename = '#' + StrID + idx;
			var a = $(filename).val();
			a = jQuery.trim(a);
			if (a != "") {
				var filetype = a.substring(a.lastIndexOf(".")+1);
				errCheck = "y";
				filetype = filetype.toLowerCase();
				for (i=0; i < filterStr.length ; i++ ) {
					if (filetype == filterStr[i]) {
						errCheck = "n";
					}
				}
				if (errCheck == "y") {
					if (mLang == "en") {
						alert(filetype + " is not available for uploading");
					} else if (mLang == "cn") {
						alert("不能上传" + filetype + "文件");
					} else if (mLang == "jp") {
						alert(filetype + "ファイルはアップロードできません。");
					} else {
						alert(filetype + "은 업로드할 수 없습니다");
					}
					$(filename).focus();
					return false;
				}
				if (typeof($(filename)[0].files) == "undefined" || $(filename)[0].files == "null") {
				} else {
					var fileSize = $(filename)[0].files[0].size;
					if (parseInt(fileSize) > parseInt(sizeLimit)) {
						errCheck = "y";
						if (mLang == "en") {
							alert('Please check file size');
						} else if (mLang == "cn") {
							alert("超过文件容量");
						} else if (mLang == "jp") {
							alert("ファイルのサイズが最大値を超えています。");
						} else {
							alert("업로드 최대 용량을 초과했습니다.");
						}
						$(filename).focus();
						return false;
					}
				}
			}
		}
	} else {
		var fileformname = StrID;
		var filename = '#' + StrID;
		var a = $(filename).val();
		a = jQuery.trim(a);
		if (a != "") {
			var filetype = a.substring(a.lastIndexOf(".")+1);
			errCheck = "y";
			filetype = filetype.toLowerCase();
			for (i=0; i < filterStr.length ; i++ ) {
				if (filetype == filterStr[i]) {
					errCheck = "n";
				}
			}
			if (errCheck == "y") {
				if (mLang == "en") {
					alert(filetype + " is not available for uploading");
				} else if (mLang == "cn") {
					alert("不能上传" + filetype + "文件");
				} else if (mLang == "jp") {
					alert(filetype + "ファイルはアップロードできません。");
				} else {
					alert(filetype + "은 업로드할 수 없습니다");
				}
				$(filename).focus();
				return false;
			}
			if (typeof($(filename)[0].files) == "undefined" || $(filename)[0].files == "null") {
			} else {
				var fileSize = $(filename)[0].files[0].size;
				if (parseInt(fileSize) > parseInt(sizeLimit)) {
					errCheck = "y";
					if (mLang == "en") {
						alert('Please check file size');
					} else if (mLang == "cn") {
						alert("超过文件容量");
					} else if (mLang == "jp") {
						alert("ファイルのサイズが最大値を超えています。");
					} else {
						alert("업로드 최대 용량을 초과했습니다.");
					}
					$(filename).focus();
					return false;
				}
			}
		} else {
			if (mType == "userphoto") {
				var b = $("#aPhotoName").val();
			} else {
				var b = "N";
			}
			if (mOpt == "Y" && b != "Y") {
				errCheck = "y";
				if (mLang == "en") {
					alert("Please select file");
				} else if (mLang == "cn") {
					alert("请选择文件");
				} else if (mLang == "jp") {
					alert("ファイルを選択ください。");
				} else {
					alert("파일을 선택하세요");
				}
				$("#"+StrID).focus();
				return false;
			} else {
				errCheck = "n";
			}
		}
	}
	if (errCheck == "y") {
		return false;
	} else {
		return true;
	}
}

function validatePassword(StrID, mOpt, mMsg){
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var filter = /^(?=.*?[A-Za-z])(?=.*?[0-9])(?=.*?[`~\!@#\$%\^\&\*\(\)_\+\-=\{\}\[\]\|\\:";'\<>\?,\./]).{9,15}$/;
	if (filter.test(a) || (a == "" && mOpt == "N")) {
		return true;
	} else{
		alert(mMsg);
		$("#"+StrID).focus();
		return false;
	}
}

function validatePassword2(StrID, mOpt, mMsg){
	var a = $("#"+StrID).val();
	var b = $("#"+StrID+"2").val();
	a = jQuery.trim(a);
	b = jQuery.trim(b);
	if ((a != "" || b != "") && a != b) {
		alert(mMsg)
		$("#"+StrID+"2").focus();
		return false;
	} else{
		return true;
	}
}

function validateUserID(StrID, mOpt, mMsg){
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var filter = /^[a-zA-Z0-9]{7,15}$/;
	if (filter.test(a) || (a == "" && mOpt == "N")) {
		return true;
	} else {
		alert(mMsg);
		$("#"+StrID).focus();
		return false;
	}
}

function validateCode(StrID, mOpt, mMsg){
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var filter = /^[A-Z0-9]{1,15}$/;
	if (filter.test(a) || (a == "" && mOpt == "N")) {
		return true;
	} else {
		alert(mMsg);
		$("#"+StrID).focus();
		return false;
	}
}

function validateAgree(StrID, mMsg) {
	var a = $("input:radio[name="+StrID+"]:checked").val();
	if (a != "Y") {
		alert(mMsg);
		$("input:radio[name='"+StrID+"']").first().focus();
		return false;
	} else {
		return true;
	}
}

function validateSelect(StrID, mOpt, mMsg){
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	if (a.length < 1 && mOpt == "Y") {
		alert(mMsg);
		$("#"+StrID).focus();
		return false;
	} else{
		return true;
	}
}

function validateRadio(StrID, mOpt, mMsg){
	var a = $("input:radio[name='"+StrID+"']:checked").val();
	if ((a == "" || typeof a == "undefined") && mOpt == "Y") {
		alert(mMsg);
		$("input:radio[name='"+StrID+"']").first().focus();
		return false;
	} else{
		return true;
	}
}

function validateRadioEtc(StrID, mValue, mOpt, mMsg){
	var a = $("input:radio[name='"+StrID+"']:checked").val();
	a = jQuery.trim(a);
	var b = $("#"+StrID+"_etc").val();
	b = jQuery.trim(b);

	if (mOpt == "N") {
		return true;
	} else {
		if (a == mValue && b == "") {
			alert(mMsg);
			$("#"+StrID+"_etc").focus();
			return false;
		} else {
			return true;
		}
	}
}

function validateCheckBox(StrID, mOpt, mMsg){
	var a;
	a = "";
	$("input:checkbox[name='"+StrID+"[]']:checked").each(function() {
		a = a + $(this).val();
	});

	if ((a == "" || typeof a == "undefined") && mOpt == "Y") {
		alert(mMsg);
		$("input:checkbox[name='"+StrID+"[]']").first().focus();
		return false;
	} else {
		return true;
	}
}

function validateCheckBoxEtc(StrID, mValue, mOpt, mMsg) {
	var a;
	a = "";
	var b = $("#"+StrID+"_etc").val();
	b = jQuery.trim(b);
	var chk;
	chk = "N";

	$("input:checkbox[name='"+StrID+"[]']:checked").each(function() {
		a = $(this).val();
		if (a == mValue) {
			chk = "Y";
		}
	});

	if (mOpt == "N") {
		return true;
	} else {
		if (chk == "Y" && b == "") {
			alert(mMsg);
			$("#"+StrID+"_etc").focus();
			return false;
		} else {
			return true;
		}
	}
}

function validateTime(StrIDFrom, StrIDTo, sOpt, sMsg) {
	var a = $("#"+StrIDFrom).val();
	a = jQuery.trim(a);
	var b = $("#"+StrIDTo).val();
	b = jQuery.trim(b);
	if (a == "" && b== "" && sOpt == "N") {
		return true;
	} else {
		if (a < b) {
			return true;
		} else {
			alert(sMsg);
			$("#"+StrIDTo).focus();
			return false;
		}
	}
}

function validatePeriod(StrIDFrom, StrIDTo, sOpt, sMsg) {
	var a = $("#"+StrIDFrom).val();
	a = jQuery.trim(a);
	var b = $("#"+StrIDTo).val();
	b = jQuery.trim(b);
	if ($("#"+StrIDFrom).is(':disabled') == false && $("#"+StrIDTo).is(':disabled') == false) {
		if (a == "" && b== "" && sOpt == "N") {
			return true;
		} else {
			if (a <= b) {
				if (validateDate(StrIDFrom, "Y", sMsg) && validateDate(StrIDTo, "Y", sMsg)) {
					return true;
				}
			} else {
				alert(sMsg);
				$("#"+StrIDTo).focus();
				return false;
			}
		}
	} else {
		return true;
	}
}

function validatePeriodB(StrID, StrIDFrom, StrIDTo, sOpt, sMsg) {
	//날짜 시작시간 종료시간
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var b = $("#"+StrIDFrom).val();
	b = jQuery.trim(b);
	var c = $("#"+StrIDTo).val();
	c = jQuery.trim(c);
	if ($("#"+StrID).is(':disabled') == false && $("#"+StrIDFrom).is(':disabled') == false && $("#"+StrIDTo).is(':disabled') == false) {
		if (a == "" && b== "" && c == "" && sOpt == "N") {
			return true;
		} else {
			if (validateDate(StrID, "Y", sMsg)) {
				if (b != "" && c != "" && b <= c) {
					return true;
				} else {
					alert(sMsg);
					$("#"+StrIDTo).focus();
					return false;
				}
			} else {
				return false;
			}
		}
	} else {
		return true;
	}
}

function validatePeriodC(StrIDFrom, StrTimeFrom, StrIDTo, StrTimeTo, sOpt, sMsg) {
	//시작 날짜 시작시간 종료날짜 종료시간
	var a = $("#"+StrIDFrom).val();
	a = jQuery.trim(a);
	var b = $("#"+StrIDTo).val();
	b = jQuery.trim(b);
	var c = $("#"+StrTimeFrom).val();
	c = jQuery.trim(c);
	var d = $("#"+StrTimeTo).val();
	d = jQuery.trim(d);
	if ($("#"+StrIDFrom).is(':disabled') == false && $("#"+StrIDTo).is(':disabled') == false && $("#"+StrTimeFrom).is(':disabled') == false && $("#"+StrTimeTo).is(':disabled') == false) {
		if (a == "" && b== "" && c== "" && d== "" && sOpt == "N") {
			return true;
		} else {
			if (a <= b) {
				if (validateDate(StrIDFrom, "Y", sMsg) && validateDate(StrIDTo, "Y", sMsg)) {
					if (c != "" && d != "") {
						if (a == b) {
							if (c <= d) {
								return true;
							} else {
								alert(sMsg);
								$("#"+StrIDTo).focus();
								return false;
							}
						} else {
							return true;
						}
					} else {
						alert(sMsg);
						$("#"+StrIDTo).focus();
						return false;
					}
				}
			} else {
				alert(sMsg);
				$("#"+StrIDTo).focus();
				return false;
			}
		}
	} else {
		return true;
	}
}

function validatePeriod2(StrID, StrID2, sOpt, sMsg) {
	var a = $("#"+StrID).val();
	a = jQuery.trim(a);
	var b = $("#"+StrID2).val();
	b = jQuery.trim(b);
	if ($("#"+StrID).is(':disabled') == false && $("#"+StrID2).is(':disabled') == false) {
		if (a == "" && b== "" && sOpt == "N") {
			return true;
		} else {
			if (a <= b) {
				if (validateDate(StrID, "Y", sMsg) && validateDate(StrID2, "Y", sMsg)) {
					return true;
				}
			} else {
				alert(sMsg);
				$("#"+StrID2).focus();
				return false;
			}
		}
	} else {
		return true;
	}
}

function validateAmount(StrID, StrID2, sOpt, sMsg) {
	var a = parseInt($("#"+StrID).val().replace(/,/g, ""));
	if (isNaN(a)) {
		a = 0;
	}
	var b = parseInt($("#"+StrID2).val().replace(/,/g, ""));
	if (isNaN(b)) {
		b = 0;
	}
	if (a < b) {
		alert(sMsg);
		$("#"+StrID2).focus();
		return false;
	} else {
		return true;
	}
}

function closePop() {
	if (typeof(parent.document.getElementById('b-close3')) != 'undefined' && parent.document.getElementById('b-close3') != null) {
		window.parent.$("#b-close3").click();
		window.parent.$("#b-close2").click();
		window.parent.$("#b-close").click();
	} else if (typeof(parent.document.getElementById('b-close2')) != 'undefined' && parent.document.getElementById('b-close2') != null) {
		window.parent.$("#b-close2").click();
		window.parent.$("#b-close").click();
	} else if (typeof(parent.document.getElementById('b-close')) != 'undefined' && parent.document.getElementById('b-close') != null) {
		window.parent.$("#b-close").click();
	} else {
		window.close();
	}
}


function fnDateAdd(val,dateType,iNum) {
    var _strDate = null;
    var parts = val.split('-');
    var iYar = Number(parts[0]);
    var iMonth = Number(parts[1]) - 1;
    var iDay = Number(parts[2]);
    switch (dateType) {
        case "y":
            iYar = iYar + iNum;
            break;
        case "m":
            iMonth = iMonth + iNum;
            break;
        case "d":
            iDay = iDay + iNum;
            break;
        default:
    }
    var now = new Date(iYar, iMonth, iDay);
    var year = now.getFullYear();
    var mon = (now.getMonth() + 1) > 9 ? '' + (now.getMonth() + 1) : '0' + (now.getMonth() + 1);
    var day = now.getDate() > 9 ? '' + now.getDate() : '0' + now.getDate();
    return String.format("{0}-{1}-{2}", year, mon, day);
}

String.format = function () {
    var s = arguments[0];
    for (var i = 0; i < arguments.length - 1; i++) {
        var reg = new RegExp("\\{" + i + "\\}", "gm");
        s = s.replace(reg, arguments[i + 1]);
    }
    return s;
}

String.nowDate = function () {
    var now = new Date();
    var year = now.getFullYear();
    var mon = (now.getMonth() + 1) > 9 ? '' + (now.getMonth() + 1) : '0' + (now.getMonth() + 1);
    var day = now.getDate() > 9 ? '' + now.getDate() : '0' + now.getDate();
    return String.format("{0}-{1}-{2}", year, mon, day);
}

function formatDate(date) {
	var d = new Date(date),
	month = '' + (d.getMonth() + 1),
	day = '' + d.getDate(),
	year = d.getFullYear();
	if (month.length < 2) month = '0' + month;
	if (day.length < 2) day = '0' + day;
	return year + month + day;
}

function dateDiff(_date1, _date2) {
    var diffDate_1 = _date1 instanceof Date ? _date1 : new Date(_date1);
    var diffDate_2 = _date2 instanceof Date ? _date2 : new Date(_date2);

	diffDate_1 = new Date(diffDate_1.getFullYear(), diffDate_1.getMonth()+1, diffDate_1.getDate());
	diffDate_2 = new Date(diffDate_2.getFullYear(), diffDate_2.getMonth()+1, diffDate_2.getDate());

	var diff = Math.abs(diffDate_2.getTime() - diffDate_1.getTime());
    diff = Math.ceil(diff / (1000 * 3600 * 24)) + 1;

    return diff;
}

function formatTime(date) {
	var d = new Date(date);
	var hour = '' + d.getHours();
	var minute = '' + d.getMinutes();
	if (hour.length < 2) hour = '0' + hour;
	if (minute.length < 2) minute = '0' + minute;
	return hour + minute;
}