# 📦 自动打包说明

本文档介绍如何使用 GitHub Actions 自动打包 Cloud Music Download 为各平台可执行文件。

## 🚀 自动打包触发方式

### 方式一：发布新版本（推荐）

1. 创建并推送标签：
```bash
git tag v1.0.0
git push origin v1.0.0
```

2. GitHub Actions 会自动：
   - 构建 Windows、macOS、Linux 三个平台的可执行文件
   - 创建 GitHub Release
   - 上传打包文件到 Release

### 方式二：手动触发

1. 进入 GitHub 仓库
2. 点击 "Actions" 标签
3. 选择 "Build Executables" workflow
4. 点击 "Run workflow"
5. 选择是否创建 Release
6. 点击 "Run workflow" 按钮

## 📥 下载打包文件

### 从 Release 下载

1. 进入 [Releases](https://github.com/mobaixingyao/Cloud-Music-Download/releases) 页面
2. 选择对应版本
3. 下载对应平台的文件：
   - Windows: `Cloud-Music-Download-windows.zip`
   - macOS: `Cloud-Music-Download-macos.zip`
   - Linux: `Cloud-Music-Download-linux.tar.gz`

### 从 Actions 下载

1. 进入 [Actions](https://github.com/mobaixingyao/Cloud-Music-Download/actions) 页面
2. 选择对应的 workflow 运行记录
3. 在 "Artifacts" 部分下载对应平台的文件

## 🛠️ 本地打包

如果需要在本地打包，请按以下步骤操作：

### 安装依赖

```bash
pip install -r requirements.txt
```

### 打包命令

#### Windows
```bash
pyinstaller --clean "Cloud Music Download.spec"
```

#### macOS
```bash
pyinstaller --clean "Cloud Music Download.spec"
```

#### Linux
```bash
pyinstaller --clean "Cloud Music Download.spec"
```

打包完成后，可执行文件位于 `dist/` 目录下。

## 📋 打包文件说明

### Windows
- 文件名：`Cloud Music Download.exe`
- 类型：单个可执行文件
- 大小：约 15-20 MB

### macOS
- 文件名：`Cloud Music Download`
- 类型：单个可执行文件
- 大小：约 15-20 MB
- 注意：首次运行可能需要执行 `xattr -cr "Cloud Music Download"`

### Linux
- 文件名：`Cloud Music Download`
- 类型：单个可执行文件
- 大小：约 15-20 MB
- 注意：需要添加执行权限 `chmod +x "Cloud Music Download"`

## ⚙️ 配置文件说明

### build.yml

GitHub Actions 配置文件，位于 `.github/workflows/build.yml`

主要功能：
- 多平台构建（Windows、macOS、Linux）
- 使用 PyInstaller 打包
- 自动创建 Release
- 上传构建产物

### Cloud Music Download.spec

PyInstaller 配置文件，定义打包规则

主要配置：
- 单文件打包模式
- 窗口模式（无控制台）
- 包含图标文件
- 包含必要的依赖库

### requirements.txt

Python 依赖列表，包含：
- customtkinter：GUI 框架
- requests：HTTP 请求库
- Pillow：图像处理库
- pyinstaller：打包工具

## 🔧 自定义打包

### 修改图标

1. 替换 `icon.ico` 文件
2. 重新打包即可

### 添加额外文件

在 `Cloud Music Download.spec` 文件中修改 `datas` 列表：

```python
datas=[
    ('icon.ico', '.'),
    ('config.json', '.'),  # 添加配置文件
    ('README.md', '.'),    # 添加说明文档
],
```

### 修改打包选项

在 `Cloud Music Download.spec` 文件中修改 `exe` 配置：

```python
exe = EXE(
    # ... 其他配置
    name='Your App Name',      # 修改应用名称
    console=True,              # 显示控制台（调试用）
    debug=True,                # 启用调试模式
)
```

## 🐛 常见问题

### 打包后文件过大

- 使用 UPX 压缩：`upx=True`
- 排除不必要的模块：在 `excludes` 中添加

### 打包后无法运行

1. 检查是否包含所有依赖
2. 检查 `hiddenimports` 列表
3. 使用 `console=True` 查看错误信息

### macOS 提示"无法打开"

运行以下命令：
```bash
xattr -cr "Cloud Music Download"
```

### Linux 无法运行

添加执行权限：
```bash
chmod +x "Cloud Music Download"
```

## 📚 相关文档

- [PyInstaller 官方文档](https://pyinstaller.org/)
- [GitHub Actions 文档](https://docs.github.com/actions)
- [CustomTkinter 文档](https://customtkinter.tomschimansky.com/)
