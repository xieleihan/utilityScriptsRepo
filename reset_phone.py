from typing import Any, List, Dict

import requests
import os
import sys

from dotenv import load_dotenv
from datetime import datetime, date, timedelta

load_dotenv()

# 参数信息
login_url = os.getenv("LOGIN_URL")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
login_type = int(os.getenv("LOGIN_TYPE", "2"))

# 模拟真实用户
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

session = requests.Session()
login_data = {
    "userName": username,
    "password": password,
    "loginType": login_type
}

response = session.post(
    login_url,
    json=login_data,
    headers=headers,
    allow_redirects=True,
    verify=False  # 仅用于测试，生产环境建议使用真实证书
)

# 获取关键token
if response.status_code == 200:
    try:
        json_response = response.json()
        if json_response.get("success") is True:
            data = json_response.get("data", {})
            token = data.get("token") if isinstance(data, dict) else None

            if token:
                ACCESS_TOKEN = token
                print("🔑 成功获取 Token:", ACCESS_TOKEN)
            else:
                sys.exit(1)
        else:
            msg = json_response.get("msg", "未知错误")
            trace_id = json_response.get("traceId", "无追踪ID")
            sys.exit(1)

    except requests.exceptions.JSONDecodeError:
        sys.exit(1)
else:
    sys.exit(1)

# 获取header头
BASE_HEADERS = { 'Accept': 'application/json, text/plain, */*', 'Accept-Language': 'zh_CN', 'Cache-Control': 'no-cache',
                 'Content-Type': 'application/json', 'Origin': 'http://platform.localtest.echoing.cc:61002', 'Pragma': 'no-cache',
                 'Proxy-Connection': 'keep-alive', 'Referer': 'http://platform.localtest.echoing.cc:61002/cloudMachine/loggerList',
                 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                 'accessToken': ACCESS_TOKEN }

# 定义接口
# http://platform.echoing.cc/api/v1/ctrlTaskMng/page
PLATFORM_BASE_API_ALL = 'http://platform.echoing.cc/api/v1/ctrlTaskMng/page'
PLATFORM_BASE_API_RESET = 'http://platform.echoing.cc/api/v1/cloudDevice/reboot'
# Default time range (can be overridden if needed)
now = datetime.now()
print('当前时间:', now)

# 获取今天的 00:00:00
today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

# 昨天的 00:00:00
yesterday_midnight = today_midnight - timedelta(days=1)

# 设置任务时间范围
taskCreateStartTime = yesterday_midnight.strftime("%Y-%m-%d %H:%M:%S")
taskCreateEndTime = today_midnight.strftime("%Y-%m-%d %H:%M:%S")

# 任务查询参数
def found():
    return {
        "taskStatus": 1,
        "pageNum": 1,
        "pageSize": 500,
        "taskCreateStartTime": taskCreateStartTime,
        "taskCreateEndTime": taskCreateEndTime,
    }

# 发起请求获取数据
session = requests.Session()
session.headers.update(BASE_HEADERS)

def getDelayTask():
    response = session.post(PLATFORM_BASE_API_ALL, json=found())
    if response.status_code == 200:
        try:
            json_response = response.json()
            if json_response.get("success") is True:
                data = json_response.get("data", [])
                # 如果 data 是列表，遍历提取 cid
                items = data.get("data", [])  # 默认空列表，防止 key 不存在

                if isinstance(items, list):
                    records = [item["cid"] for item in items if isinstance(item, dict) and "cid" in item]
                else:
                    records = []
                print(records, len(records))
                return records
            else:
                msg = json_response.get("msg", "未知错误")
                trace_id = json_response.get("traceId", "无追踪ID")
                sys.exit(1)

        except requests.exceptions.JSONDecodeError:
            sys.exit(1)
    else:
        sys.exit(1)

def resetPhone(arr):
    response =session.post(PLATFORM_BASE_API_RESET, json={"snList": arr})
    print(response)
    if response.status_code == 200:
        try:
            json_response = response.json()

            if json_response.get("success") is True:
                print("重置成功:", json_response)
            else:
                print("重置失败:", json_response)
                sys.exit(1)

        except requests.exceptions.JSONDecodeError:
            sys.exit(1)
    else:
        sys.exit(1)

resetPhone(getDelayTask())