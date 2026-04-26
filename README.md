# 🎵 Cloud Music Download

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![Build](https://github.com/mobaixingyao/Cloud-Music-Download/workflows/Build%20Executables/badge.svg)

**一款基于 Python 开发的网易云音乐下载工具，支持无损音质下载**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [使用说明](#-使用说明) • [配置说明](#-配置说明)

</div>

***

## 📖 项目简介

Cloud Music Download 是一个开源的网易云音乐下载工具，提供简洁友好的图形界面，支持搜索、试听、下载网易云音乐。基于 [NeteaseCloudMusicApiEnhanced/api-enhanced](https://github.com/NeteaseCloudMusicApiEnhanced/api-enhanced) 项目开发，支持无损音质下载。

### ✨ 功能特性

- 🔍 **音乐搜索** - 支持关键词搜索，快速找到想听的歌曲
- 🎵 **无损下载** - 支持无损音质（FLAC）下载
- 📋 **歌单下载** - 支持批量下载整个歌单
- 👤 **账号登录** - 支持网易云账号扫码登录
- 🎨 **现代界面** - 基于 CustomTkinter 的现代化 UI 设计
- 📁 **自定义路径** - 支持自定义下载路径和文件命名格式
- 🌐 **灵活部署** - 支持本地和云端 API 部署
- 💻 **跨平台** - 支持 Windows、macOS、Linux
- 📱 **自适应分辨率** - 自动适配不同分辨率和 DPI 缩放
- 🔧 **相对路径支持** - 支持相对路径配置，便于移植

***

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- Node.js 14 或更高版本（本地部署 API 时需要）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

#### 方式一：直接运行（推荐）

Windows 用户：

```bash
start.bat
```

Linux/macOS 用户：

```bash
python "Cloud Music Download.py"
```

#### 方式二：手动安装依赖后运行

```bash
# 安装 Python 依赖
pip install customtkinter requests pillow

# 运行程序
python "Cloud Music Download.py"
```

***

## 📖 使用说明

### 1. 配置 API 服务

#### 选项 A：使用云端 API（推荐新手）

1. 在云端部署 [api-enhanced](https://github.com/NeteaseCloudMusicApiEnhanced/api-enhanced) 项目
2. 在设置中填写云端 API 地址
3. 保存设置即可使用

#### 选项 B：使用本地 API

1. 克隆或下载 [api-enhanced](https://github.com/NeteaseCloudMusicApiEnhanced/api-enhanced) 项目
2. 在设置中选择 API 服务路径（包含 `app.js` 的目录）
3. API 地址填写 `http://localhost:3000`
4. 启用"启动时自动启动本地 API 服务"
5. 保存设置，程序会自动启动 API 服务

### 2. 登录账号

1. 点击"设置"按钮
2. 点击"点击登录"
3. 使用网易云音乐 APP 扫描二维码
4. 登录成功后即可访问个人歌单

### 3. 搜索和下载

1. 在搜索框输入歌曲名称或歌手
2. 点击搜索按钮
3. 在结果列表中选择要下载的歌曲
4. 点击下载按钮开始下载
5. 下载完成后可在下载目录查看

### 4. 歌单下载

1. 登录后点击"我的歌单"
2. 选择要下载的歌单
3. 点击"批量下载"按钮
4. 等待下载完成

***

## ⚙️ 配置说明

### config.json 配置文件

程序会在运行目录下生成 `config.json` 配置文件：

```json
{
  "api_url": "http://localhost:3000",
  "file_name_format": "song-artist",
  "current_user_file": null,
  "auto_close_download_window": false,
  "download_dir": "../downloads",
  "auto_start_api": false,
  "auto_close_api": true,
  "api_path": "../api-enhanced-main"
}
```

### 配置项说明

| 配置项                          | 说明               | 默认值                     |
| ---------------------------- | ---------------- | ----------------------- |
| `api_url`                    | API 服务地址         | `http://localhost:3000` |
| `file_name_format`           | 文件命名格式           | `song-artist`           |
| `current_user_file`          | 当前用户数据文件         | `null`                  |
| `auto_close_download_window` | 下载完成后自动关闭窗口      | `false`                 |
| `download_dir`               | 下载目录（支持相对路径）     | `../downloads`          |
| `auto_start_api`             | 启动时自动启动本地 API    | `false`                 |
| `auto_close_api`             | 关闭程序时自动关闭 API    | `true`                  |
| `api_path`                   | API 服务路径（支持相对路径） | `../api-enhanced-main`  |

### 文件命名格式

- `song-artist`: 歌曲名 - 歌手
- `artist-song`: 歌手 - 歌曲名

***

## 🛠️ 技术栈

- **GUI 框架**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **HTTP 请求**: [Requests](https://github.com/psf/requests)
- **图像处理**: [Pillow](https://github.com/python-pillow/Pillow)
- **API 服务**: [NeteaseCloudMusicApiEnhanced](https://github.com/NeteaseCloudMusicApiEnhanced/api-enhanced)

***

## 📁 项目结构

```
MoMusic/
├── Cloud Music Download.py    # 主程序
├── config.json                 # 配置文件
├── icon.ico                    # 程序图标
├── start.bat                   # Windows 启动脚本
├── node/                       # Node.js 运行时（可选）
├── downloads/                  # 下载目录
├── userdata/                   # 用户数据
└── api-enhanced-main/          # API 服务（可选）
```

***

## ⚠️ 免责声明

- 本软件仅供学习交流使用
- 请勿用于商业用途
- 使用本软件造成的一切后果由用户自行承担

***

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star ⭐**

Made with ❤️ by 墨白星耀

</div>
