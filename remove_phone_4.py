import requests
import time
import logging
import json

BASE_URL = "http://rdcpc3.echoing.cc:10012"
IMAGE_ADDR = "registry.cn-guangzhou.aliyuncs.com/mytos/dobox:Q12_base_202508141406"
RESOLUTION = "1"
DNS = "8.8.8.8"
WIDTH = "1080"
HEIGHT = "1920"
TIMEOUT = 300
DELAY_BETWEEN_VMS = 3.0  # 创建后等待 3 秒
MAX_RETRIES = 5

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
        logging.FileHandler("create_vms.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def request_with_retry(method, url, **kwargs):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug(f"[尝试 {attempt}/{MAX_RETRIES}] {method} {url}")
            if method.upper() == "GET":
                response = requests.get(url, timeout=TIMEOUT, **kwargs)
            elif method.upper() == "POST":
                response = requests.post(url, timeout=TIMEOUT, **kwargs)
            else:
                raise ValueError("Unsupported HTTP method")

            if response.status_code in (200, 201, 202):
                return response
            else:
                logger.warning(f"HTTP {response.status_code} {response.reason} for {url}")
                if attempt < MAX_RETRIES:
                    backoff = 2 ** (attempt - 1)
                    time.sleep(backoff)
        except Exception as e:
            logger.error(f" {method} {url} 失败: {e} (尝试 {attempt}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES:
                backoff = 2 ** (attempt - 1)
                time.sleep(backoff)
    return None

def create_and_run_vms_for_ip(ip):
    # 检查当前已创建的 VM 数量
    check_url = f"{BASE_URL}/get/{ip}"
    response = request_with_retry("GET", check_url)
    if not response:
        logger.error(f" 无法获取 {ip} 的云机列表，跳过")
        return False

    try:
        data = response.json()
        current_count = len(data.get("msg", []))
        logger.info(f" {ip} 当前已有 {current_count} 个云机实例")
        print(f"{ip} 当前已有 {current_count} 个云机实例")
    except Exception as e:
        logger.error(f" 解析 {ip} 响应失败: {e}")
        return False

    if current_count >= 5:
        logger.info(f" {ip} 已有 5 个实例，跳过创建")
        print(f"{ip} 已经搞完5个过了")
        return True

    # 创建并启动缺失的实例
    for i in range(1, 6):
        name = f"{ip}T100{i}"
        logger.info(f"开始处理 {name}")

        # 构造创建 URL
        create_url = f"{BASE_URL}/dc_api/v1/create/{ip}/{i}/{name}"
        params = {
            "image_addr": IMAGE_ADDR,
            "resolution": RESOLUTION,
            "width": WIDTH,
            "height": HEIGHT,
            "custom_tag": name,
            "dns": DNS
        }

        # 发送 POST 请求创建
        response = request_with_retry("POST", create_url, params=params)
        if response:
            result_text = response.text.strip()
            logger.info(f" 创建成功: {name} → {result_text}")
            print(f"{name} → {result_text}")
        else:
            logger.error(f" 创建失败: {name}")
            print(f"{name} → 创建失败")
            continue  # 继续下一个，不阻塞

        # 等待 3 秒
        time.sleep(DELAY_BETWEEN_VMS)

        # 启动云机
        run_url = f"{BASE_URL}/run/{ip}/{name}"
        response = request_with_retry("GET", run_url)
        if response:
            result_text = response.text.strip()
            logger.info(f"启动成功: {name} → {result_text}")
            print(f"{name} 启动 → {result_text}")
        else:
            logger.error(f" 启动失败: {name}")
            print(f"{name} 启动失败")

    return True

if __name__ == "__main__":
    total_ips = len(ips)
    logger.info(f"开始为 {total_ips} 台主机创建云机实例...")

    for idx, ip in enumerate(ips, 1):
        logger.info(f"======== [{idx}/{total_ips}] 处理主机: {ip} ========")
        print(f"\n=== [{idx}/{total_ips}] {ip} 开始处理 ===")
        create_and_run_vms_for_ip(ip)
        print(f"=== [{idx}/{total_ips}] {ip} 处理完成 ===\n")

    logger.info(" 所有主机处理完成！")
    print("\n 所有任务已完成！")