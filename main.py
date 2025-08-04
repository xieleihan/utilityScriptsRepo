import os
from smbclient import open_file
import smbclient
import secrets
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional, Dict, List, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 应用实例
app = FastAPI(
    title="PassWall Config API",
    description="通过 SMB 协议读取和修改 OpenWrt PassWall 配置",
    version="1.0.0"
)

def read_passwall_config_smb(
    server_ip,
    username,
    password,
    share_name="smb",
    config_path="/smb/etc/config/passwall",
    domain=""
):
    """
        通过 SMB 读取 PassWall 配置文件

        Args:
            server_ip: 路由器 IP 地址
            username: SMB 用户名（通常是 root）
            password: SMB 密码
            share_name: 共享名，默认 C$（Windows 管理共享）
            config_path: 配置文件路径（相对于共享根目录）
            domain: 域（可选）

        Returns:
            str: 配置文件内容
    """
    print(f'sever_ip: {server_ip}, username: {username}, share_name: {share_name}, config_path: {config_path}, domain: {domain}')
    try:
        smbclient.ClientConfig(username=username, password=password, domain=domain) # 配置 SMB 客户端
        smb_path = fr"\\{server_ip}\{share_name}{config_path.replace('/', '\\')}"  # 构建 SMB 路径
        print(f"链接在建立中: {smb_path}")

        # 读取
        with open_file(smb_path, mode='r', encoding='utf-8') as file:
            content = file.read()
            # print(f"读取到的内容: {content}")

        return content
    except Exception as e:
        print(f"SMB 连接失败: {e}")
        return None

@app.get("/")
async def root():
    """根路径"""
    return {"message": "PassWall Config API 服务运行中", "version": "1.0.0"}

@app.get("/read-config")
async def read_config():
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
            print("=== .env 文件原始内容 ===")
            print(repr(content))
            print("=== 结束 ===")
    except Exception as e:
        print("读取 .env 失败:", e)

    load_dotenv()  # 加载环境变量

    server_ip = os.getenv("SERVER_IP")
    username = os.getenv("MYUSERNAME")
    password = os.getenv("MYPASSWORD")
    share_name = os.getenv("SHARE_NAME", "")
    config_path = os.getenv("CONFIG_PATH", "/smb/etc/config/passwall")
    domain = os.getenv("DOMAIN", "")

    if not server_ip or not username or not password:
        print("请确保 SERVER_IP, USERNAME 和 PASSWORD 环境变量已设置。")
        return {"error": "缺少必要的环境变量","code": 500}

    config_content = read_passwall_config_smb(
        server_ip,
        username,
        password,
        share_name,
        config_path,
        domain
    )

    if config_content:
        print("✅ 读取成功!")
        return {"config": config_content, "code": 200}

    else:
        print("❌ 无法读取配置文件")
        return {"error": "无法读取配置文件", "code": 500}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)