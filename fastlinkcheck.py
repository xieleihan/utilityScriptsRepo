import requests
import os
import sys
import json

from dotenv import load_dotenv

load_dotenv()

useremail = os.getenv("USEREMAIL")
login_url = os.getenv("LOGIN_URL")
checkout_url = os.getenv("CHECKOUT_URL")
logout_url = os.getenv("LOGOUT_URL")
password = os.getenv("PASSWORD")
ikuuu_password = os.getenv("IKUUU_PASSWORD")
ikuuu_login_url = os.getenv("IKUUU_LOGIN_URL")
ikuuu_checkout_url = os.getenv("IKUUU_CHECKOUT_URL")
ikuuu_logout_url = os.getenv("IKUUU_LOGOUT_URL")

# 模拟真实用户
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

session = requests.Session()
login_data = {
    "email": useremail ,
    "passwd": password,
    "code":''
}

response = session.post(
    login_url,
    json=login_data,
    headers=headers,
    allow_redirects=True,
    # verify=False  # 仅用于测试，生产环境建议使用真实证书
)

print("Fastlink登录响应状态码:", response.status_code)
if response.status_code == 200:
    print("Fastlink登录成功😊")
    try:
        data = session.cookies.get_dict()
        resp_checkin = session.post(checkout_url,
                                    headers={'User-Agent': headers['User-Agent'], 'Accept': headers['Accept']})
        parsed = json.loads(resp_checkin.text)
        if parsed.get("ret") == 1:
            print("✅ Fastlink签到成功:", parsed.get("msg"))
        else:
            print("❌ Fastlink签到失败:", parsed.get("msg"))
        print("Fastlink运行退出登录")
        try:
            resp_logout = session.post(logout_url,
                                       headers={'User-Agent': headers['User-Agent'], 'Accept': headers['Accept']})
            print("Fastlink退出登录了")
        except Exception as e:
            print("退出登录请求失败:", str(e))


    except requests.exceptions.JSONDecodeError:
        sys.exit(1)
else:
    sys.exit(1)

session_1 = requests.Session()
login_data = {
    "host": 'ikuuu.org',
    "email": useremail ,
    "passwd": ikuuu_password,
    "code":''
}

response_1 = session_1.post(
    ikuuu_login_url,
    json=login_data,
    headers=headers,
    allow_redirects=True,
    # verify=False  # 仅用于测试，生产环境建议使用真实证书
)

print("Ikuuu登录响应状态码:", response_1.status_code)
if response_1.status_code == 200:
    print("Ikuuu登录成功😊")
    try:
        data = session_1.cookies.get_dict()
        resp_checkin = session_1.post(ikuuu_checkout_url,
                                    headers={'User-Agent': headers['User-Agent'], 'Accept': headers['Accept']})
        parsed = json.loads(resp_checkin.text)
        if parsed.get("ret") == 1:
            print("✅ Ikuuu签到成功:", parsed.get("msg"))
        else:
            print("❌ Ikuuu签到失败:", parsed.get("msg"))
        print("Ikuuu运行退出登录")
        try:
            resp_logout = session_1.post(ikuuu_logout_url,
                                       headers={'User-Agent': headers['User-Agent'], 'Accept': headers['Accept']})
            print("Ikuuu退出登录了")
        except Exception as e:
            print("退出登录请求失败:", str(e))


    except requests.exceptions.JSONDecodeError:
        sys.exit(1)
