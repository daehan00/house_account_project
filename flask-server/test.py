from flask import flash, redirect, request, session, url_for
from utils import api_ra_list_post
import os
import requests
import json

ra_data = {
    "authority": False,
    "division_num": None,
    "email_address": "pzr2001@naver.com",
    "house_name": "AVISON",
    "semester": False,
    "user_id": 2022124082,
    "user_name": "박지영",
    "user_num": "010-4359-9993",
    "year": 2024
}
code, response_text = api_ra_list_post(ra_data)

# 결과 처리 예시
print(f"Status Code: {code}")
print(f"Response: {response_text}")