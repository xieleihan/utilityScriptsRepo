"""
视频合成处理服务 - 通过 FFmpeg 合成多个视频片段
支持视频片段拼接、缺失片段处理、时间同步
"""

import os
import json
import subprocess
from typing import Dict, Any, List
import requests
import imageio_ffmpeg as iioffmpeg
import time


class VideoCompositorService:
    """视频合成处理服务"""

    def __init__(self):
        self.temp_dir = "temp"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.log_info(f"临时目录路径: {os.path.abspath(self.temp_dir)}")

    def log_info(self, msg: str):
        """记录信息日志"""
        print(f"[INFO] {msg}")

    def log_error(self, msg: str, error: Exception = None):
        """记录错误日志"""
        if error:
            print(f"[ERROR] {msg}: {str(error)}")
        else:
            print(f"[ERROR] {msg}")

    def download_file(self, url: str, filename: str) -> bool:
        """下载文件，并处理 URL 路径末尾可能存在的空格"""
        url = url.strip()
        
        if not url:
            self.log_error(f"URL 为空，跳过下载")
            return False
        
        if not os.path.isabs(filename) and not filename.startswith("temp"):
            filename = os.path.join(self.temp_dir, os.path.basename(filename))
        
        self.log_info(f"Downloading {url[:80]}... -> {filename}")
        try:
            os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
            
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            file_size = os.path.getsize(filename)
            self.log_info(f"✓ 文件下载完成: {filename} ({file_size} 字节)")
            return True
        except requests.exceptions.RequestException as e:
            self.log_error(f"Error downloading {url[:80]}...", e)
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception as remove_error:
                    self.log_error(f"删除失败文件 {filename} 失败", remove_error)
            return False

    def trim_video(self, input_file: str, start_us: int, end_us: int, output_file: str) -> bool:
        """
        根据时间戳剪辑视频
        start_us, end_us: 微秒单位
        """
        # 转换为秒
        start_sec = start_us / 1000000.0
        duration_sec = (end_us - start_us) / 1000000.0
        
        self.log_info(f"剪辑视频: {start_sec:.2f}s - {start_sec + duration_sec:.2f}s ({duration_sec:.2f}s)")
        
        ffmpeg_path = iioffmpeg.get_ffmpeg_exe()
        
        # 使用重新编码确保兼容性
        cmd = (
            f'"{ffmpeg_path}" -y -i "{input_file}" '
            f'-ss {start_sec} -t {duration_sec} '
            f'-c:v libx264 -preset ultrafast -crf 23 '
            f'-c:a aac -b:a 128k '
            f'"{output_file}"'
        )
        
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            if os.path.exists(output_file):
                self.log_info(f"✓ 视频剪辑完成: {os.path.basename(output_file)}")
                return True
            return False
        except subprocess.CalledProcessError as e:
            self.log_error(f"视频剪辑失败", e)
            return False


    def create_black_frame_video(self, width: int, height: int, duration_us: int) -> str:
        """创建黑色帧视频用于填充缺失段"""
        duration_seconds = duration_us / 1000000.0
        output_file = os.path.join(self.temp_dir, f"black_{width}x{height}_{int(duration_us)}.mp4")
        
        if os.path.exists(output_file):
            self.log_info(f"✓ 黑色视频已存在: {output_file}")
            return output_file
        
        self.log_info(f"创建黑色填充视频: {width}x{height}, 时长 {duration_seconds:.2f}秒")
        
        ffmpeg_path = iioffmpeg.get_ffmpeg_exe()
        cmd = (
            f'"{ffmpeg_path}" -f lavfi -i color=black:s={width}x{height} '
            f'-f lavfi -i anullsrc=r=44100:cl=stereo -c:v libx264 -preset ultrafast -t {duration_seconds} '
            f'-pix_fmt yuv420p -c:a aac -b:a 128k "{output_file}"'
        )
        
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
            self.log_info(f"✓ 黑色视频创建完成: {output_file}")
            return output_file
        except subprocess.CalledProcessError as e:
            self.log_error(f"创建黑色视频失败", e)
            raise Exception(f"Failed to create black frame video: {str(e)}")

    def cleanup_temp_files(self):
        """清理临时文件和文件夹"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                for filename in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        self.log_error(f"删除文件 {file_path} 失败", e)
                
                try:
                    os.rmdir(self.temp_dir)
                    self.log_info(f"✓ 临时目录 {self.temp_dir} 已成功清理")
                except Exception as e:
                    self.log_error(f"删除临时目录 {self.temp_dir} 失败", e)
        except Exception as e:
            self.log_error(f"清理临时文件失败", e)

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行视频合成"""
        output_file = None
        start_time = time.time()
        try:
            draft_url = kwargs.get("draft_url", "")
            video_infos_str = kwargs.get("video_infos", "[]")
            
            self.log_info(f"开始视频合成处理...")
            self.log_info(f"Draft URL: {draft_url[:80]}...")
            
            # 解析视频信息
            video_infos = json.loads(video_infos_str)
            
            if not video_infos:
                raise ValueError("视频信息为空")
            
            self.log_info(f"发现 {len(video_infos)} 个视频片段")
            
            # 获取视频宽高和总时长
            width = video_infos[0].get("width", 1024)
            height = video_infos[0].get("height", 1024)
            max_end = max([info.get("end", 0) for info in video_infos])
            total_duration_seconds = max_end / 1000000.0
            
            self.log_info(f"视频尺寸: {width}x{height}")
            self.log_info(f"总时长: {total_duration_seconds:.2f}秒 ({max_end}微秒)")
            
            # 步骤1：下载所有原始视频，并处理缺失片段
            processed_videos = []
            concat_demux_content = ""
            
            for i, info in enumerate(video_infos):
                video_url = info.get("video_url", "").strip()
                start_us = info.get("start", 0)
                end_us = info.get("end", 0)
                duration_us = end_us - start_us
                duration_sec = duration_us / 1000000.0
                
                if not video_url:
                    # 缺失视频片段，创建黑色填充
                    self.log_info(f"片段 {i}: 缺失视频 URL，创建黑色填充 ({duration_sec:.2f}秒)")
                    black_video = self.create_black_frame_video(width, height, duration_us)
                    processed_videos.append(black_video)
                    concat_demux_content += f"file '{os.path.basename(black_video)}'\n"
                else:
                    # 下载视频
                    original_file = os.path.join(self.temp_dir, f"original_{i}.mp4")
                    if not self.download_file(video_url, original_file):
                        raise Exception(f"视频片段 {i} 下载失败")
                    
                    if not os.path.exists(original_file):
                        raise Exception(f"视频文件下载后不存在: {original_file}")
                    
                    # 重新编码为统一格式（确保兼容性），并调整为指定时长
                    processed_file = os.path.join(self.temp_dir, f"processed_{i}.mp4")
                    
                    ffmpeg_path = iioffmpeg.get_ffmpeg_exe()
                    
                    # 使用 pad filter 确保视频时长正确
                    cmd = (
                        f'"{ffmpeg_path}" -y -i "{original_file}" '
                        f'-c:v libx264 -preset ultrafast -crf 23 '
                        f'-c:a aac -b:a 128k '
                        f'-t {duration_sec} '
                        f'"{processed_file}"'
                    )
                    
                    self.log_info(f"片段 {i}: 处理视频 ({duration_sec:.2f}秒)")
                    try:
                        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                        if not os.path.exists(processed_file):
                            raise Exception(f"处理后的视频文件不存在: {processed_file}")
                        self.log_info(f"✓ 片段 {i} 处理完成")
                    except subprocess.CalledProcessError as e:
                        self.log_error(f"处理视频片段 {i} 失败", e)
                        raise Exception(f"处理视频片段 {i} 失败: {str(e)}")
                    
                    processed_videos.append(processed_file)
                    concat_demux_content += f"file '{os.path.basename(processed_file)}'\n"
            
            if not processed_videos:
                raise ValueError("没有有效的视频片段")
            
            self.log_info(f"✓ 所有 {len(processed_videos)} 个片段已处理完毕")
            
            # 步骤2：创建 concat demuxer 配置文件
            concat_config_file = os.path.join(self.temp_dir, "concat_list.txt")
            with open(concat_config_file, 'w', encoding='utf-8') as f:
                f.write(concat_demux_content)
            
            self.log_info(f"✓ Concat 配置文件已创建，包含 {len(processed_videos)} 个片段")
            
            # 步骤3：执行 FFmpeg 合成
            ffmpeg_path = iioffmpeg.get_ffmpeg_exe()
            output_file = os.path.join(self.temp_dir, "output_video.mp4")
            
            self.log_info(f"输出文件路径: {os.path.abspath(output_file)}")
            
            # 在 temp 目录执行命令以使用相对路径
            cmd = (
                f'"{ffmpeg_path}" -y '
                f'-f concat -safe 0 -i "concat_list.txt" '
                f'-c:v copy -c:a copy '
                f'"output_video.mp4"'
            )
            
            self.log_info(f"执行 FFmpeg 合成命令...")
            try:
                result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, cwd=self.temp_dir)
                self.log_info(f"✅ 视频合成完成: {output_file}")
            except subprocess.CalledProcessError as e:
                self.log_error(f"❌ FFmpeg 合成失败", e)
                self.log_error(f"STDOUT: {e.stdout}")
                self.log_error(f"STDERR: {e.stderr}")
                raise Exception(f"FFmpeg 合成失败: {str(e)}")
            
            if not os.path.exists(output_file):
                raise Exception(f"输出文件不存在: {os.path.abspath(output_file)}")
            
            output_size = os.path.getsize(output_file)
            self.log_info(f"输出文件大小: {output_size} 字节 ({output_size/1024/1024:.2f} MB)")
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            time_str = f"{minutes}分{seconds:.2f}秒" if minutes > 0 else f"{seconds:.2f}秒"
            self.log_info(f"✅ 视频合成耗时: {time_str}")
            
            result = {
                "code": 0,
                "message": "视频合成成功",
                "video_path": os.path.abspath(output_file),
                "file_size": output_size,
                "duration_seconds": total_duration_seconds,
                "elapsed_time": f"{time_str}",
                "time": int(time.time() * 1000)
            }
            
            return result

        except Exception as e:
            self.log_error("视频合成失败", e)
            
            result = {
                "code": 1,
                "message": f"视频合成失败: {str(e)}",
                "video_path": "",
                "file_size": 0,
                "duration_seconds": 0,
                "time": int(time.time() * 1000)
            }
            
            return result
        finally:
            # 清理临时文件
            if output_file and os.path.exists(output_file):
                # 只清理非输出文件的临时文件
                try:
                    import shutil
                    for filename in os.listdir(self.temp_dir):
                        file_path = os.path.join(self.temp_dir, filename)
                        if file_path != output_file:
                            try:
                                if os.path.isfile(file_path) or os.path.islink(file_path):
                                    os.unlink(file_path)
                                elif os.path.isdir(file_path):
                                    shutil.rmtree(file_path)
                            except Exception as e:
                                pass
                except:
                    pass


if __name__ == "__main__":
    data = {
    "draft_url": "https://ts.fyshark.com/#/cozeToJianyin?drafId=https://video-snot-12220.oss-cn-shanghai.aliyuncs.com/2025-10-28/draft/9b4feac8-04de-43d6-8592-73b731e77edb.json",
    "video_infos": "[{\"video_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/videos/girl_dance/half_body_dance/%E5%8D%8A%E8%BA%AB%E8%88%9E%E8%B9%88100.mp4\",\"width\":1024,\"height\":1024,\"start\":0,\"end\":4000000,\"duration\":4000000,\"mask\":\"\"},{\"video_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/videos/girl_dance/half_body_dance/%E5%8D%8A%E8%BA%AB%E8%88%9E%E8%B9%8811.mp4\",\"width\":1024,\"height\":1024,\"start\":4000000,\"end\":8000000,\"duration\":4000000,\"mask\":\"\"},{\"video_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/videos/girl_dance/half_body_dance/%E5%8D%8A%E8%BA%AB%E8%88%9E%E8%B9%8812.mp4\",\"width\":1024,\"height\":1024,\"start\":8000000,\"end\":12000000,\"duration\":4000000,\"mask\":\"\"},{\"video_url\":\"https://test-redao.oss-cn-beijing.aliyuncs.com/videos/girl_dance/half_body_dance/8%E6%9C%8826%E6%97%A5.mp4\",\"width\":1024,\"height\":1024,\"start\":12000000,\"end\":16000000,\"duration\":4000000,\"mask\":\"\"}]"
}
    
    compositor = VideoCompositorService()
    result = compositor.execute(**data)
    print(f"\n最终结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
