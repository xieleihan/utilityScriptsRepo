from typing import Any, List, Dict, Optional
import logging
import requests
import os
import sys
try:
    from urllib3.exceptions import InsecureRequestWarning
    import urllib3
    urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    pass

from dotenv import load_dotenv
from datetime import datetime, date, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# 参数信息
login_url = os.getenv("LOGIN_URL")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
login_type = int(os.getenv("LOGIN_TYPE", "2"))

# 参数验证
if not all([login_url, username, password]):
    logger.error("缺少必需的环境变量：LOGIN_URL, USERNAME, PASSWORD")
    sys.exit(1)

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
    verify=False,  # 仅用于测试，生产环境建议使用真实证书
    timeout=10
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
                logger.info("✅ 成功获取 Token")
            else:
                logger.error("❌ 响应中未找到 token")
                sys.exit(1)
        else:
            msg = json_response.get("msg", "未知错误")
            trace_id = json_response.get("traceId", "无追踪ID")
            logger.error(f"❌ 登录失败：{msg}（TraceID: {trace_id}）")
            sys.exit(1)

    except requests.exceptions.JSONDecodeError:
        logger.error("❌ 响应格式不是有效的 JSON")
        sys.exit(1)
else:
    logger.error(f"❌ 登录请求失败：HTTP {response.status_code}")
    sys.exit(1)

# 获取header头
BASE_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh_CN',
    'Cache-Control': 'no-cache',
    'Content-Type': 'application/json',
    'Origin': 'https://platform.emmasai.com',
    'Pragma': 'no-cache',
    'Proxy-Connection': 'keep-alive',
    'Referer': 'https://platform.emmasai.com/cloudMachine/loggerList',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'accessToken': ACCESS_TOKEN
}

# 定义接口
PLATFORM_BASE_API_ALL = 'https://platform.emmasai.com/api/v1/ctrlTaskMng/page'
PLATFORM_BASE_API_REMOVE = 'http://platform.echoing.cc/api/v1/ctrlTaskMng/remove'
PLATFORM_BASE_API_START = 'https://platform.emmasai.com/api/v1/ctrlTaskMng/taskRetry'

# 设置任务时间范围
now = datetime.now()
logger.info(f'当前时间: {now}')

# 获取今天的 00:00:00
today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

# 昨天的 00:00:00
yesterday_midnight = today_midnight - timedelta(days=1)

# 时间范围
taskCreateStartTime = yesterday_midnight.strftime("%Y-%m-%d %H:%M:%S")
taskCreateEndTime = now.strftime("%Y-%m-%d %H:%M:%S")

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
    "pageSize": 1000,
    "exceptionType": exceptionType, # 异常类型 3为控件找不到 1是未知 67是网络不通 59是获取验证码异常 64账号登出
    "platform": "7",
}
    if isopen:
        # print(obj, "这是带时间的参数")
        return obj
    else:
        print(noobj, "这是不带时间的参数")
        return noobj

# 发起请求获取数据
session = requests.Session()
session.headers.update(BASE_HEADERS)

def getTheVerificationCode(input_str: str = "") -> List[str]:
    """获取验证码异常的账号列表
    
    Returns:
        包含账号的列表
    """
    logger.info("🔍 开始获取验证码异常的账号列表")
    try:
        response = session.post(
            PLATFORM_BASE_API_ALL, 
            json=found(64, False, 0), 
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"❌ 请求失败，状态码: {response.status_code}")
            return []
        
        data = response.json()
        logger.debug(f"📦 返回的原始数据: {data}")
        
        # 确保路径存在且为列表
        if 'data' not in data or not isinstance(data['data'], dict):
            logger.warning("⚠️  没有找到有效的数据")
            return []
        
        outer_data = data['data'].get('data', [])
        
        if not isinstance(outer_data, list):
            logger.warning(f"⚠️  数据格式错误，期望列表，收到: {type(outer_data)}")
            return []
        
        logger.info(f"📋 获取到 {len(outer_data)} 条原始数据")
        
        # 提取 account 字段
        accounts = []
        for item in outer_data:
            if isinstance(item, dict) and 'account' in item:
                account = item['account']
                if account:  # 过滤掉空值
                    accounts.append(account)
                    logger.debug(f"✅ 提取账号: {account}")
            else:
                logger.debug(f"⚠️  项目缺少 'account' 字段或不是字典: {item}")
        
        logger.info(f"✅ 成功提取 {len(accounts)} 个账号")
        logger.debug(f"📝 账号列表: {accounts}")
        
        return accounts

    except requests.exceptions.Timeout:
        logger.error("❌ 请求超时")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("❌ 连接错误")
        return []
    except requests.exceptions.JSONDecodeError:
        logger.error("❌ 响应不是有效的 JSON")
        return []
    except requests.RequestException as e:
        logger.error(f"❌ 请求异常: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ 发生异常: {e}", exc_info=True)
        return []
    

def getAccountInfo(account):
    logger.info("🔍 开始获取验证码异常的账号列表")
    try:
        response = session.post(
            PLATFORM_BASE_API_ALL, 
            json={
                "pageNum": 1,
                "pageSize": 20,
                "account": account,
                "platform": 7
            }, 
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"❌ 请求失败，状态码: {response.status_code}")
            return []
        
        data = response.json()
        logger.debug(f"📦 返回的原始数据: {data}")
        
        # 确保路径存在且为列表
        if 'data' not in data or not isinstance(data['data'], dict):
            logger.warning("⚠️  没有找到有效的数据")
            return []
        
        outer_data = data['data'].get('data', [])
        
        if not isinstance(outer_data, list):
            logger.warning(f"⚠️  数据格式错误，期望列表，收到: {type(outer_data)}")
            return []
        
        logger.info(f"📋 获取到 {len(outer_data)} 条原始数据")
        
        # 提取 id 字段 且fromType = 21
        id = []
        for item in outer_data:
            if isinstance(item, dict) and item.get('fromType') == 21 and 'id' in item:
                id_value = item['id']
                if id_value:  # 过滤掉空值
                    id.append(id_value)
                    logger.debug(f"✅ 提取id: {id_value}")
            else:
                logger.debug(f"⚠️  项目缺少 'id' 字段或不是字典: {item}")
        
        logger.info(f"✅ 成功提取 {len(id)} 个id")
        logger.debug(f"📝 id列表: {id}")
        return id

    except requests.exceptions.Timeout:
        logger.error("❌ 请求超时")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("❌ 连接错误")
        return []
    except requests.exceptions.JSONDecodeError:
        logger.error("❌ 响应不是有效的 JSON")
        return []
    except requests.RequestException as e:
        logger.error(f"❌ 请求异常: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ 发生异常: {e}", exc_info=True)
        return []

def startTask(list):
    try:
        response = session.post(
            PLATFORM_BASE_API_START,
            json=list,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success") is True:
                print("✅ 成功启动任务 ID:", list)
            else:
                print("❌ 启动任务失败:", data.get("msg", "未知错误"))
        else:
            print("请求失败，状态码:", response.status_code)
    except requests.RequestException as e:
        print("请求异常:", e)

# 主程序
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("开始执行账号过滤任务")
    logger.info("=" * 60)
    
    try:
        accounts = getTheVerificationCode()
        
        if accounts:
            new_acc =  list(set(accounts))
            print("这是账号数组",new_acc)
            logger.info(f"\n✅ 成功获取 {len(new_acc)} 个账号:")
            for account in new_acc:
                ids = getAccountInfo(account)
                print("这是账号对应的id",ids)
                if ids:
                    startTask(ids)
                else:
                    logger.info(f"ℹ️  账号 {account} 没有找到对应的ID")
        else:
            logger.info("ℹ️  没有获取到任何账号")
        
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {e}", exc_info=True)
    
    finally:
        logger.info("=" * 60)
        logger.info("执行完毕")
        logger.info("=" * 60)