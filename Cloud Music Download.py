from math import log
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import requests
import threading
import webbrowser
import subprocess
import os
import sys
import time
import json
from datetime import datetime
from PIL import Image, ImageTk
import io
import base64

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# 设置 customtkinter 外观
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

def get_app_dir():
    """获取应用程序所在目录（兼容开发和打包环境）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def resolve_path(path):
    """将相对路径转换为绝对路径"""
    if not path:
        return path
    
    if os.path.isabs(path):
        return path
    
    app_dir = get_app_dir()
    resolved = os.path.normpath(os.path.join(app_dir, path))
    return resolved

def make_relative_path(path):
    """将绝对路径转换为相对路径（如果可能）"""
    if not path:
        return path
    
    if not os.path.isabs(path):
        return path
    
    app_dir = get_app_dir()
    try:
        rel_path = os.path.relpath(path, app_dir)
        if len(rel_path) < len(path):
            return rel_path
    except:
        pass
    
    return path

CONFIG_FILE = os.path.join(get_app_dir(), "config.json")
USER_DATA_DIR = os.path.join(get_app_dir(), "userdata")

def ensure_user_data_dir():
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "file_name_format" not in config:
                    config["file_name_format"] = "song-artist"
                if "current_user_file" not in config:
                    config["current_user_file"] = None
                if "auto_close_download_window" not in config:
                    config["auto_close_download_window"] = False
                if "auto_start_api" not in config:
                    config["auto_start_api"] = False
                if "auto_close_api" not in config:
                    config["auto_close_api"] = True
                if "api_path" not in config:
                    config["api_path"] = ""
                return config
        except:
            pass
    return {"api_url": "http://localhost:3000", "file_name_format": "song-artist", "current_user_file": None, "auto_close_download_window": False, "auto_start_api": False, "auto_close_api": True, "api_path": ""}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_all_user_files():
    ensure_user_data_dir()
    files = []
    if os.path.exists(USER_DATA_DIR):
        for f in os.listdir(USER_DATA_DIR):
            if f.startswith("user_data") and f.endswith(".json"):
                files.append(os.path.join(USER_DATA_DIR, f))
    return sorted(files)

def get_next_user_file():
    ensure_user_data_dir()
    base_file = os.path.join(USER_DATA_DIR, "user_data.json")
    if not os.path.exists(base_file):
        return base_file
    
    index = 1
    while True:
        next_file = os.path.join(USER_DATA_DIR, f"user_data{index}.json")
        if not os.path.exists(next_file):
            return next_file
        index += 1

def load_user_data(user_file=None):
    ensure_user_data_dir()
    if user_file:
        if os.path.exists(user_file):
            try:
                with open(user_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return None
    
    config = load_config()
    current_file = config.get("current_user_file")
    if current_file and os.path.exists(current_file):
        try:
            with open(current_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    
    user_files = get_all_user_files()
    if user_files:
        try:
            with open(user_files[0], "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

def save_user_data(cookie, user_name, user_id, user_file=None):
    ensure_user_data_dir()
    data = {
        "cookie": cookie,
        "user_name": user_name,
        "user_id": user_id
    }
    
    if user_file:
        save_file = user_file
    else:
        existing_file = find_user_file_by_id(user_id)
        if existing_file:
            save_file = existing_file
        else:
            save_file = get_next_user_file()
    
    with open(save_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    config = load_config()
    config["current_user_file"] = save_file
    save_config(config)
    
    return save_file

def find_user_file_by_id(user_id):
    user_files = get_all_user_files()
    for f in user_files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
                if data.get("user_id") == user_id:
                    return f
        except:
            pass
    return None

def get_all_users():
    user_files = get_all_user_files()
    users = []
    for f in user_files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
                users.append({
                    "file": f,
                    "user_name": data.get("user_name", "未知用户"),
                    "user_id": data.get("user_id")
                })
        except:
            pass
    return users


def get_download_dir():
    config = load_config()
    custom_dir = config.get("download_dir")
    if custom_dir:
        resolved_dir = resolve_path(custom_dir)
        if os.path.exists(resolved_dir):
            return resolved_dir
        try:
            os.makedirs(resolved_dir, exist_ok=True)
            return resolved_dir
        except:
            pass
    download_dir = os.path.join(get_app_dir(), 'downloads')
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    return download_dir


def sanitize_filename(name):
    if os.name == 'nt':
        invalid_chars = '<>:"/\\|?*'
    else:
        invalid_chars = '/\0'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name


class DownloadWindow(ctk.CTkToplevel):
    def __init__(self, parent, song_name, song_id, base_url, log_callback, artist_name="", name_format="song-artist", auto_close=False):
        super().__init__(parent)
        self.song_name = song_name
        self.song_id = song_id
        self.base_url = base_url
        self.log_callback = log_callback
        self.artist_name = artist_name
        self.name_format = name_format
        self.auto_close = auto_close
        self.cancelled = False
        self.download_dir = get_download_dir()
        self.temp_file = None
        self.final_file = None
        self._alive = True
        
        self.title(f"下载: {song_name}")
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        window_width = 550
        window_height = 300
        
        window_width = min(window_width, int(screen_width * 0.4))
        window_height = min(window_height, int(screen_height * 0.4))
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        
        self.update_idletasks()
        actual_width = self.winfo_width()
        actual_height = self.winfo_height()
        actual_x = (screen_width - actual_width) // 2
        actual_y = (screen_height - actual_height) // 2
        self.geometry(f"+{actual_x}+{actual_y}")
        
        self.setup_ui()
        
        self.update_idletasks()
        self.after(200, self.start_download)
    
    def setup_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text=f"歌曲: {self.song_name}", font=("", 14, "bold")).pack(anchor="w")
        
        self.status_label = ctk.CTkLabel(frame, text="正在获取下载链接...")
        self.status_label.pack(anchor="w", pady=(10, 5))
        
        self.progress = ctk.CTkProgressBar(frame, width=350)
        self.progress.pack(pady=5)
        self.progress.set(0)
        
        self.progress_label = ctk.CTkLabel(frame, text="0%")
        self.progress_label.pack()
        
        self.speed_label = ctk.CTkLabel(frame, text="")
        self.speed_label.pack(pady=5)
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(pady=(10, 0))
        
        self.folder_btn = ctk.CTkButton(btn_frame, text="打开下载文件夹", width=120, command=self.open_folder)
        self.folder_btn.pack(side="left", padx=(0, 10))
        
        self.cancel_btn = ctk.CTkButton(btn_frame, text="取消下载", width=120, command=self.cancel_download)
        self.cancel_btn.pack(side="left")
        
        self.protocol("WM_DELETE_WINDOW", self.cancel_download)
    
    def start_download(self):
        threading.Thread(target=self.download_thread, daemon=True).start()
    
    def safe_after(self, func, *args):
        if self._alive:
            try:
                self.after(0, func, *args)
            except:
                pass
    
    def update_progress(self, percent, downloaded, total_size, speed):
        if not self._alive:
            return
        try:
            self.progress.set(percent / 100.0)
            self.progress_label.configure(text=f"{percent:.1f}%")
            self.speed_label.configure(
                text=f"已下载: {downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB  速度: {speed/1024:.0f}KB/s"
            )
        except:
            pass
    
    def download_thread(self):
        try:
            url = f"{self.base_url}/song/url/v1?id={self.song_id}&level=lossless"
            self.safe_after(lambda: self.log_callback(f"[下载] 请求API: {url}", "INFO"))
            
            response = requests.get(url, timeout=10)
            self.safe_after(lambda: self.log_callback(f"[下载] API状态码: {response.status_code}", "INFO"))
            
            data = response.json()
            self.safe_after(lambda: self.log_callback(f"[下载] API响应: {data}", "INFO"))
            
            if not data.get("data") or not data["data"][0].get("url"):
                error_msg = f"获取失败: 可能无版权 (code={data.get('code')}, msg={data.get('message')})"
                self.safe_after(lambda: self.status_label.configure(text="获取失败: 可能无版权"))
                self.safe_after(lambda: self.cancel_btn.configure(text="关闭"))
                self.safe_after(lambda: self.log_callback(f"[下载] {error_msg}", "ERROR"))
                return
            
            song_url = data["data"][0]["url"]
            song_size = data["data"][0].get("size", 0)
            song_br = data["data"][0].get("br", 0)
            song_type = data["data"][0].get("type", "")
            song_level = data["data"][0].get("level", "")
            
            self.safe_after(lambda: self.status_label.configure(text="正在下载..."))
            self.safe_after(lambda: self.log_callback(f"[下载] 获取成功 - 类型:{song_type} 码率:{song_br} 大小:{song_size/1024/1024:.2f}MB 等级:{song_level}", "INFO"))
            self.safe_after(lambda: self.log_callback(f"[下载] 下载链接: {song_url[:80]}...", "INFO"))
            
            timestamp = int(time.time())
            temp_name = f"temp_{timestamp}_{self.song_id}.mp3"
            self.temp_file = os.path.join(self.download_dir, temp_name)
            
            self.safe_after(lambda: self.log_callback(f"[下载] 开始下载文件到: {self.temp_file}", "INFO"))
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://music.163.com/'
            }
            response = requests.get(song_url, stream=True, timeout=120, headers=headers)
            self.safe_after(lambda: self.log_callback(f"[下载] 文件响应状态码: {response.status_code}", "INFO"))
            self.safe_after(lambda: self.log_callback(f"[下载] Content-Type: {response.headers.get('content-type', 'N/A')}", "INFO"))
            
            total_size = int(response.headers.get('content-length', 0))
            self.safe_after(lambda: self.log_callback(f"[下载] 文件大小: {total_size/1024/1024:.2f}MB (Content-Length)", "INFO"))
            
            downloaded = 0
            start_time = time.time()
            last_update = 0
            
            with open(self.temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancelled:
                        break
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        current_time = time.time()
                        if total_size > 0 and (current_time - last_update > 0.2 or downloaded >= total_size):
                            last_update = current_time
                            percent = min((downloaded / total_size) * 100, 100)
                            elapsed = current_time - start_time
                            speed = downloaded / elapsed if elapsed > 0 else 0
                            self.safe_after(self.update_progress, percent, downloaded, total_size, speed)
            
            if self.cancelled:
                if self.temp_file and os.path.exists(self.temp_file):
                    try:
                        os.remove(self.temp_file)
                    except:
                        pass
                self.safe_after(lambda: self.log_callback(f"[下载] 已取消: {self.song_name}", "WARNING"))
                return
            
            if not os.path.exists(self.temp_file):
                self.safe_after(lambda: self.status_label.configure(text="下载失败: 文件未创建"))
                self.safe_after(lambda: self.cancel_btn.configure(text="关闭"))
                self.safe_after(lambda: self.log_callback(f"[下载] 失败: 临时文件未创建", "ERROR"))
                return
            
            safe_song_name = sanitize_filename(self.song_name)
            safe_artist_name = sanitize_filename(self.artist_name) if self.artist_name else ""
            
            if self.name_format == "artist-song" and safe_artist_name:
                file_name = f"{safe_artist_name}-{safe_song_name}"
            else:
                if safe_artist_name:
                    file_name = f"{safe_song_name}-{safe_artist_name}"
                else:
                    file_name = safe_song_name
            
            self.final_file = os.path.join(self.download_dir, f"{file_name}.mp3")
            
            if os.path.exists(self.final_file):
                os.remove(self.final_file)
            
            os.rename(self.temp_file, self.final_file)
            file_size = os.path.getsize(self.final_file) if os.path.exists(self.final_file) else 0
            
            self.safe_after(lambda: self.status_label.configure(text="下载完成!"))
            self.safe_after(lambda: self.progress.set(1.0))
            self.safe_after(lambda: self.progress_label.configure(text="100%"))
            self.safe_after(lambda: self.cancel_btn.configure(text="关闭"))
            self.safe_after(lambda: self.log_callback(f"[下载] 完成: {self.song_name} - 文件大小:{file_size/1024/1024:.2f}MB 路径:{self.final_file}", "INFO"))
            
            if self.auto_close:
                self.safe_after(lambda: self.after(1500, self.close_window))
            
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            self.safe_after(lambda: self.status_label.configure(text=f"下载失败: {str(e)}"))
            self.safe_after(lambda: self.cancel_btn.configure(text="关闭"))
            self.safe_after(lambda: self.log_callback(f"[下载] 异常: {error_detail}", "ERROR"))
    
    def cancel_download(self):
        if self.cancel_btn.cget("text") == "关闭":
            self._alive = False
            self.destroy()
            return
        
        self.cancelled = True
        self.safe_after(lambda: self.status_label.configure(text="已取消"))
        self.safe_after(lambda: self.cancel_btn.configure(text="关闭"))
        
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass
        
        self.log_callback(f"已取消下载: {self.song_name}", "WARNING")
    
    def close_window(self):
        self._alive = False
        self.destroy()
    
    def open_folder(self):
        webbrowser.open(self.download_dir)


class BatchDownloadWindow(ctk.CTkToplevel):
    def __init__(self, parent, songs, base_url, log_callback, name_format="song-artist", auto_close=False):
        super().__init__(parent)
        self.songs = songs
        self.base_url = base_url
        self.log_callback = log_callback
        self.name_format = name_format
        self.auto_close = auto_close
        self.cancelled = False
        self.download_dir = get_download_dir()
        self._alive = True
        self.current_index = 0
        self.total_count = len(songs)
        self.completed_count = 0
        self.failed_count = 0
        self.temp_file = None
        self.final_file = None
        
        self.title("批量下载")
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        window_width = 550
        window_height = 380
        
        window_width = min(window_width, int(screen_width * 0.4))
        window_height = min(window_height, int(screen_height * 0.4))
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        
        self.update_idletasks()
        actual_width = self.winfo_width()
        actual_height = self.winfo_height()
        actual_x = (screen_width - actual_width) // 2
        actual_y = (screen_height - actual_height) // 2
        self.geometry(f"+{actual_x}+{actual_y}")
        
        self.setup_ui()
        
        self.update_idletasks()
        self.after(200, self.start_batch_download)
    
    def setup_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.count_label = ctk.CTkLabel(frame, text=f"下载进度: 0/{self.total_count}", font=("", 14, "bold"))
        self.count_label.pack(anchor="w")
        
        self.song_label = ctk.CTkLabel(frame, text="当前歌曲: 准备中...", font=("", 12))
        self.song_label.pack(anchor="w", pady=(10, 5))
        
        self.status_label = ctk.CTkLabel(frame, text="正在获取下载链接...")
        self.status_label.pack(anchor="w", pady=(5, 5))
        
        self.progress = ctk.CTkProgressBar(frame, width=350)
        self.progress.pack(pady=5)
        self.progress.set(0)
        
        self.progress_label = ctk.CTkLabel(frame, text="0%")
        self.progress_label.pack()
        
        self.speed_label = ctk.CTkLabel(frame, text="")
        self.speed_label.pack(pady=5)
        
        self.summary_label = ctk.CTkLabel(frame, text="")
        self.summary_label.pack(anchor="w", pady=(5, 0))
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(pady=(10, 0))
        
        self.folder_btn = ctk.CTkButton(btn_frame, text="打开下载文件夹", width=120, command=self.open_folder)
        self.folder_btn.pack(side="left", padx=(0, 10))
        
        self.cancel_btn = ctk.CTkButton(btn_frame, text="取消下载", width=120, command=self.cancel_download)
        self.cancel_btn.pack(side="left")
        
        self.protocol("WM_DELETE_WINDOW", self.cancel_download)
    
    def start_batch_download(self):
        threading.Thread(target=self.batch_download_thread, daemon=True).start()
    
    def safe_after(self, func, *args):
        if self._alive:
            try:
                self.after(0, func, *args)
            except:
                pass
    
    def update_progress(self, percent, downloaded, total_size, speed):
        if not self._alive:
            return
        try:
            self.progress.set(percent / 100.0)
            self.progress_label.configure(text=f"{percent:.1f}%")
            self.speed_label.configure(
                text=f"已下载: {downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB  速度: {speed/1024:.0f}KB/s"
            )
        except:
            pass
    
    def update_count_label(self):
        remaining = self.total_count - self.completed_count - self.failed_count
        self.count_label.configure(text=f"下载进度: {self.completed_count}/{self.total_count} (剩余: {remaining})")
        self.summary_label.configure(text=f"已完成: {self.completed_count}  失败: {self.failed_count}")
    
    def batch_download_thread(self):
        for i, song in enumerate(self.songs):
            if self.cancelled:
                break
            
            self.current_index = i
            song_id = song.get("id")
            song_name = song.get("name", "未知歌曲")
            artist_name = song.get("artist_name", "")
            
            self.safe_after(lambda name=song_name: self.song_label.configure(text=f"当前歌曲: {name}"))
            self.safe_after(lambda: self.status_label.configure(text="正在获取下载链接..."))
            self.safe_after(lambda: self.progress.set(0))
            self.safe_after(lambda: self.progress_label.configure(text="0%"))
            self.safe_after(lambda: self.speed_label.configure(text=""))
            self.safe_after(self.update_count_label)
            
            success = self.download_single_song(song_id, song_name, artist_name)
            
            if success:
                self.completed_count += 1
            else:
                self.failed_count += 1
            
            self.safe_after(self.update_count_label)
        
        if not self.cancelled:
            self.safe_after(lambda: self.song_label.configure(text="批量下载完成!"))
            self.safe_after(lambda: self.status_label.configure(text=f"成功: {self.completed_count}  失败: {self.failed_count}"))
            self.safe_after(lambda: self.cancel_btn.configure(text="关闭"))
            self.safe_after(lambda: self.log_callback(f"[批量下载] 完成: 成功{self.completed_count}首, 失败{self.failed_count}首", "INFO"))
            
            if self.auto_close and self.failed_count == 0:
                self.safe_after(lambda: self.after(1500, self.close_window))
        else:
            self.safe_after(lambda: self.status_label.configure(text="已取消"))
            self.safe_after(lambda: self.cancel_btn.configure(text="关闭"))
    
    def download_single_song(self, song_id, song_name, artist_name):
        try:
            url = f"{self.base_url}/song/url/v1?id={song_id}&level=lossless"
            self.safe_after(lambda: self.log_callback(f"[下载] 请求API: {url}", "INFO"))
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if not data.get("data") or not data["data"][0].get("url"):
                self.safe_after(lambda: self.status_label.configure(text="获取失败: 可能无版权"))
                self.safe_after(lambda: self.log_callback(f"[下载] {song_name} - 获取失败: 可能无版权", "ERROR"))
                return False
            
            song_url = data["data"][0]["url"]
            song_size = data["data"][0].get("size", 0)
            
            self.safe_after(lambda: self.status_label.configure(text="正在下载..."))
            self.safe_after(lambda: self.log_callback(f"[下载] 开始下载: {song_name}", "INFO"))
            
            timestamp = int(time.time())
            temp_name = f"temp_{timestamp}_{song_id}.mp3"
            self.temp_file = os.path.join(self.download_dir, temp_name)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://music.163.com/'
            }
            response = requests.get(song_url, stream=True, timeout=120, headers=headers)
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            start_time = time.time()
            last_update = 0
            
            with open(self.temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancelled:
                        break
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        current_time = time.time()
                        if total_size > 0 and (current_time - last_update > 0.2 or downloaded >= total_size):
                            last_update = current_time
                            percent = min((downloaded / total_size) * 100, 100)
                            elapsed = current_time - start_time
                            speed = downloaded / elapsed if elapsed > 0 else 0
                            self.safe_after(self.update_progress, percent, downloaded, total_size, speed)
            
            if self.cancelled:
                if self.temp_file and os.path.exists(self.temp_file):
                    try:
                        os.remove(self.temp_file)
                    except:
                        pass
                return False
            
            if not os.path.exists(self.temp_file):
                self.safe_after(lambda: self.status_label.configure(text="下载失败: 文件未创建"))
                return False
            
            safe_song_name = sanitize_filename(song_name)
            safe_artist_name = sanitize_filename(artist_name) if artist_name else ""
            
            if self.name_format == "artist-song" and safe_artist_name:
                file_name = f"{safe_artist_name}-{safe_song_name}"
            else:
                if safe_artist_name:
                    file_name = f"{safe_song_name}-{safe_artist_name}"
                else:
                    file_name = safe_song_name
            
            self.final_file = os.path.join(self.download_dir, f"{file_name}.mp3")
            
            if os.path.exists(self.final_file):
                os.remove(self.final_file)
            
            os.rename(self.temp_file, self.final_file)
            file_size = os.path.getsize(self.final_file) if os.path.exists(self.final_file) else 0
            
            self.safe_after(lambda: self.status_label.configure(text="下载完成!"))
            self.safe_after(lambda: self.progress.set(1.0))
            self.safe_after(lambda: self.progress_label.configure(text="100%"))
            self.safe_after(lambda: self.log_callback(f"[下载] 完成: {song_name} - {file_size/1024/1024:.2f}MB", "INFO"))
            
            return True
            
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            self.safe_after(lambda: self.status_label.configure(text=f"下载失败: {str(e)}"))
            self.safe_after(lambda: self.log_callback(f"[下载] 异常: {song_name} - {error_detail}", "ERROR"))
            return False
    
    def cancel_download(self):
        if self.cancel_btn.cget("text") == "关闭":
            self._alive = False
            self.destroy()
            return
        
        self.cancelled = True
        self.safe_after(lambda: self.status_label.configure(text="已取消"))
        self.safe_after(lambda: self.cancel_btn.configure(text="关闭"))
        
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass
        
        self.log_callback(f"已取消批量下载", "WARNING")
    
    def close_window(self):
        self._alive = False
        self.destroy()
    
    def open_folder(self):
        webbrowser.open(self.download_dir)


class MusicDownloaderApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Cloud Music Download V1.0.0")
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        base_width = 1200
        base_height = 800
        
        max_width = min(base_width, int(screen_width * 0.6))
        max_height = min(base_height, int(screen_height * 0.6))
        
        min_width = 900
        min_height = 600
        window_width = max(max_width, min_width)
        window_height = max(max_height, min_height)
        
        window_width = min(window_width, 1400)
        window_height = min(window_height, 900)
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(min_width, min_height)
        self.root.resizable(True, True)
        
        self.root.update_idletasks()
        
        actual_width = self.root.winfo_width()
        actual_height = self.root.winfo_height()
        actual_x = (screen_width - actual_width) // 2
        actual_y = (screen_height - actual_height) // 2
        self.root.geometry(f"+{actual_x}+{actual_y}")
        
        self.all_songs = []
        self.api_process = None
        self.api_available = False
        self.login_cookie = None
        self.login_session = None
        self.user_name = None
        self.user_id = None
        
        self.playlist_offset = 0
        self.playlist_limit = 50
        self.current_playlist_id = None
        
        self.search_offset = 0
        self.search_limit = 30
        self.search_keyword = ""
        
        self.config = load_config()
        self.BASE_URL = self.config.get("api_url", "http://localhost:3000")
        
        self.setup_ui()
        self.bind_events()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.root.update_idletasks()
        
        self.root.after(50, self.load_saved_user_data)
        self.root.after(100, self.try_start_api)
    
    def try_start_api(self):
        threading.Thread(target=self._check_and_start_api, daemon=True).start()
    
    def _check_and_start_api(self):
        if check_api_running():
            self.root.after(0, lambda: (self.log("API服务已在运行", "INFO"), setattr(self, 'api_available', True)))
            return
        
        api_path = self.config.get("api_path", "")
        if not api_path:
            self.root.after(0, lambda: (
                self.log("未配置本地API服务路径", "INFO"),
                self.log("如需使用本地API，请在设置中选择API服务目录", "INFO"),
            ))
            return
        
        resolved_api_path = resolve_path(api_path)
        if not os.path.exists(resolved_api_path):
            self.root.after(0, lambda: (
                self.log(f"API路径不存在: {resolved_api_path}", "ERROR"),
                self.log("请检查设置中的API服务路径配置", "ERROR"),
            ))
            return
        
        auto_start_api = self.config.get("auto_start_api", False)
        if not auto_start_api:
            self.root.after(0, lambda: (
                self.log("API服务未运行，自动启动已禁用", "WARNING"),
                self.log("如需自动启动，请在设置中启用「启动时自动启动本地API服务」", "WARNING"),
                self.log(f"当前API地址: {self.BASE_URL}", "INFO")
            ))
            return
        
        self.root.after(0, lambda: self.log("API服务未运行，正在尝试启动...", "INFO"))
        self._start_api_thread(resolved_api_path)
    
    def _start_api_thread(self, api_path):
        self.api_process = start_api_server(api_path)
        
        if not self.api_process:
            self.root.after(0, lambda: self.log("API服务启动失败：无法创建进程", "ERROR"))
            return
        
        pid = self.api_process.pid
        self.root.after(0, lambda: self.log(f"API进程已启动 (PID: {pid})", "INFO"))
        self.root.after(0, lambda: self.log("正在初始化API服务（首次启动可能需要1-2分钟）...", "INFO"))
        
        max_wait = 180
        for i in range(max_wait):
            time.sleep(1)
            
            poll_result = self.api_process.poll()
            if poll_result is not None:
                stdout, stderr = self.api_process.communicate()
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else ""
                stdout_msg = stdout.decode('utf-8', errors='ignore') if stdout else ""
                self.root.after(0, lambda msg=error_msg[:500]: self.log(f"API进程已退出，返回码: {poll_result}", "ERROR"))
                if error_msg:
                    self.root.after(0, lambda msg=error_msg[:500]: self.log(f"错误: {msg}", "ERROR"))
                self.api_process = None
                return
            
            if check_api_running():
                self.api_available = True
                self.root.after(0, lambda: self.log("API服务启动成功", "INFO"))
                return
        
        self.root.after(0, lambda: self.log("API服务启动超时，请检查配置", "ERROR"))
        if self.api_process:
            try:
                if os.name == 'nt':
                    self.api_process.terminate()
                else:
                    import signal
                    os.killpg(os.getpgid(self.api_process.pid), signal.SIGTERM)
            except:
                pass
            self.api_process = None
    
    def load_saved_user_data(self):
        user_data = load_user_data()
        if user_data:
            self.login_cookie = user_data.get("cookie")
            self.user_name = user_data.get("user_name")
            self.user_id = user_data.get("user_id")
            self.login_session = requests.Session()
            self.log(f"已加载用户: {self.user_name}", "INFO")
        else:
            self.log("未检测到登录信息，请先登录", "WARNING")
    
    def on_closing(self):
        auto_close_api = self.config.get("auto_close_api", True)
        if self.api_process and auto_close_api:
            try:
                if os.name == 'nt':
                    self.api_process.terminate()
                    try:
                        self.api_process.wait(timeout=5)
                    except:
                        self.api_process.kill()
                else:
                    import signal
                    os.killpg(os.getpgid(self.api_process.pid), signal.SIGTERM)
                    try:
                        self.api_process.wait(timeout=5)
                    except:
                        os.killpg(os.getpgid(self.api_process.pid), signal.SIGKILL)
            except:
                pass
        self.root.destroy()
    
    def setup_ui(self):
        self.setup_top_frame()
        self.setup_bottom_frame()
    
    def setup_top_frame(self):
        self.top_frame = ctk.CTkFrame(self.root)
        self.top_frame.pack(fill="x", side="top", padx=10, pady=10)
        
        self.settings_button = ctk.CTkButton(self.top_frame, text="设置", width=80)
        self.settings_button.pack(side="left", padx=(0, 10))
        
        self.music_search_button = ctk.CTkButton(self.top_frame, text="音乐搜索", width=80)
        self.music_search_button.pack(side="left", padx=(0, 10))
        
        self.playlist_button = ctk.CTkButton(self.top_frame, text="歌单列表", width=80)
        self.playlist_button.pack(side="left", padx=(0, 10))
        
        self.about_button = ctk.CTkButton(self.top_frame, text="关于", width=80, command=self.open_about)
        self.about_button.pack(side="left", padx=(0, 10))
        
        # 分隔线使用空Frame代替
        self.separator = ctk.CTkFrame(self.top_frame, width=2, height=20)
        
        self.search_label = ctk.CTkLabel(self.top_frame, text="音乐搜索:")
        self.search_entry = ctk.CTkEntry(self.top_frame, width=160)
        self.search_button = ctk.CTkButton(self.top_frame, text="搜索", width=60)
        self.download_button = ctk.CTkButton(self.top_frame, text="下载", width=60)
        
        self.enter_playlist_button = ctk.CTkButton(self.top_frame, text="进入歌单", width=80)
        
        self.prev_page_button = ctk.CTkButton(self.top_frame, text="上一页", width=60)
        self.next_page_button = ctk.CTkButton(self.top_frame, text="下一页", width=60)
        self.page_label = ctk.CTkLabel(self.top_frame, text="")
        self.download_playlist_button = ctk.CTkButton(self.top_frame, text="下载", width=60)
        
        self.show_search_controls()
    
    def setup_bottom_frame(self):
        self.bottom_frame = ctk.CTkFrame(self.root)
        self.bottom_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.search_page = ctk.CTkFrame(self.bottom_frame)
        self.playlist_page = ctk.CTkFrame(self.bottom_frame)
        self.playlist_detail_page = ctk.CTkFrame(self.bottom_frame)
        
        self.setup_search_page()
        self.setup_playlist_page()
        self.setup_playlist_detail_page()
        
        self.show_search_page()
    
    def setup_search_page(self):
        results_frame = ctk.CTkFrame(self.search_page)
        results_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)
        
        columns = ("序号", "歌曲名", "歌手")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=20, selectmode="extended")
        
        self.results_tree.heading("序号", text="序号")
        self.results_tree.heading("歌曲名", text="歌曲名")
        self.results_tree.heading("歌手", text="歌手")
        
        self.results_tree.column("序号", width=50, anchor="center")
        self.results_tree.column("歌曲名", width=200, anchor="w")
        self.results_tree.column("歌手", width=150, anchor="w")
        
        scrollbar_y = ctk.CTkScrollbar(results_frame, command=self.results_tree.yview)
        scrollbar_x = ctk.CTkScrollbar(results_frame, orientation="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        
        log_frame = ctk.CTkFrame(self.search_page)
        log_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.log_text = ctk.CTkTextbox(log_frame, width=280, height=20)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text.tag_config("INFO_HEADER", foreground="#0D47A1")
        self.log_text.tag_config("INFO_CONTENT", foreground="#42A5F5")
        self.log_text.tag_config("WARNING_HEADER", foreground="#E65100")
        self.log_text.tag_config("WARNING_CONTENT", foreground="#FFB74D")
        self.log_text.tag_config("ERROR_HEADER", foreground="#B71C1C")
        self.log_text.tag_config("ERROR_CONTENT", foreground="#EF5350")
    
    def setup_playlist_page(self):
        playlist_frame = ctk.CTkFrame(self.playlist_page)
        playlist_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        columns = ("序号", "歌单名", "歌曲数", "歌单ID")
        self.playlist_tree = ttk.Treeview(playlist_frame, columns=columns, show="headings", height=20)
        
        self.playlist_tree.heading("序号", text="序号")
        self.playlist_tree.heading("歌单名", text="歌单名")
        self.playlist_tree.heading("歌曲数", text="歌曲数")
        self.playlist_tree.heading("歌单ID", text="歌单ID")
        
        self.playlist_tree.column("序号", width=50, anchor="center")
        self.playlist_tree.column("歌单名", width=300, anchor="w")
        self.playlist_tree.column("歌曲数", width=80, anchor="center")
        self.playlist_tree.column("歌单ID", width=150, anchor="center")
        
        scrollbar_y = ctk.CTkScrollbar(playlist_frame, command=self.playlist_tree.yview)
        self.playlist_tree.configure(yscrollcommand=scrollbar_y.set)
        
        self.playlist_tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        
        log_frame2 = ctk.CTkFrame(self.playlist_page)
        log_frame2.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.log_text2 = ctk.CTkTextbox(log_frame2, width=280, height=20)
        self.log_text2.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text2.tag_config("INFO_HEADER", foreground="#0D47A1")
        self.log_text2.tag_config("INFO_CONTENT", foreground="#42A5F5")
        self.log_text2.tag_config("WARNING_HEADER", foreground="#E65100")
        self.log_text2.tag_config("WARNING_CONTENT", foreground="#FFB74D")
        self.log_text2.tag_config("ERROR_HEADER", foreground="#B71C1C")
        self.log_text2.tag_config("ERROR_CONTENT", foreground="#EF5350")
    
    def setup_playlist_detail_page(self):
        detail_frame = ctk.CTkFrame(self.playlist_detail_page)
        detail_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        columns = ("序号", "歌曲名", "歌手", "歌曲ID")
        self.playlist_detail_tree = ttk.Treeview(detail_frame, columns=columns, show="headings", height=20, selectmode="extended")
        
        self.playlist_detail_tree.heading("序号", text="序号")
        self.playlist_detail_tree.heading("歌曲名", text="歌曲名")
        self.playlist_detail_tree.heading("歌手", text="歌手")
        self.playlist_detail_tree.heading("歌曲ID", text="歌曲ID")
        
        self.playlist_detail_tree.column("序号", width=50, anchor="center")
        self.playlist_detail_tree.column("歌曲名", width=300, anchor="w")
        self.playlist_detail_tree.column("歌手", width=150, anchor="w")
        self.playlist_detail_tree.column("歌曲ID", width=150, anchor="center")
        
        scrollbar_y = ctk.CTkScrollbar(detail_frame, command=self.playlist_detail_tree.yview)
        self.playlist_detail_tree.configure(yscrollcommand=scrollbar_y.set)
        
        self.playlist_detail_tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        
        log_frame3 = ctk.CTkFrame(self.playlist_detail_page)
        log_frame3.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.log_text3 = ctk.CTkTextbox(log_frame3, width=280, height=20)
        self.log_text3.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text3.tag_config("INFO_HEADER", foreground="#0D47A1")
        self.log_text3.tag_config("INFO_CONTENT", foreground="#42A5F5")
        self.log_text3.tag_config("WARNING_HEADER", foreground="#E65100")
        self.log_text3.tag_config("WARNING_CONTENT", foreground="#FFB74D")
        self.log_text3.tag_config("ERROR_HEADER", foreground="#B71C1C")
        self.log_text3.tag_config("ERROR_CONTENT", foreground="#EF5350")
    
    def show_search_controls(self):
        self.separator.pack(side="left", fill="y", padx=15)
        self.search_label.pack(side="left", padx=(0, 5))
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_button.pack(side="left", padx=(0, 10))
        self.download_button.pack(side="left")
        self.prev_page_button.configure(command=self.search_prev_page)
        self.prev_page_button.pack(side="left", padx=(10, 5))
        self.page_label.configure(text=f"第 {(self.search_offset // self.search_limit) + 1} 页")
        self.page_label.pack(side="left", padx=(0, 5))
        self.next_page_button.configure(command=self.search_next_page)
        self.next_page_button.pack(side="left")
        self.enter_playlist_button.pack_forget()
        self.download_playlist_button.pack_forget()
    
    def show_playlist_controls(self):
        self.separator.pack_forget()
        self.search_label.pack_forget()
        self.search_entry.pack_forget()
        self.search_button.pack_forget()
        self.download_button.pack_forget()
        self.enter_playlist_button.configure(text="进入歌单", command=self.on_enter_playlist)
        self.enter_playlist_button.pack(side="left", padx=(0, 10))
        self.prev_page_button.pack_forget()
        self.page_label.pack_forget()
        self.next_page_button.pack_forget()
        self.download_playlist_button.pack_forget()
    
    def show_playlist_detail_controls(self):
        self.separator.pack_forget()
        self.search_label.pack_forget()
        self.search_entry.pack_forget()
        self.search_button.pack_forget()
        self.download_button.pack_forget()
        self.enter_playlist_button.configure(text="返回", command=self.show_playlist_page)
        self.enter_playlist_button.pack(side="left", padx=(0, 10))
        self.prev_page_button.configure(command=self.prev_page)
        self.prev_page_button.pack(side="left", padx=(0, 5))
        self.page_label.pack(side="left", padx=(0, 5))
        self.next_page_button.configure(command=self.next_page)
        self.next_page_button.pack(side="left", padx=(0, 10))
        self.download_playlist_button.pack(side="left")
    
    def show_search_page(self):
        self.playlist_page.pack_forget()
        self.playlist_detail_page.pack_forget()
        self.search_page.pack(fill="both", expand=True)
        self.show_search_controls()
    
    def show_playlist_page(self):
        self.search_page.pack_forget()
        self.playlist_detail_page.pack_forget()
        self.playlist_page.pack(fill="both", expand=True)
        self.show_playlist_controls()
        self.get_playlist()
    
    def show_playlist_detail_page(self, playlist_id):
        self.search_page.pack_forget()
        self.playlist_page.pack_forget()
        self.playlist_detail_page.pack(fill="both", expand=True)
        self.show_playlist_detail_controls()
        self.playlist_offset = 0
        self.get_playlist_tracks(playlist_id, self.playlist_offset)
    
    def on_enter_playlist(self):
        selected = self.playlist_tree.selection()
        if not selected:
            self.log2("请先选择一个歌单", "WARNING")
            return
        
        item = selected[0]
        values = self.playlist_tree.item(item, "values")
        playlist_id = values[3]
        self.current_playlist_id = playlist_id
        self.show_playlist_detail_page(playlist_id)
    
    def bind_events(self):
        self.search_button.configure(command=self.on_search)
        self.search_entry.bind("<Return>", lambda e: self.on_search())
        self.download_button.configure(command=self.on_download)
        self.settings_button.configure(command=self.open_settings)
        self.music_search_button.configure(command=self.show_search_page)
        self.playlist_button.configure(command=self.show_playlist_page)
        self.download_playlist_button.configure(command=self.on_download_playlist_song)
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        
        header_tag = f"{level}_HEADER"
        content_tag = f"{level}_CONTENT"
        header = f"[{timestamp}] [{level}] "
        self.log_text.insert("end", header, header_tag)
        self.log_text.insert("end", f"{message}\n", content_tag)
        
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def on_search(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("提示", "请输入搜索内容")
            return
        
        self.search_keyword = keyword
        self.search_offset = 0
        self.search_button.configure(state="disabled")
        self.log(f"开始搜索: {keyword}", "INFO")
        
        threading.Thread(target=self.search_music, args=(keyword, self.search_offset), daemon=True).start()
    
    def search_music(self, keyword, offset=0):
        try:
            url = f"{self.BASE_URL}/search?keywords={keyword}&limit={self.search_limit}&offset={offset}"
            self.root.after(0, self.log, f"正在请求API: {url}", "INFO")
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get("result") and data["result"].get("songs"):
                self.all_songs = data["result"]["songs"]
                self.root.after(0, self.update_results, offset)
                self.root.after(0, self.log, f"搜索成功，找到 {len(self.all_songs)} 首歌曲", "INFO")
                self.root.after(0, self.update_search_page_label)
            else:
                self.root.after(0, self.log, "未找到相关歌曲", "WARNING")
                self.root.after(0, lambda: self.clear_results())
        except Exception as e:
            self.root.after(0, self.log, f"搜索失败: {str(e)}", "ERROR")
        finally:
            self.root.after(0, lambda: self.search_button.configure(state="normal"))
    
    def update_search_page_label(self):
        self.page_label.configure(text=f"第 {(self.search_offset // self.search_limit) + 1} 页")
    
    def search_prev_page(self):
        if self.search_offset >= self.search_limit:
            self.search_offset -= self.search_limit
            self.search_button.configure(state="disabled")
            threading.Thread(target=self.search_music, args=(self.search_keyword, self.search_offset), daemon=True).start()
    
    def search_next_page(self):
        self.search_offset += self.search_limit
        self.search_button.configure(state="disabled")
        threading.Thread(target=self.search_music, args=(self.search_keyword, self.search_offset), daemon=True).start()
    
    def update_results(self, offset=0):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        for i, song in enumerate(self.all_songs, 1):
            artist_name = ", ".join([a["name"] for a in song.get("artists", [])])
            self.results_tree.insert("", "end", values=(offset + i, song["name"], artist_name))
    
    def clear_results(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.all_songs = []
    
    def on_download(self):
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要下载的歌曲")
            return
        
        songs_to_download = []
        for item in selected:
            index = self.results_tree.index(item)
            if index < len(self.all_songs):
                song = self.all_songs[index]
                song_id = song["id"]
                song_name = song["name"]
                artists = song.get("artists", [])
                artist_name = ", ".join([a["name"] for a in artists]) if artists else ""
                songs_to_download.append({
                    "id": song_id,
                    "name": song_name,
                    "artist_name": artist_name
                })
        
        if not songs_to_download:
            return
        
        name_format = self.config.get("file_name_format", "song-artist")
        auto_close = self.config.get("auto_close_download_window", False)
        
        if len(songs_to_download) == 1:
            song = songs_to_download[0]
            self.log(f"创建下载任务: {song['name']}(按住ctrl可多选下载)", "INFO")
            DownloadWindow(self.root, song["name"], song["id"], self.BASE_URL, self.log, song["artist_name"], name_format, auto_close)
        else:
            self.log(f"创建批量下载任务: {len(songs_to_download)}首歌曲", "INFO")
            BatchDownloadWindow(self.root, songs_to_download, self.BASE_URL, self.log, name_format, auto_close)

    def yyy_login(self, qr_label):
        self.log("点击登录按钮", "INFO")
        self.login_session = requests.Session()
        
        get_login_key_json = f"{self.BASE_URL}/login/qr/key"
        login_key_response = self.login_session.get(get_login_key_json)
        login_key = login_key_response.json()['data']['unikey']
        self.log(f"获取登录key: {login_key}", "INFO")
        get_login_QRcode_json = f"{self.BASE_URL}/login/qr/create?key={login_key}&qrimg=true"
        get_login_QRcode_jsons = self.login_session.get(get_login_QRcode_json)
        self.log(f"获取json:{get_login_QRcode_jsons.json()}", "INFO")
        get_login_QRcode_base64 = get_login_QRcode_jsons.json()['data']['qrimg']
        self.log(f"获取二维码base64成功", "INFO")
        
        self.show_qr_image(qr_label, get_login_QRcode_base64)
        
        self.login_check_thread = threading.Thread(target=self.check_login_status, args=(login_key,), daemon=True)
        self.login_check_thread.start()
    
    def get_user_data(self):
        self.log("正在获取用户信息...", "INFO")
        headers = {
            "Cookie": self.login_cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        all_user_data_url = f"{self.BASE_URL}/user/account"
        try:
            response = self.login_session.get(all_user_data_url, timeout=10, headers=headers)
            all_user_data = response.json()
            
            if all_user_data.get('code') == 200:
                profile = all_user_data.get('profile', {})
                self.user_id = profile.get('userId')
                self.user_name = profile.get('nickname')
                
                self.log(f"获取用户昵称: {self.user_name}", "INFO")
                self.log(f"获取用户UID: {self.user_id}", "INFO")
                
                save_user_data(self.login_cookie, self.user_name, self.user_id)
                self.log("用户数据已保存", "INFO")
                
            else:
                self.log(f"无法获取用户信息，状态码: {all_user_data.get('code')}", "ERROR")
        except Exception as e:
            self.log(f"请求用户信息异常: {str(e)}", "ERROR")

    def get_playlist(self):
        if not self.user_id:
            self.log2("错误：未找到用户UID，请重新登录", "ERROR")
            return
        
        get_playlist_url = f"{self.BASE_URL}/user/playlist?uid={self.user_id}"
        
        try:
            self.log2("正在拉取歌单...", "INFO")
            headers = {"Cookie": self.login_cookie}
            response = self.login_session.get(get_playlist_url, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("code") == 200:
                playlists = data.get("playlist", [])
                self.log2(f"成功获取 {len(playlists)} 个歌单", "INFO")
                
                for item in self.playlist_tree.get_children():
                    self.playlist_tree.delete(item)
                
                for i, pl in enumerate(playlists, 1):
                    pl_name = pl.get('name')
                    pl_id = pl.get('id')
                    track_count = pl.get('trackCount', 0)
                    
                    self.playlist_tree.insert("", "end", values=(i, pl_name, track_count, pl_id))
            else:
                self.log2(f"获取歌单失败，状态码: {data.get('code')}", "ERROR")
        except Exception as e:
            self.log2(f"请求歌单异常: {str(e)}", "ERROR")

    def log2(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text2.configure(state="normal")
        
        header_tag = f"{level}_HEADER"
        content_tag = f"{level}_CONTENT"
        header = f"[{timestamp}] [{level}] "
        self.log_text2.insert("end", header, header_tag)
        self.log_text2.insert("end", f"{message}\n", content_tag)
        
        self.log_text2.see("end")
        self.log_text2.configure(state="disabled")
    
    def log3(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text3.configure(state="normal")
        
        header_tag = f"{level}_HEADER"
        content_tag = f"{level}_CONTENT"
        header = f"[{timestamp}] [{level}] "
        self.log_text3.insert("end", header, header_tag)
        self.log_text3.insert("end", f"{message}\n", content_tag)
        
        self.log_text3.see("end")
        self.log_text3.configure(state="disabled")
    
    def get_playlist_tracks(self, playlist_id, offset=0):
        get_tracks_url = f"{self.BASE_URL}/playlist/track/all?id={playlist_id}&limit={self.playlist_limit}&offset={offset}"
        
        try:
            self.log3(f"正在获取歌单歌曲 (offset={offset})...", "INFO")
            headers = {"Cookie": self.login_cookie}
            response = self.login_session.get(get_tracks_url, headers=headers, timeout=30)
            data = response.json()
            
            if data.get("code") == 200:
                songs = data.get("songs", [])
                self.log3(f"成功获取 {len(songs)} 首歌曲", "INFO")
                
                for item in self.playlist_detail_tree.get_children():
                    self.playlist_detail_tree.delete(item)
                
                for i, song in enumerate(songs, 1):
                    song_name = song.get('name')
                    song_id = song.get('id')
                    artists = song.get('ar', [])
                    artist_name = ", ".join([a.get('name', '') for a in artists])
                    
                    self.playlist_detail_tree.insert("", "end", values=(offset + i, song_name, artist_name, song_id))
                
                page_num = (offset // self.playlist_limit) + 1
                self.page_label.configure(text=f"第 {page_num} 页")
            else:
                self.log3(f"获取歌曲失败，状态码: {data.get('code')}", "ERROR")
        except Exception as e:
            self.log3(f"请求歌曲异常: {str(e)}", "ERROR")
    
    def prev_page(self):
        if self.playlist_offset >= self.playlist_limit:
            self.playlist_offset -= self.playlist_limit
            self.get_playlist_tracks(self.current_playlist_id, self.playlist_offset)
    
    def next_page(self):
        self.playlist_offset += self.playlist_limit
        self.get_playlist_tracks(self.current_playlist_id, self.playlist_offset)
    
    def on_download_playlist_song(self):
        selected = self.playlist_detail_tree.selection()
        if not selected:
            self.log3("请先选择要下载的歌曲", "WARNING")
            return
        
        songs_to_download = []
        for item in selected:
            values = self.playlist_detail_tree.item(item, "values")
            song_id = values[3]
            song_name = values[1]
            artist_name = values[2] if len(values) > 2 else ""
            songs_to_download.append({
                "id": song_id,
                "name": song_name,
                "artist_name": artist_name
            })
        
        if not songs_to_download:
            return
        
        name_format = self.config.get("file_name_format", "song-artist")
        auto_close = self.config.get("auto_close_download_window", False)
        
        if len(songs_to_download) == 1:
            song = songs_to_download[0]
            self.log3(f"创建下载任务: {song['name']}", "INFO")
            DownloadWindow(self.root, song["name"], song["id"], self.BASE_URL, self.log3, song["artist_name"], name_format, auto_close)
        else:
            self.log3(f"创建批量下载任务: {len(songs_to_download)}首歌曲", "INFO")
            BatchDownloadWindow(self.root, songs_to_download, self.BASE_URL, self.log3, name_format, auto_close)

    def check_login_status(self, unikey):
            shown_802 = False
            shown_801 = False
            while True:
                try:
                    time.sleep(1)
                    check_url = f"{self.BASE_URL}/login/qr/check?key={unikey}"
                    response = self.login_session.get(check_url, timeout=10)
                    data = response.json()
                    code = data.get('code')
                    
                    if code == 800:
                        self.root.after(0, self.log, "二维码已过期，请重新获取", "WARNING")
                        break
                    elif code == 801:
                        if not shown_801:
                            shown_801 = True
                            self.root.after(0, self.log, "等待扫码", "INFO")
                    elif code == 802:
                        if not shown_802:
                            self.root.after(0, self.log, "已扫码，请在手机上确认", "WARNING")
                            shown_802 = True
                    elif code == 803:
                        raw_cookie = data.get('cookie', '')
                        
                        cookie_dict = {}
                        exclude_keys = {'Path', 'Expires', 'Max-Age', 'Domain', 'SameSite', 'HTTPOnly', 'Secure'}
                        
                        parts = raw_cookie.replace(';;', ';').split(';')
                        for part in parts:
                            if '=' in part:
                                k, v = part.strip().split('=', 1)
                                if k not in exclude_keys and v:
                                    cookie_dict[k] = v
                        
                        self.login_cookie = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])

                        self.root.after(0, self.log, "登录成功！", "INFO")
                        self.root.after(0, self.log, f"Cookie已提取", "INFO")
                        self.root.after(0, self.get_user_data)
                        break
                    else:
                        self.root.after(0, self.log, f"未知状态码: {code}", "INFO")
                except Exception as e:
                    self.root.after(0, self.log, f"检查登录状态失败: {str(e)}", "ERROR")
                    break
    
    def show_qr_image(self, qr_label, base64_data):
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]
        
        img_bytes = base64.b64decode(base64_data)
        img_io = io.BytesIO(img_bytes)
        img_pil = Image.open(img_io)
        
        img_tk = ImageTk.PhotoImage(img_pil)
        
        qr_label.configure(image=img_tk)
        qr_label.image = img_tk

    def open_about(self):
        about_window = ctk.CTkToplevel(self.root)
        about_window.title("关于")
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        window_width = 500
        window_height = 450
        
        window_width = min(window_width, int(screen_width * 0.5))
        window_height = min(window_height, int(screen_height * 0.5))
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        about_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        about_window.update_idletasks()
        actual_width = about_window.winfo_width()
        actual_height = about_window.winfo_height()
        actual_x = (screen_width - actual_width) // 2
        actual_y = (screen_height - actual_height) // 2
        about_window.geometry(f"+{actual_x}+{actual_y}")
        
        version_label = ctk.CTkLabel(about_window, text="关于Cloud Music DownloadV1.0.0", font=("", 20))
        version_label.pack(pady=(20, 15))
        
        text_widget = ctk.CTkTextbox(about_window, wrap="word")
        text_widget.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        about_text = """
本软件由 @墨白星耀 开发并开源于 GitHub 的开源程序
本软件基于 GitHub 开源项目 NeteaseCloudMusicApiEnhanced/api-enhanced (项目仓库: https://github.com/NeteaseCloudMusicApiEnhanced/api-enhanced)，使用 Python 开发的 GUI 界面音乐下载程序

封面来源：Pixiv @すいそう (作品 PID: 137922433)

本软件完全免费，禁止商用、倒卖及二次分发
本软件仅供学习交流使用，使用本软件造成的一切后果由用户自行承担

——————— 使用教程 ———————

1. 在本地或云端部署 NeteaseCloudMusicApiEnhanced/api-enhanced
   部署教程请前往：https://github.com/NeteaseCloudMusicApiEnhanced/api-enhanced 查看

2. 部署完成后：
   云端 Docker 部署：在设置中填写部署的网址
   本地部署：设置 API 服务路径为 NeteaseCloudMusicApiEnhanced/api-enhanced 项目根目录，
API 地址填写 http://localhost:3000

3. 完成设置后，程序将自动检测并运行
"""
        
        text_widget.insert("1.0", about_text)
        text_widget.configure(state="disabled")
        
        close_button = ctk.CTkButton(about_window, text="关闭", width=80, command=about_window.destroy)
        close_button.pack(pady=(0, 20))

    def open_settings(self):
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("设置")
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        window_width = 600
        window_height = 800
        
        window_width = min(window_width, int(screen_width * 0.5))
        window_height = min(window_height, int(screen_height * 0.6))
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        settings_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        settings_window.update_idletasks()
        actual_width = settings_window.winfo_width()
        actual_height = settings_window.winfo_height()
        actual_x = (screen_width - actual_width) // 2
        actual_y = (screen_height - actual_height) // 2
        settings_window.geometry(f"+{actual_x}+{actual_y}")
        
        frame = ctk.CTkFrame(settings_window)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="API服务路径:").grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        api_path_frame = ctk.CTkFrame(frame)
        api_path_frame.grid(row=0, column=1, pady=(0, 10), padx=(10, 0), sticky="w")
        
        current_api_path = self.config.get("api_path", "")
        display_api_path = resolve_path(current_api_path) if current_api_path else "未选择"
        api_path_var = ctk.StringVar(value=display_api_path)
        api_path_entry = ctk.CTkEntry(api_path_frame, width=240)
        api_path_entry.pack(side="left", padx=(0, 5))
        api_path_entry.insert(0, display_api_path)
        api_path_entry.configure(state="readonly")
        
        def browse_api_path():
            initial_dir = resolve_path(current_api_path) if current_api_path else get_app_dir()
            selected_dir = filedialog.askdirectory(initialdir=initial_dir, title="选择API服务目录")
            if selected_dir:
                app_js = os.path.join(selected_dir, "app.js")
                if not os.path.exists(app_js):
                    messagebox.showwarning("提示", "所选目录不是有效的API服务目录\n请选择包含 app.js 的目录")
                    return
                api_path_var.set(selected_dir)
                api_path_entry.configure(state="normal")
                api_path_entry.delete(0, "end")
                api_path_entry.insert(0, selected_dir)
                api_path_entry.configure(state="readonly")
                update_api_settings_visibility(True)
        
        def clear_api_path():
            api_path_var.set("")
            api_path_entry.configure(state="normal")
            api_path_entry.delete(0, "end")
            api_path_entry.insert(0, "未选择")
            api_path_entry.configure(state="readonly")
            update_api_settings_visibility(False)
        
        ctk.CTkButton(api_path_frame, text="选择", width=50, command=browse_api_path).pack(side="left", padx=(0, 5))
        ctk.CTkButton(api_path_frame, text="清除", width=50, command=clear_api_path).pack(side="left")
        
        api_hint = ctk.CTkLabel(frame, text="选择包含 app.js 的API服务目录后可启用本地API功能", text_color="gray")
        api_hint.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        api_settings_frame = ctk.CTkFrame(frame)
        api_settings_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        auto_start_api_var = ctk.BooleanVar(value=self.config.get("auto_start_api", False))
        auto_start_api_check = ctk.CTkCheckBox(api_settings_frame, text="启动时自动启动本地API服务", variable=auto_start_api_var)
        auto_start_api_check.pack(anchor="w", pady=(10, 5), padx=10)
        
        auto_close_api_var = ctk.BooleanVar(value=self.config.get("auto_close_api", True))
        auto_close_api_check = ctk.CTkCheckBox(api_settings_frame, text="程序关闭时自动关闭API服务", variable=auto_close_api_var)
        auto_close_api_check.pack(anchor="w", pady=(0, 10), padx=10)
        
        def update_api_settings_visibility(has_api_path):
            if has_api_path:
                api_settings_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
            else:
                api_settings_frame.grid_forget()
        
        update_api_settings_visibility(bool(current_api_path))
        
        sep1 = ctk.CTkFrame(frame, height=2, fg_color="gray")
        sep1.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        ctk.CTkLabel(frame, text="API地址:").grid(row=4, column=0, sticky="w", pady=(0, 10))
        
        api_entry = ctk.CTkEntry(frame, width=300)
        api_entry.grid(row=4, column=1, pady=(0, 10), padx=(10, 0))
        api_entry.insert(0, self.BASE_URL)
        
        ctk.CTkLabel(frame, text="文件命名格式:").grid(row=5, column=0, sticky="w", pady=(0, 10))
        
        name_format_var = ctk.StringVar(value=self.config.get("file_name_format", "song-artist"))
        name_format_combo = ctk.CTkComboBox(frame, variable=name_format_var, width=300, values=["song-artist", "artist-song"], state="readonly")
        name_format_combo.grid(row=5, column=1, pady=(0, 10), padx=(10, 0))
        
        format_hint = ctk.CTkLabel(frame, text="song-artist: 歌曲名-歌手  |  artist-song: 歌手-歌曲名")
        format_hint.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        auto_close_var = ctk.BooleanVar(value=self.config.get("auto_close_download_window", False))
        auto_close_check = ctk.CTkCheckBox(frame, text="下载完成后自动关闭下载窗口", variable=auto_close_var)
        auto_close_check.grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        ctk.CTkLabel(frame, text="下载保存目录:").grid(row=8, column=0, sticky="w", pady=(0, 10))
        
        download_dir_frame = ctk.CTkFrame(frame)
        download_dir_frame.grid(row=8, column=1, pady=(0, 10), padx=(10, 0), sticky="w")
        
        current_download_dir = self.config.get("download_dir", "")
        display_download_dir = resolve_path(current_download_dir) if current_download_dir else get_download_dir()
        download_dir_var = ctk.StringVar(value=display_download_dir)
        download_dir_entry = ctk.CTkEntry(download_dir_frame, width=240)
        download_dir_entry.pack(side="left", padx=(0, 5))
        download_dir_entry.insert(0, display_download_dir)
        
        def browse_download_dir():
            initial_dir = resolve_path(current_download_dir) if current_download_dir else get_download_dir()
            selected_dir = filedialog.askdirectory(initialdir=initial_dir, title="选择下载保存目录")
            if selected_dir:
                download_dir_var.set(selected_dir)
                download_dir_entry.delete(0, "end")
                download_dir_entry.insert(0, selected_dir)
        
        ctk.CTkButton(download_dir_frame, text="浏览...", width=60, command=browse_download_dir).pack(side="left")
        
        sep2 = ctk.CTkFrame(frame, height=2, fg_color="gray")
        sep2.grid(row=9, column=0, columnspan=2, sticky="ew", pady=10)
        
        ctk.CTkLabel(frame, text="登录网易云").grid(row=10, column=0, sticky="w", pady=(0, 10))
        btn = ctk.CTkButton(frame, text="点击登录", command=lambda: self.yyy_login(qr_label))
        btn.grid(row=10, column=1, pady=(0, 10), padx=(10, 0), sticky="w")
        
        qr_label = ctk.CTkLabel(frame, text="")
        qr_label.grid(row=11, column=0, columnspan=2, pady=(10, 0))
        
        ctk.CTkLabel(frame, text="切换用户:").grid(row=12, column=0, sticky="w", pady=(0, 10))
        
        user_frame = ctk.CTkFrame(frame)
        user_frame.grid(row=12, column=1, pady=(0, 10), padx=(10, 0), sticky="w")
        
        user_list = ctk.CTkComboBox(user_frame, width=240, state="readonly")
        user_list.pack(side="left", padx=(0, 10))
        
        def refresh_user_list():
            users = get_all_users()
            user_names = [u["user_name"] for u in users]
            user_list.configure(values=user_names)
            current_file = self.config.get("current_user_file")
            for i, u in enumerate(users):
                if u["file"] == current_file:
                    user_list.set(u["user_name"])
                    break
            return users
        
        users_data = refresh_user_list()
        
        def switch_user(event=None):
            selected_name = user_list.get()
            for u in users_data:
                if u["user_name"] == selected_name:
                    user_data = load_user_data(u["file"])
                    if user_data:
                        self.login_cookie = user_data.get("cookie")
                        self.user_name = user_data.get("user_name")
                        self.user_id = user_data.get("user_id")
                        self.config["current_user_file"] = u["file"]
                        save_config(self.config)
                        self.log(f"已切换到用户: {self.user_name}", "INFO")
                    break
        
        user_list.bind("<<ComboboxSelected>>", switch_user)
        
        ctk.CTkButton(user_frame, text="刷新", width=60, command=lambda: refresh_user_list()).pack(side="left")
        
        current_user_label = ctk.CTkLabel(frame, text=f"当前用户: {self.user_name or '未登录'}")
        current_user_label.grid(row=13, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        def save_settings():
            new_url = api_entry.get().strip()
            if not new_url:
                messagebox.showwarning("提示", "API地址不能为空")
                return
            
            new_download_dir = download_dir_var.get().strip()
            if new_download_dir:
                resolved_download_dir = resolve_path(new_download_dir)
                if not os.path.exists(resolved_download_dir):
                    try:
                        os.makedirs(resolved_download_dir)
                    except Exception as e:
                        messagebox.showwarning("提示", f"无法创建目录: {e}")
                        return
            
            new_api_path = api_path_var.get().strip()
            if new_api_path == "未选择":
                new_api_path = ""
            
            if new_api_path:
                resolved_api_path = resolve_path(new_api_path)
                if not os.path.exists(resolved_api_path):
                    messagebox.showwarning("提示", f"API路径不存在: {resolved_api_path}")
                    return
            
            old_api_path = self.config.get("api_path", "")
            old_auto_start = self.config.get("auto_start_api", False)
            new_auto_start = auto_start_api_var.get() if new_api_path else False
            
            self.BASE_URL = new_url
            self.config["api_url"] = new_url
            self.config["file_name_format"] = name_format_var.get()
            self.config["auto_close_download_window"] = auto_close_var.get()
            
            saved_api_path = make_relative_path(new_api_path) if new_api_path else ""
            saved_download_dir = make_relative_path(new_download_dir) if new_download_dir else ""
            
            self.config["api_path"] = saved_api_path
            if new_api_path:
                self.config["auto_start_api"] = auto_start_api_var.get()
                self.config["auto_close_api"] = auto_close_api_var.get()
            else:
                self.config["auto_start_api"] = False
                self.config["auto_close_api"] = True
            if new_download_dir:
                self.config["download_dir"] = saved_download_dir
            save_config(self.config)
            self.log(f"设置已保存", "INFO")
            settings_window.destroy()
            
            def test_and_start_api():
                if check_api_running():
                    self.root.after(0, lambda: self.log("API服务已在运行", "INFO"))
                    self.api_available = True
                    return
                
                if new_api_path and new_auto_start:
                    self.root.after(0, lambda: self.log("正在启动本地API服务...", "INFO"))
                    self._start_api_thread(resolve_path(new_api_path))
                else:
                    self.root.after(0, lambda: self.log(f"正在测试API连接: {new_url}", "INFO"))
                    try:
                        resp = requests.get(new_url, timeout=5)
                        if resp.status_code == 200:
                            self.root.after(0, lambda: self.log("API连接成功", "INFO"))
                            self.api_available = True
                        else:
                            self.root.after(0, lambda: self.log(f"API返回状态码: {resp.status_code}", "WARNING"))
                    except Exception as e:
                        self.root.after(0, lambda: self.log(f"API连接失败: {e}", "ERROR"))
            
            threading.Thread(target=test_and_start_api, daemon=True).start()
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.grid(row=14, column=0, columnspan=2, pady=(10, 0))
        
        ctk.CTkButton(btn_frame, text="保存", width=80, command=save_settings).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="取消", width=80, command=settings_window.destroy).pack(side="left")
        
        version_label = ctk.CTkLabel(frame, text="Cloud Music Download V1.0.0", text_color="gray")
        version_label.grid(row=15, column=0, columnspan=2, pady=(20, 0))


def check_api_running():
    try:
        response = requests.get("http://localhost:3000", timeout=2)
        return response.status_code == 200
    except:
        return False


def start_api_server(api_path):
    if not api_path or not os.path.exists(api_path):
        print(f"API路径无效: {api_path}")
        return None
    
    app_js = os.path.join(api_path, "app.js")
    if not os.path.exists(app_js):
        print(f"app.js 不存在: {app_js}")
        return None
    
    env = os.environ.copy()
    
    node_cmd = "node"
    
    if os.name == 'nt':
        node_exe_name = "node.exe"
    else:
        node_exe_name = "node"
    
    project_node_exe = os.path.join(get_app_dir(), "node", node_exe_name)
    if os.path.exists(project_node_exe):
        node_cmd = project_node_exe
        node_dir = os.path.dirname(project_node_exe)
        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
        print(f"使用项目内Node.js: {node_cmd}")
    else:
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"使用系统Node.js: {result.stdout.strip()}")
            else:
                print("未找到可用的Node.js，请确保已安装Node.js")
                return None
        except:
            print("未找到可用的Node.js，请确保已安装Node.js")
            return None
    
    print(f"启动API: {node_cmd} {app_js}")
    print(f"工作目录: {api_path}")
    
    try:
        kwargs = {
            'args': [node_cmd, app_js],
            'cwd': api_path,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'env': env
        }
        
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs['start_new_session'] = True
        
        process = subprocess.Popen(**kwargs)
        print(f"进程已创建, PID: {process.pid}")
        return process
    except Exception as e:
        print(f"启动API服务失败: {e}")
        return None

def get_app_dir():
    """获取应用程序所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def main():
    root = ctk.CTk()
    
    icon_path = os.path.join(get_app_dir(), "icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    
    app = MusicDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()