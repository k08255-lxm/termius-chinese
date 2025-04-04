#!/bin/bash

echo "Termius 一键汉化工具启动脚本"
echo "============================"
echo ""

# 检查是否以root权限运行
if [ "$(id -u)" != "0" ]; then
   echo "此脚本需要root权限才能运行"
   echo "请使用 sudo 运行此脚本"
   echo "命令: sudo bash $0"
   exit 1
fi

# 检查Python环境
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "Python3未安装！"
    echo "请安装Python 3.6或更高版本。"
    echo "您可以使用以下命令安装Python："
    echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-tk"
    echo "Fedora: sudo dnf install python3 python3-pip python3-tkinter"
    echo "Arch Linux: sudo pacman -S python python-pip tk"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "pip3未安装！正在尝试安装..."
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y python3-pip
    elif command -v dnf &> /dev/null; then
        dnf install -y python3-pip
    elif command -v pacman &> /dev/null; then
        pacman -S --noconfirm python-pip
    else
        echo "无法自动安装pip，请手动安装后重试"
        exit 1
    fi
fi

# 检查tkinter
echo "检查并安装必要的依赖..."
python3 -c "import tkinter" &> /dev/null
if [ $? -ne 0 ]; then
    echo "tkinter未安装！正在尝试安装..."
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y python3-tk
    elif command -v dnf &> /dev/null; then
        dnf install -y python3-tkinter
    elif command -v pacman &> /dev/null; then
        pacman -S --noconfirm tk
    else
        echo "无法自动安装tkinter，请手动安装后重试"
        echo "Ubuntu/Debian: sudo apt-get install python3-tk"
        echo "Fedora: sudo dnf install python3-tkinter"
        echo "Arch Linux: sudo pacman -S tk"
        exit 1
    fi
fi

# 给脚本执行权限
chmod +x termius_chinese.py

# 启动汉化工具
echo "启动汉化工具..."
python3 termius_chinese.py

if [ $? -ne 0 ]; then
    echo ""
    echo "程序运行出错！"
    echo "请确保您的系统已安装Python 3.6+和必要的依赖。"
    echo ""
    echo "按Enter键退出..."
    read
fi