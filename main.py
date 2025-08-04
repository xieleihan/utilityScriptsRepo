import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Any

import smbclient
from smbclient import open_file
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

# ------------------- 初始化 FastAPI 和日志 -------------------
app = FastAPI(
    title="PassWall Config API",
    description="通过 SMB 协议读取和修改 OpenWrt PassWall 配置",
    version="1.0.0"
)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------- 工具函数 -------------------
def load_smb_env_config() -> Dict[str, str]:
    load_dotenv()
    return {
        "server_ip": os.getenv("SERVER_IP"),
        "username": os.getenv("MYUSERNAME"),
        "password": os.getenv("MYPASSWORD"),
        "share_name": os.getenv("SHARE_NAME", "smb"),
        "config_path": os.getenv("CONFIG_PATH", "/etc/config/passwall"),
        "domain": os.getenv("DOMAIN", "")
    }

def build_smb_path(server_ip: str, share_name: str, config_path: str) -> str:
    norm_path = config_path.replace("/", "\\")
    return f"\\\\{server_ip}\\{share_name}{norm_path}"

# ------------------- 数据模型 -------------------
class SMBConfig(BaseModel):
    server_ip: str
    username: str
    password: str
    share_name: str = "smb"

class ConfigSection(BaseModel):
    type: str
    name: str
    options: Dict[str, str]

class AddSectionFullRequest(BaseModel):
    smb_config: SMBConfig
    section: ConfigSection
    shunt_node_name: str = None
    shunt_option_suffix: str = None
    shunt_proxy_node: str = None

# ------------------- 核心类 -------------------
class PassWallConfigManager:
    def __init__(self, server_ip: str, username: str, password: str, share_name: str, config_path: str):
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.share_name = share_name
        self.config_path = config_path
        self.smb_path = build_smb_path(server_ip, share_name, config_path)
        smbclient.register_session(server_ip, username=username, password=password)

    def read_config(self) -> str:
        try:
            with open_file(self.smb_path, mode='r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取失败: {e}")
            raise HTTPException(status_code=500, detail=f"读取失败: {str(e)}")

    def write_config(self, content: str) -> bool:
        try:
            with open_file(self.smb_path, mode='w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"写入失败: {e}")
            raise HTTPException(status_code=500, detail=f"写入失败: {str(e)}")

    def parse_config(self, content: str) -> List[Dict]:
        sections = []
        current_section = None
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('config '):
                if current_section:
                    sections.append(current_section)
                parts = line.split()
                current_section = {
                    'type': parts[1],
                    'name': parts[2] if len(parts) >= 3 else '',
                    'options': {}
                }
            elif line.startswith('option ') and current_section:
                match = re.match(r"option\s+(\w+)\s+(.+)", line)
                if match:
                    key, value = match.groups()
                    value = value.strip("'\"")
                    current_section['options'][key] = value
        if current_section:
            sections.append(current_section)
        return sections

    def format_config(self, sections: List[Any]) -> str:
        lines = []
        for section in sections:
            lines.append("")
            # 使用 . 访问属性
            if section.name:
                lines.append(f"config {section.type} '{section.name}'")
            else:
                lines.append(f"config {section.type}")
            for key, value in section.options.items():
                escaped = value.replace("'", "\\'") if any(c in value for c in " ' \"") else value
                lines.append(f"\toption {key} '{escaped}'")
        return '\n'.join(lines).strip()

# ------------------- 接口 -------------------
@app.get("/")
async def root():
    return {"message": "PassWall Config API 正常运行", "version": "1.0.0"}

# 读取配置文件信息
@app.get("/read-config")
async def read_config():
    cfg = load_smb_env_config()
    if not cfg["server_ip"] or not cfg["username"] or not cfg["password"]:
        raise HTTPException(status_code=400, detail="缺少必要环境变量")
    manager = PassWallConfigManager(cfg["server_ip"], cfg["username"], cfg["password"], cfg["share_name"], cfg["config_path"])
    content = manager.read_config()
    return {"success": 'success', "code": 200, "data": content}

# 添加配置段(往配置文件后面添加)
'''
    测试
    curl --location 'http://127.0.0.1:8000/config/add-section' \
    --header 'Content-Type: application/json' \
    --data '{
      "smb_config": {
        "server_ip": "192.168.10.1",
        "username": "root",
        "password": "redao2024",
        "share_name": "smb"
      },
      "section": {
        "type": "shunt_rules",
        "name": "fenliu_test_ssh",
        "options": {
          "remarks": "fenliu_test_ssh",
          "network": "tcp,udp",
          "source": "192.168.10.23",
          "ip_list": "0.0.0.0/0"
        }
      }
    }'
    raw
    {
      "smb_config": {
        "server_ip": "192.168.10.1",
        "username": "root",
        "password": "redao2024",
        "share_name": "smb"
      },
      "section": {
        "type": "shunt_rules",
        "name": "fenliu_test_ssh",
        "options": {
          "remarks": "fenliu_test_ssh",
          "network": "tcp,udp",
          "source": "192.168.10.23",
          "ip_list": "0.0.0.0/0"
        }
      }
    }
'''
@app.post("/config/add-section")
async def add_section(payload: AddSectionFullRequest):
    smb_config = payload.smb_config
    section = payload.section
    shunt_node_name = payload.shunt_node_name
    shunt_option_suffix = payload.shunt_option_suffix
    shunt_proxy_node = payload.shunt_proxy_node

    manager = PassWallConfigManager(
        smb_config.server_ip,
        smb_config.username,
        smb_config.password,
        smb_config.share_name,
        "/etc/config/passwall"
    )

    content = manager.read_config()
    sections = manager.parse_config(content)
    sections = [ConfigSection(**s) if isinstance(s, dict) else s for s in sections]
    sections.append(section)

    if shunt_node_name and shunt_option_suffix and shunt_proxy_node:
        print("[调试] 命中目标 section，正在修改 options1")
        for idx, sec in enumerate(sections):
            print(f"[调试] 当前 section: {sec.name}, type: {sec.type}")
            if sec.type == "nodes" and sec.name == shunt_node_name:
                print("[调试] 命中目标 section，正在修改 options")
                logger.info(f"添加 shunt 选项到 section: {sec.name}")
                sec.options[f"fenliu_{shunt_option_suffix}"] = shunt_proxy_node
                sec.options[f"fenliu_{shunt_option_suffix}_proxy_tag"] = "main"
                sections[idx] = sec
                break

    new_content = manager.format_config(sections)
    manager.write_config(new_content)

    return {
        "success": 'success',
        "message": "配置段添加成功",
        "section": section
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)