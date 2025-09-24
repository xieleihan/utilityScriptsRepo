import requests
import time
import logging
import json

BASE_URL = "http://rdcpc3.echoing.cc:10012"
TIMEOUT = 300
DELAY_BETWEEN_REQUESTS = 1.0  # 每次请求后等待 1 秒

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

CMD = "ping -c 4 www.goolge.com"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("execute_shell.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def execute_adb_shell(ip, name):
    url = f"{BASE_URL}/and_api/v1/shell/{ip}/{name}"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "cmd": CMD
    }

    try:
        logger.info(f"执行命令: {ip}/{name} → {CMD}")
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)

        result_text = response.text.strip()
        logger.info(f"响应: [{response.status_code}] {result_text}")
        print(f"{ip}/{name} → {result_text}")

    except requests.exceptions.Timeout:
        logger.error(f"超时: {ip}/{name}")
        print(f"{ip}/{name} → 请求超时")
    except requests.exceptions.ConnectionError:
        logger.error(f"连接失败: {ip}/{name}")
        print(f"{ip}/{name} → 连接失败")
    except Exception as e:
        logger.error(f"未知错误: {ip}/{name} → {e}")
        print(f"{ip}/{name} → 发生错误: {e}")

if __name__ == "__main__":
    total_ips = len(ips)
    total_commands = total_ips * 5
    logger.info(f"开始为 {total_ips} 台主机 × 5 实例 = {total_commands} 次命令执行...")

    count = 0
    for idx, ip in enumerate(ips, 1):
        print(f"\n=== [{idx}/{total_ips}] 处理主机: {ip} ===")
        logger.info(f"======== [{idx}/{total_ips}] 处理主机: {ip} ========")

        for i in range(1, 6):
            name = f"{ip}T100{i}"
            count += 1
            logger.info(f"[{count}/{total_commands}] → {ip}/{name}")

            execute_adb_shell(ip, name)
            time.sleep(DELAY_BETWEEN_REQUESTS)  # 每次请求后等 1 秒

    logger.info(" 所有命令执行完成！")
    print(f"\n 共执行 {total_commands} 次 ADB Shell 命令，任务已完成！")