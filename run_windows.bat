@echo off
echo Termius 一键汉化工具启动脚本
echo ============================
echo.

CD /D "%~dp0"

if exist "termius_chinese.exe" (
    echo 启动汉化工具...
    start "" "termius_chinese.exe"
    exit /b 0
)

if not exist "termius_chinese.py" (
    echo 未找到 termius_chinese.exe 或 termius_chinese.py！
    echo 请重新下载并完整解压 Windows 压缩包。
    pause
    exit /b 1
)

echo 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 未安装或未添加到环境变量中！
    echo 请安装 Python 3.6 或更高版本。
    echo 您可以从 https://www.python.org/downloads/ 下载 Python。
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

echo 启动汉化工具...
python termius_chinese.py

if %errorlevel% neq 0 (
    echo.
    echo 程序运行出错！
    echo 请确保您的计算机已安装 Python 3.6+ 和必要的依赖。
    echo.
    echo 按任意键退出...
    pause >nul
)
