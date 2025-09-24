import requests
import time
import logging

BASE_URL = "http://rdcpc3.echoing.cc:10012"
IMAGE_ADDR = "registry.cn-guangzhou.aliyuncs.com/mytos/dobox:Q12_base_202508141406"
TIMEOUT = 600  # 单次请求超时 5 分钟
DELAY_BETWEEN_HOSTS = 1.0  # 主机间间隔
MAX_RETRIES = 5  # 最大重试次数

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
        logging.FileHandler("pull_image.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def pull_image_to_host_with_retry(ip):
    url = f"{BASE_URL}/dc_api/v1/pull_image2/{ip}"
    params = {"image_addr": IMAGE_ADDR}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f" [尝试 {attempt}/{MAX_RETRIES}] 请求主机: {ip}")
            response = requests.post(url, params=params, timeout=TIMEOUT)

            if response.status_code in (200, 201, 202):
                logger.info(f"成功: {ip} → HTTP {response.status_code} {response.reason}")
                return True  # 成功，退出重试循环
            else:
                logger.warning(f"失败: {ip} → HTTP {response.status_code} {response.reason}")
                if attempt < MAX_RETRIES:
                    backoff = 2 ** (attempt - 1)  # 指数退避：1s, 2s, 4s, 8s, 16s
                    logger.info(f"等待 {backoff} 秒后重试...")
                    time.sleep(backoff)

        except requests.exceptions.Timeout:
            logger.error(f"超时: {ip} → 尝试 {attempt}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES:
                backoff = 2 ** (attempt - 1)
                logger.info(f"等待 {backoff} 秒后重试...")
                time.sleep(backoff)
        except requests.exceptions.ConnectionError:
            logger.error(f"连接失败: {ip} → 尝试 {attempt}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES:
                backoff = 2 ** (attempt - 1)
                logger.info(f"等待 {backoff} 秒后重试...")
                time.sleep(backoff)
        except Exception as e:
            logger.error(f"未知错误: {ip} → {e} → 尝试 {attempt}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES:
                backoff = 2 ** (attempt - 1)
                logger.info(f"等待 {backoff} 秒后重试...")
                time.sleep(backoff)

    logger.error(f"最终失败: {ip} → 已重试 {MAX_RETRIES} 次")
    return False

if __name__ == "__main__":
    total = len(ips)
    success_count = 0
    fail_count = 0

    logger.info(f"开始为 {total} 台主机拉取并导入镜像: {IMAGE_ADDR}")

    for i, ip in enumerate(ips, 1):
        logger.info(f"======== [{i}/{total}] 处理主机: {ip} ========")
        if pull_image_to_host_with_retry(ip):
            success_count += 1
        else:
            fail_count += 1
        time.sleep(DELAY_BETWEEN_HOSTS)  # 主机间间隔

    logger.info("所有请求已完成！")
    logger.info(f"成功: {success_count} 台 | 失败: {fail_count} 台")