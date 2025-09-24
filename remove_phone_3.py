import requests
import time
import logging

BASE_URL = "http://rdcpc3.echoing.cc:10012"
TIMEOUT = 300      # 超时 10秒
DELAY_BETWEEN_HOSTS = 1.0  # 主机间间隔
MAX_RETRIES = 5    # 最大重试次数

ips = [
    "192.168.150.3",
    "192.168.150.4",
    "192.168.150.5",
    "192.168.150.6",
    "192.168.150.7",
    "192.168.150.8",
    "192.168.150.9",
    "192.168.150.10",
    "192.168.150.12",
    "192.168.150.13",
    "192.168.150.14",
    "192.168.150.15",
    "192.168.150.16",
    "192.168.150.17",
    "192.168.150.18",
    "192.168.150.19",
    "192.168.150.21",
    "192.168.150.22",
    "192.168.150.23",
    "192.168.150.24",
    "192.168.150.25",
    "192.168.150.26",
    "192.168.150.28",
    "192.168.150.30",
    "192.168.150.31",
    "192.168.150.32",
    "192.168.150.33",
    "192.168.150.34",
    "192.168.150.35",
    "192.168.150.36",
    "192.168.150.37",
    "192.168.150.40",
    "192.168.150.41",
    "192.168.150.42",
    "192.168.150.43",
    "192.168.150.44",
    "192.168.150.45",
    "192.168.150.46",
    "192.168.150.47"
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("install_sdk.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def install_sdk_to_host(ip):
    url = f"{BASE_URL}/host_api/v1/install_sdk"
    params = {"ip_list": ip}

    try:
        logger.info(f"请求安装 SDK: {ip}")
        response = requests.get(url, params=params, timeout=TIMEOUT)

        result_text = response.text.strip()
        logger.info(f"响应: {ip} → [{response.status_code}] {result_text}")
        print(f"{ip} {result_text}")

        return True

    except requests.exceptions.Timeout:
        logger.error(f"超时: {ip}")
        print(f"{ip} 请求超时")
    except requests.exceptions.ConnectionError:
        logger.error(f"连接失败: {ip}")
        print(f"{ip} 连接失败")
    except Exception as e:
        logger.error(f"未知错误: {ip} → {e}")
        print(f"{ip} 发生错误: {e}")

    # 发生异常也返回 True，确保流程继续
    return True

if __name__ == "__main__":
    total = len(ips)
    logger.info(f"开始为 {total} 台主机安装 SDK")

    for i, ip in enumerate(ips, 1):
        logger.info(f"[{i}/{total}] 处理主机: {ip}")
        install_sdk_to_host(ip)  # 强制继续
        time.sleep(DELAY_BETWEEN_HOSTS)

    logger.info("所有请求已完成！")
