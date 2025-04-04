@echo off
echo Termius 一键汉化工具启动脚本
echo ============================
echo.

:: 检查是否以管理员身份运行
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo 请求管理员权限...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

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

echo 检查并安装必要的依赖...
pip install -q tkinter

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