import os
import json
import subprocess
import requests
import imageio_ffmpeg as iioffmpeg

def download_file(url, filename):
    """下载文件，并处理 URL 路径末尾可能存在的空格"""
    # 确保 URL 在下载前被清理
    url = url.strip()
    print(f"Downloading {url} -> {filename}")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        # 如果下载失败，删除可能创建的空文件
        if os.path.exists(filename):
            os.remove(filename)
        raise

def get_real_video_url(draft_url):
    """通过 API 获取真实的视频 URL"""
    api_url = "https://ts-api.fyshark.com/api/get_draft_status"
    headers = {"Content-Type": "application/json"}
    payload = {"draft_url": draft_url}
    
    print(f"Fetching real video URL from API...")
    response = requests.post(api_url, json=payload, headers=headers)
    response.raise_for_status()
    
    result = response.json()
    real_video_url = result.get("data", {}).get("video_url")
    
    if not real_video_url:
        raise ValueError(f"Failed to get video_url from API response: {result}")
    
    print(f"Got real video URL: {real_video_url}")
    return real_video_url

def combine_video_audio(data):
    # 1. 解析数据和设置时长
    audio_infos = json.loads(data["audio_infos"])
    draft_video_url = data["video_url"]
    
    # max_duration 是微秒，转换为秒
    max_duration_seconds = data["max_duration"] / 1000000.0 
    print(f"Maximum video duration set to: {max_duration_seconds:.2f} seconds ({data['max_duration']} microseconds).")

    # 2. 获取视频 URL 并下载
    video_url = get_real_video_url(draft_video_url)
    os.makedirs("temp", exist_ok=True)
    video_file = "temp/video.mp4"
    download_file(video_url, video_file)

    # 3. 下载配音音频文件并构建 filter_complex
    input_files = []
    filter_parts = []

    # 循环下载配音音频
    for i, info in enumerate(audio_infos):
        # 注意: 这里使用 info["audio_url"].strip() 确保去除 URL 尾部空格
        audio_file = f"temp/audio_{i}.mp3"
        download_file(info["audio_url"].strip(), audio_file)
        # 为每个外部音频文件添加 -i 参数 (索引从 1 开始: [1:a], [2:a], ...)
        input_files.append(f"-i {audio_file}")

        # 计算延时和音量
        # start 和 end 是微秒，adelay 需要毫秒，所以除以 1000
        start_us = info["start"]
        end_us = info["end"]
        start_ms = int(start_us / 1000)
        duration_ms = int((end_us - start_us) / 1000)
        volume = info.get("volume", 1)
        
        print(f"  Audio {i}: start={start_us}µs ({start_ms}ms), end={end_us}µs, duration={duration_ms}ms")
        
        # 使用 adelay, volume 滤镜，并给每个处理后的音频流一个标签 [a0], [a1], ...
        filter_parts.append(
            f"[{i+1}:a]adelay={start_ms}|{start_ms},volume={volume}[a{i}];"
        )

    num_dub = len(audio_infos)
    # 构建所有配音的标签: [a0][a1]...[aN]
    dub_labels = "".join([f"[a{i}]" for i in range(num_dub)])

    # [0:a] 是原视频音频流
    # 确保原视频音频流和所有配音流一起混音
    filter_complex = (
        # 1. 处理原视频音频流 [0:a]，resample/pan 以确保兼容性，并给它 [original] 标签
        f"[0:a]aresample=44100,pan=stereo|c0=c0|c1=c1,asetpts=PTS-STARTPTS[original];"
        # 2. 注入所有配音的延时和音量处理
        + "".join(filter_parts)
        # 3. 混合所有音频流 (原声 [original] + 所有配音 {dub_labels})
        # inputs={num_dub + 1} 表示原声 + num_dub 个配音
        # duration=longest 仍保留，但会被 -t 选项覆盖
        + f"[original]{dub_labels}amix=inputs={num_dub + 1}:duration=longest:dropout_transition=0:weights=" 
        + "|".join(["1"] * (num_dub + 1))  # 所有轨道权重为1
        + "[aout]"
    )

    # 4. 构建并执行 FFmpeg 命令
    ffmpeg_path = iioffmpeg.get_ffmpeg_exe()
    
    # 关键修改：添加 -t {max_duration_seconds} 来限制输出时长
    cmd = (
        f'"{ffmpeg_path}" -y '
        f'-i {video_file} {" ".join(input_files)} '
        f'-filter_complex "{filter_complex}" '
        f'-map 0:v -map "[aout]" '
        f'-c:v copy -c:a aac -b:a 128k '
        f'-t {max_duration_seconds} '
        f'output.mp4'
    )
    
    print(f"\nRunning FFmpeg:\n{cmd}\n")
    try:
        # 使用 stderr=subprocess.PIPE 来捕获 FFmpeg 的进度输出，但这里为了方便查看，直接让它输出到控制台
        subprocess.run(cmd, shell=True, check=True, capture_output=False)
        print("合成完成：output.mp4")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg failed with error: {e}")
        # 如果需要更详细的错误信息，可以捕获输出并打印
        # print(e.stderr.decode('utf-8'))
        
if __name__ == "__main__":
    # 示例数据
    data = {
        "audio_infos": "[{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmptcz43knn_081fdf70.mp3   \",\"start\":0,\"end\":4826000,\"volume\":1},{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmpweldsagc_10b39003.mp3   \",\"start\":4826000,\"end\":11553000,\"volume\":1},{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmp0551x5uy_ea5fca95.mp3   \",\"start\":11553000,\"end\":17660000,\"volume\":1},{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmpo2o6hgam_d66f0511.mp3   \",\"start\":23082170,\"end\":28054170,\"volume\":1},{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmpw9njd5qu_9fe4cb99.mp3   \",\"start\":28054170,\"end\":32291170,\"volume\":1},{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmpgcyc5yd__9f9adad5.mp3   \",\"start\":32291170,\"end\":38394170,\"volume\":1},{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmpr2dev9zj_6dfa0166.mp3   \",\"start\":43816340,\"end\":51713340,\"volume\":1},{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmp12x1l2rr_dc34dab0.mp3   \",\"start\":51713340,\"end\":55780340,\"volume\":1},{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmpklk6evrc_0a115888.mp3   \",\"start\":55780340,\"end\":60441340,\"volume\":1},{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmpoifnko56_a5c2d181.mp3   \",\"start\":65863511,\"end\":73144511,\"volume\":1},{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmp647ci7kr_83cbe8c2.mp3   \",\"start\":73144511,\"end\":82092511,\"volume\":1},{\"audio_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/uploads/2025/10/21/tmpzz49dsrs_be69b54a.mp3   \",\"start\":82092511,\"end\":90033333,\"volume\":1}]",
        "max_duration": 90033333, # 使用最长的音频结束时间作为 max_duration
        "video_url": "https://video.aiyes.vip/api/get_video/3bd83cda-5502-450b-b3af-1f8bccb5e63a"
    }
    combine_video_audio(data)
