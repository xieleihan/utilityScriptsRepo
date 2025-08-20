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
PLATFORM_BASE_API_REMOVE= 'http://platform.echoing.cc/api/v1/ctrlTaskMng/remove'
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
def found(exceptionType,isopen,cid):
    #带时间 true
    obj = {
    "pageNum": 1,
    "pageSize": 500,
    "taskStatus": 4, #任务状态
    "exceptionType": exceptionType, # 异常类型 3为控件找不到 1是未知 67是网络不通 59是获取验证码异常 31是邮箱地址变更异常
    "creatTime": [
        taskCreateStartTime,
        taskCreateStartTime
    ],
    "taskCreateStartTime": taskCreateStartTime,
    "taskCreateEndTime": taskCreateEndTime,
    "platform": "1"
}
    # 不带时间 false
    noobj = {
    "pageNum": 1,
    "pageSize": 500,
    "eventType": exceptionType, # 异常类型 3为控件找不到 1是未知 67是网络不通 59是获取验证码异常
    "platform": "1",
    "cid": cid
}
    if isopen:
        # print(obj, "这是带时间的参数")
        return obj
    else:
        # print(noobj, "这是不带时间的参数")
        return noobj

# 发起请求获取数据
session = requests.Session()
session.headers.update(BASE_HEADERS)

def getTheVerificationCode(input_str: str = "") -> list[Any]:
    try:
        response = session.post(PLATFORM_BASE_API_ALL, json=found(59,True,0), timeout=10)
        if response.status_code == 200:
            data = response.json()

            # 确保路径存在且为列表
            if 'data' in data and isinstance(data['data'], dict):
                outer_data = data['data'].get('data', [])
                # print("提取的原始数据:", outer_data)

                if isinstance(outer_data, list):
                    task_ids = []

                    for item in outer_data:
                        if isinstance(item, dict) and 'detail' in item:
                            detail_dict = item['detail']

                            if isinstance(detail_dict, dict):
                                task_id = detail_dict.get('serial')
                                if task_id and task_id not in task_ids:
                                    task_ids.append(task_id)
                    print("提取的任务ID:", task_ids)
                    return task_ids
                else:
                    print("data['data']['data'] 不是列表")
            else:
                print("没有找到有效的数据")

        else:
            print("请求失败，状态码:", response.status_code)

        return []  # 默认返回空列表

    except requests.RequestException as e:
        print("请求异常:", e)
        return []

def getHaveYouChangedYourEmailAddress(task_id: Any) -> bool:
    try:
        response = session.post(PLATFORM_BASE_API_ALL, json=found(31, False, task_id), timeout=100)
        if response.status_code == 200:
            data = response.json()
            # 取外层 data.data 列表
            outer_data = data.get("data", {}).get("data", [])
            # print(response.json(),"这是外层 data.data 的数据")
            if isinstance(outer_data, list) and outer_data:
                first_item = outer_data[0]
                if isinstance(first_item, dict):
                    task_status = first_item.get("taskStatus")
                    # print("task_id:", task_id, "task_status:", task_status)
                    return task_status == 4
            # 列表为空或格式不对
            return True
        else:
            print("请求失败，状态码:", response.status_code)
            return False
    except requests.RequestException as e:
        print("请求异常:", e)
        return False

task_ids = getTheVerificationCode()  # 获取数组
print("-------------------------",task_ids)
istask_ids: List[bool] = []

for task_id in task_ids:
    result = getHaveYouChangedYourEmailAddress(task_id)
    istask_ids.append(result)

print("最终任务状态数组:", istask_ids)

# 将数组结果转换为对象格式 {task_id: status}
result_dict: Dict[str, bool] = {}
for i, task_id in enumerate(task_ids):
    result_dict[task_id] = istask_ids[i]

print("最终任务状态对象:", result_dict)


def load_data():
    try:
        response = session.post(PLATFORM_BASE_API_ALL, json=found(59, True, 0), timeout=10)
        if response.status_code == 200:
            data = response.json()

            # 确保路径存在且为列表
            if 'data' in data and isinstance(data['data'], dict):
                outer_data = data['data'].get('data', [])

                # 存储符合条件的taskId
                task_ids = []

                # 遍历返回的数据
                for item in outer_data:
                    if isinstance(item, dict):
                        # 从detail中获取serial（任务ID）
                        detail = item.get('detail', {})
                        if isinstance(detail, dict):
                            serial = detail.get('serial')

                            # 检查这个serial在最终任务状态对象中是否存在且为True
                            if serial and serial in result_dict and result_dict[serial] is True:
                                # 获取taskId
                                task_id = detail.get('taskId')
                                if task_id:
                                    task_ids.append(task_id)

                print("符合条件的taskId数组:", task_ids)
                return task_ids
            else:
                print("没有找到有效的数据")
        else:
            print("请求失败，状态码:", response.status_code)

        return []  # 默认返回空列表

    except requests.RequestException as e:
        print("请求异常:", e)
        return []

load = load_data() #拿到需要删除的taskId

def removeData(task_ids: List[int]):
    if not task_ids:
        print("没有任务ID需要删除")
        return

    try:
        response = session.post(PLATFORM_BASE_API_REMOVE, json=task_ids, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") is True:
                print("✅ 成功删除任务ID:", task_ids)
            else:
                print("❌ 删除任务失败:", data.get("msg", "未知错误"))
        else:
            print("请求失败，状态码:", response.status_code)
    except requests.RequestException as e:
        print("请求异常:", e)

removeData(load) #删除任务