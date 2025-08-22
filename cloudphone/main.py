import logging

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
import requests
import subprocess
import aiofiles
import aiohttp
import tempfile
import os
import re
from datetime import datetime
from pydantic import BaseModel
import yaml
import uvicorn
import argparse
from urllib.parse import urlparse
import traceback
app = FastAPI()

# 定义请求体的数据模型
class ModifyDevRequest(BaseModel):
    ip: str
    cmdline: str

# Docker API的地址列表，可以添加多个 Docker 主机的 API 地址
DOCKER_API_URLS = []
CLASH_PROXY_IP = ""
current_directory = os.path.dirname(os.path.abspath(__file__))

@app.get("/containers")
async def get_container_list():
    container_list = []  # 用于存储聚合的容器信息

    # 遍历每个 Docker API URL，获取容器信息
    for docker_api_url in DOCKER_API_URLS:
        try:
            # 使用 requests 向 Docker API 发送 GET 请求
            response = requests.get(docker_api_url, timeout=3)

            # 如果请求成功（状态码为 200）
            if response.status_code == 200:
                containers = response.json()  # 将响应内容转换为 JSON 格式

                # 遍历每个容器，提取相关信息
                for container in containers:
                    container_id = container.get("Id")  # 获取容器的唯一标识符
                    names = container.get("Names", [])  # 获取容器名称列表

                    # 假设我们使用第一个名称作为代表名称，并去掉开头的斜杠 /
                    container_name = names[0].lstrip('/') if names else "unknown"
                    # 过滤掉任何名称包含 "myt_sdk" 的容器
                    if "myt_sdk" in container_name:
                        continue

                    image_name = container.get("Image")  # 获取容器的镜像名
                    created_timestamp = container.get("Created")  # 获取容器创建时间戳

                    # 格式化创建时间戳为指定格式
                    created_time = datetime.fromtimestamp(created_timestamp).strftime('%Y-%m-%d %H:%M:%S')

                    state_status = container.get("State")  # 获取容器状态
                    current_status = container.get("Status")  # 获取容器的当前状态描述

                    # 从 NetworkSettings 中获取 IP 地址
                    networks = container.get("NetworkSettings", {}).get("Networks", {})
                    ip_address = None

                    # 遍历所有网络获取 IP 地址
                    for network_data in networks.values():
                        ip_address = network_data.get("IPAddress")
                        if ip_address:  # 如果找到了 IP 地址，停止遍历
                            break

                    # 构建容器详细信息的字典
                    container_info = {
                        "id": container_id,  # 容器的唯一标识符
                        "name": container_name,  # 容器名称
                        "image": image_name,  # 容器使用的镜像名
                        "created": created_time,  # 容器的创建时间，格式化后的字符串
                        "state": state_status,  # 容器的当前状态
                        "status": current_status,  # 容器的状态描述
                        "ip_address": ip_address,  # 容器的 IP 地址
                        "main_ip": re.search(r'http://(\d+\.\d+\.\d+\.\d+):', docker_api_url).group(1)
                    }
                    # 使用正确的语法访问字典中的键
                    pathLog="/home/logs/"+container_info["main_ip"]+"/"+container_info["name"]
                    # 创建这个目录，如果存在则不创建
                    os.makedirs(pathLog, exist_ok=True)
                    # 将容器信息添加到聚合列表中
                    container_list.append(container_info)
            else:
                # 如果请求失败，抛出 HTTP 异常，并返回对应的状态码
                raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch containers from {docker_api_url}")

        except requests.exceptions.RequestException as e:
            # 捕获可能的请求异常，返回 500 服务器错误
            raise HTTPException(status_code=500, detail=f"Error connecting to Docker API at {docker_api_url}: {str(e)}")

    # 返回包含聚合容器信息的 JSON 响应
    return {"containers": container_list}

@app.post("/modifydev")
async def modify_dev(request: ModifyDevRequest):
    # 构建目标接口 URL
    url = f"http://{request.ip}:9082/modifydev"

    # 构建请求参数
    post_data = {
        'cmd': '6',
        'cmdline': request.cmdline
    }

    try:
        # 发送 POST 请求到目标接口
        response = requests.post(url, data=post_data)

        # 如果请求成功，返回目标接口的响应内容
        if response.status_code == 200:
            return response.json()  # 假设目标接口返回的是 JSON 格式
        else:
            # 如果请求失败，抛出 HTTP 异常，并返回对应的状态码
            raise HTTPException(status_code=response.status_code, detail="Error executing command")

    except requests.exceptions.RequestException as e:
        # 捕获可能的请求异常，返回 500 服务器错误
        raise HTTPException(status_code=500, detail=f"Error connecting to {url}: {str(e)}")


@app.post("/uploadfile")
async def upload_file_to_device(ip: str = Form(...), directory: str = Form(...), filename: str = Form(...), file: UploadFile = File(...)):
    # 检查是否提供了有效的 IP 地址、目录和文件名
    if not ip or not directory or not filename:
        raise HTTPException(status_code=400, detail="IP, target directory, and filename must be specified")

    # 拼接目标路径
    target_path = f"{directory}/{filename}"
    temp_file_path = None  # 初始化 temp_file_path 避免未定义时引用

    try:
        # 设备序列号使用 IP 地址和端口
        adb_serial = f"{ip}:5555"

        # 连接到指定 IP 地址的设备 (使用 5555 端口)
        connect_process = subprocess.run(["adb", "connect", adb_serial], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if connect_process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to connect to device {adb_serial}: {connect_process.stderr.decode()}")

        # 创建一个临时文件，用于存储上传的文件流
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name  # 获取临时文件的路径

            # 异步写入上传文件的内容到临时文件
            async with aiofiles.open(temp_file_path, 'wb') as temp_f:
                content = await file.read()  # 读取整个文件内容
                await temp_f.write(content)  # 写入到临时文件

        # 使用 adb push 命令上传临时文件到设备上的指定路径
        push_process = subprocess.run(["adb", "-s", adb_serial, "push", temp_file_path, target_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 检查 adb push 命令是否执行成功
        if push_process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error pushing file to device: {push_process.stderr.decode()}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing adb command: {str(e)}")

    finally:
        # 删除临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        # 断开与设备的连接
        subprocess.run(["adb", "disconnect", adb_serial], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return {"filename": filename, "target_path": target_path}

@app.post("/uploadFileExit")
async def upload_file_exit(filename: str = Form(...)):
    """
    检测指定文件名在本地 /root/mytsdk/bakk/ 目录下是否存在。

    :param filename: 要检测的文件名
    :return: 包含文件名和文件是否存在的 JSON 响应
    """
    # 检查 filename 是否为空
    if not filename:
        raise HTTPException(status_code=400, detail="文件名必须指定")

    target_path = f"/root/mytsdk/bakk/{filename}"
    file_exists = os.path.exists(target_path)
    return {"filename": filename, "exists": file_exists}

@app.post("/uploadFileToMytDomain")
async def upload_file_to_myt_domain(
        ip: str = Form(...),
        directory: str = Form(...),
        filename: str = Form(...),
        fileurl: str = Form(...)
):
    # 检查是否提供了有效的参数
    if not ip or not directory or not filename or not fileurl:
        raise HTTPException(status_code=400, detail="IP, directory, filename, and fileurl must be specified")
    # 临时文件路径
    temp_file_path = "/root/mytsdk/bakk/"
    target_path = f"/root/mytsdk/bakk/{filename}"
    try:
        temp_file_path = await download_file(fileurl, temp_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    return {"filename": filename, "target_path": target_path, "fileurl": fileurl}


@app.post("/uploadfile_url")
async def upload_file_from_url(
        ip: str = Form(...),
        directory: str = Form(...),
        filename: str = Form(...),
        fileurl: str = Form(...)
):
    # 检查是否提供了有效的参数
    if not ip or not directory or not filename or not fileurl:
        raise HTTPException(status_code=400, detail="IP, directory, filename, and fileurl must be specified")

    # 拼接目标路径
    target_path = f"{directory}/{filename}"

    # 临时文件路径
    temp_file_path = "/opt"
    try:
        # 设备序列号使用 IP 地址和端口
        adb_serial = f"{ip}:5555"

        # 连接到指定 IP 地址的设备 (使用 5555 端口)
        connect_process = subprocess.run(["adb", "connect", adb_serial], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if connect_process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to connect to device {adb_serial}: {connect_process.stderr.decode()}")

        # # 创建一个临时文件，用于存储下载的文件内容
        # with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        #     temp_file_path = temp_file.name  # 获取临时文件的路径

        temp_file_path = await download_file(fileurl, temp_file_path)

        # 使用 adb push 命令上传临时文件到设备上的指定路径
        push_process = subprocess.run(["adb", "-s", adb_serial, "push", temp_file_path, target_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 检查 adb push 命令是否执行成功
        if push_process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error pushing file to device: {push_process.stderr.decode()}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    finally:
        # 删除临时文件
        # if temp_file_path and os.path.exists(temp_file_path):
        #     os.remove(temp_file_path)
        # 断开与设备的连接
        subprocess.run(["adb", "disconnect", adb_serial], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return {"filename": filename, "target_path": target_path, "fileurl": fileurl}

@app.post("/install_xapk_folder")
async def install_xapk_folder(
        ip: str = Form(..., description="ADB设备的IP地址"),
        xapk_folder_path: str = Form(..., description="已解压的XAPK文件夹在服务器上的本地路径")
):
    """
    安装一个已解压的XAPK文件夹中的所有APK文件。
    该文件夹应包含主APK和所有分包APK文件。
    """
    adb_serial = f"{ip}:5555" # ADB设备的序列号，格式为 IP:端口

    try:
        # 1. 连接到指定 IP 地址的设备 (使用 5555 端口)
        print(f"尝试连接到 ADB 设备: {adb_serial}")
        connect_process = subprocess.run(
            ["adb", "connect", adb_serial],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True # 检查返回码，如果非零则抛出 CalledProcessError
        )
        print(f"ADB 连接输出: {connect_process.stdout.decode().strip()}")

        # 2. 验证并查找文件夹中的所有APK文件
        if not os.path.isdir(xapk_folder_path):
            raise HTTPException(status_code=400, detail=f"指定的XAPK文件夹 '{xapk_folder_path}' 不存在或不是一个目录。")

        # 4. 使用 adb install-multiple 命令安装所有APK文件
        # 注意: 使用 shell=True 时，install_command 应该是一个完整的字符串
        # 并且 shell 会在 cwd 指定的目录中展开 *.apk
        install_command = f"adb -s {adb_serial} install-multiple *.apk"

        print(f"将在目录 '{xapk_folder_path}' 中执行的命令: {install_command}")
        install_process = subprocess.run(
            install_command,
            cwd=xapk_folder_path, # <--- 关键修改: 设置当前工作目录为 XAPK 文件夹路径
            shell=True,          # <--- 关键修改: 允许 shell 解析命令字符串和通配符
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True # 检查返回码，如果非零则抛出 CalledProcessError
        )

        # 检查 adb install-multiple 命令是否执行成功
        install_output = install_process.stdout.decode().strip()
        install_error = install_process.stderr.decode().strip()

        if "Success" not in install_output:
            # 如果安装失败，则抛出异常，并包含错误信息
            raise HTTPException(status_code=500, detail=f"APK安装失败: {install_error if install_error else install_output}")

        return {"message": "XAPK文件夹中的APK文件安装成功！", "output": install_output}

    except subprocess.CalledProcessError as e:
        # 处理 subprocess 引起的错误 (如 adb 命令执行失败)
        error_detail = e.stderr.decode().strip() if e.stderr else e.output.decode().strip()
        print(f"ADB 命令执行失败 (返回码: {e.returncode}): {error_detail}")
        raise HTTPException(status_code=500, detail=f"ADB 命令执行失败 (返回码: {e.returncode}): {error_detail}")
    except Exception as e:
        # 捕获所有其他潜在错误
        print(f"安装过程中发生未知错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"安装过程中发生错误: {str(e)}")

    finally:
        # 断开与设备的连接 (即使安装失败也要尝试断开)
        # 确保 adb_serial 已定义，以防前面代码出错导致未定义
        if 'adb_serial' in locals():
            print(f"尝试断开与 ADB 设备: {adb_serial} 的连接")
            disconnect_process = subprocess.run(
                ["adb", "disconnect", adb_serial],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if disconnect_process.returncode != 0:
                print(f"警告: 无法断开与 {adb_serial} 的连接: {disconnect_process.stderr.decode().strip()}")
            else:
                print(f"已成功断开与 {adb_serial} 的连接。")

@app.post("/read-config")
async def read_config():
    '''
        读取Passwall配置文件并返回内容。
    '''
    try:
        # 定义配置文件的路径
        config_path = "/mnt/openwrt/passwall"

        # 检查文件是否存在
        if not os.path.exists(config_path):
            raise HTTPException(status_code=404, detail="配置文件不存在")

        # 读取配置文件内容
        with open(config_path, 'r', encoding='utf-8') as file:
            config_content = file.read()

        # 返回配置内容
        return {"config": config_content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取配置文件时发生错误: {str(e)}")

@app.post("/write-config")
async def write_config(config_content: str = Form(...)):
    '''
        写入Passwall配置文件。
    '''
    try:
        # 定义配置文件的路径
        config_path = "/mnt/openwrt/passwall"

        # 写入配置内容到文件
        with open(config_path, 'w', encoding='utf-8') as file:
            file.write(config_content)

        # 返回成功消息
        return {"message": "配置文件已成功更新"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入配置文件时发生错误: {str(e)}")

async def download_file(fileurl, temp_file_path):
    filename = __get_file_name_by_url(fileurl)
    temp_file_path = os.path.join(temp_file_path, filename)
    print(filename)
    print(temp_file_path)
    if os.path.exists(temp_file_path):
        print("[download_file] 文件已存在 {}".format(temp_file_path))
        return temp_file_path
        pass
    else:
        # 下载文件内容并保存到临时文件
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(fileurl, timeout=aiohttp.ClientTimeout(total=30*60)) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=500, detail=f"Failed to download file from URL: {fileurl}")
                    async with aiofiles.open(temp_file_path, 'wb') as temp_f:
                        while True:
                            chunk = await response.content.read(1024)  # 每次读取 1024 字节
                            if not chunk:
                                break
                            await temp_f.write(chunk)
            print(f"[download_file] 文件下载完成: {temp_file_path}")
            await _process_downloaded_file(temp_file_path)
        except Exception as e:
            error_message = f"Error while downloading file from URL: {fileurl}\n"
            stack_trace = traceback.format_exc()
            print(error_message + stack_trace)
            os.remove(temp_file_path)
        return temp_file_path


async def _process_downloaded_file(file_path: str):
    """
    根据文件扩展名对下载的文件进行处理，例如解压XAPK文件。
    这是一个内部辅助函数。
    """
    # 分离文件名和扩展名
    file_name_without_ext, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower() # 转换为小写以进行统一比较

    if file_extension == '.xapk':
        print(f"检测到XAPK文件: {file_path}，开始解压...")
        # 定义解压的目标目录
        # 目标目录名是原XAPK文件名不带扩展名
        unzip_destination_dir = file_name_without_ext

        # 构建unzip命令
        # 我们使用 shell=True 来让 shell 处理通配符（尽管这里没有），并且执行命令
        # 关键是设置 cwd 参数为文件所在的目录
        # 为了安全和明确，unzip 命令直接使用完整的文件路径
        unzip_command = ["unzip", "-o", file_path, "-d", unzip_destination_dir] # -o 选项表示覆盖现有文件

        print(f"执行解压命令: {' '.join(unzip_command)}")
        try:
            unzip_process = subprocess.run(
                unzip_command,
                cwd=os.path.dirname(file_path), # 设置工作目录为文件所在目录
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True # 检查返回码，如果非零则抛出 CalledProcessError
            )
            print(f"XAPK解压成功！输出:\n{unzip_process.stdout.decode().strip()}")
        except subprocess.CalledProcessError as e:
            error_detail = e.stderr.decode().strip() if e.stderr else e.output.decode().strip()
            print(f"XAPK解压失败 (返回码: {e.returncode}): {error_detail}")
            raise HTTPException(status_code=500, detail=f"XAPK文件 '{file_path}' 解压失败: {error_detail}")
        except Exception as e:
            print(f"解压XAPK文件时发生未知错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"解压XAPK文件时发生错误: {str(e)}")
    else:
        print(f"文件 '{file_path}' 不是XAPK文件，无需解压。")

def _get_config():
    env = os.getenv("APP_ENV", "dev")
    if env == "prod":
        file_name = "config.yaml"
    else:
        file_name = "config-" + env + ".yaml"
    print("[_get_config] env:%s file_name: %s" % (file_name, env))
    path = os.path.abspath(os.path.join(current_directory, "env", file_name))
    print("[_get_config] path: %s" % path)

    with open(path, 'r', encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
        print("[_get_config] cfg: %s" % cfg)
        f.close()
        return cfg

def __get_file_name_by_url(url: str):
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)


# 读取配置并初始化全局变量
def initialize_globals():
    config = _get_config()
    global DOCKER_API_URLS, CLASH_PROXY_IP
    DOCKER_API_URLS = config.get("DOCKER_API_URLS", [])
    CLASH_PROXY_IP = config.get("CLASH_PROXY_IP", "")

# FastAPI 启动时调用初始化函数
@app.on_event("startup")
async def startup():
    initialize_globals()


def main():
    parser = argparse.ArgumentParser(description="Start Uvicorn server")
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address')  # 添加 host 参数
    parser.add_argument('--port', type=int, default=8000, help='Port number')
    parser.add_argument('--env', type=str, default='dev', help='env params')
    args = parser.parse_args()
    os.environ["APP_ENV"] = args.env
    initialize_globals()
    uvicorn.run("main:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
