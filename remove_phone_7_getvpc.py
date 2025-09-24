import requests
import time

# ========== 你的 39 个 IP 列表 ==========
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

BASE_URL = "http://rdcpc3.echoing.cc:10012/dc_api/v1/vpc_get_list/"
TIMEOUT = 300  # 超时时间（秒）
DELAY = 0.5   # 每次请求间隔（秒），避免打挂服务端

def reset_host(ip):
    url = f"{BASE_URL}{ip}"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            print(f" 成功: {ip} → {response.status_code} {response.reason}")
            # 如果需要，可以打印返回内容：print(response.text)
        else:
            print(f"  失败: {ip} → {response.status_code} {response.reason}")
    except requests.exceptions.Timeout:
        print(f"  超时: {ip}")
    except requests.exceptions.ConnectionError:
        print(f" 连接失败: {ip}")
    except Exception as e:
        print(f" 错误: {ip} → {e}")

if __name__ == "__main__":
    print(f" 开始获取 {len(ips)} 个主机的vpc")
    for i, ip in enumerate(ips, 1):
        print(f"[{i}/{len(ips)}] 正在获取: {ip}")
        reset_host(ip)
        time.sleep(DELAY)  # 控制请求频率

    print(" 所有请求已完成！")