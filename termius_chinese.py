#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import platform
import shutil
import tempfile
import urllib.request
import zipfile
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import webbrowser
import threading
import json

# 版本信息
VERSION = "1.0.0"

# GitHub 仓库信息
GITHUB_REPO = "ArcSurge/Termius-Pro-zh_CN"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASE_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

# 默认安装路径
def get_default_install_path():
    system = platform.system().lower()
    if system == "windows":
        return os.path.expandvars(r"%LOCALAPPDATA%\Programs\Termius")
    elif system == "darwin":  # macOS
        return "/Applications/Termius.app/Contents"
    elif system == "linux":
        return "/opt/Termius"
    else:
        return ""

# 获取系统类型
def get_system_type():
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"

# 获取最新版本信息
def get_latest_release_info():
    try:
        with urllib.request.urlopen(GITHUB_API_URL) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"获取最新版本信息失败: {e}")
        return None

# 下载文件
def download_file(url, dest_path, progress_callback=None):
    try:
        with urllib.request.urlopen(url) as response:
            file_size = int(response.info().get('Content-Length', 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1MB
            with open(dest_path, 'wb') as out_file:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, file_size)
        return True
    except Exception as e:
        print(f"下载文件失败: {e}")
        return False

# 备份原始文件
def backup_original_file(file_path):
    if not os.path.exists(file_path):
        return False
    
    backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"备份文件失败: {e}")
        return False

# 恢复备份文件
def restore_backup(termius_path):
    app_asar_path = os.path.join(termius_path, "resources", "app.asar")
    backup_files = [f for f in os.listdir(os.path.dirname(app_asar_path)) 
                   if f.startswith("app.asar.bak.")]
    
    if not backup_files:
        return False, "未找到备份文件"
    
    # 按时间排序，获取最新的备份
    latest_backup = sorted(backup_files)[-1]
    backup_path = os.path.join(os.path.dirname(app_asar_path), latest_backup)
    
    try:
        shutil.copy2(backup_path, app_asar_path)
        return True, f"已恢复备份: {latest_backup}"
    except Exception as e:
        return False, f"恢复备份失败: {e}"

# 应用汉化
class TermiusChineseApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Termius 汉化工具 v{VERSION}")
        self.root.geometry("600x450")
        self.root.resizable(True, True)
        
        # 设置窗口图标
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="Termius 一键汉化工具", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 说明文本
        desc_text = "此工具可以帮助您一键汉化 Termius 软件，支持 Windows、macOS 和 Linux 平台。\n在使用前，请确保已关闭 Termius 软件。"
        desc_label = ttk.Label(main_frame, text=desc_text, wraplength=550, justify="center")
        desc_label.pack(pady=10)
        
        # 安装路径选择
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(path_frame, text="Termius 安装路径:").pack(side=tk.LEFT, padx=5)
        
        self.path_var = tk.StringVar(value=get_default_install_path())
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=40)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(path_frame, text="浏览...", command=self.browse_path)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # 汉化版本选择
        version_frame = ttk.LabelFrame(main_frame, text="汉化版本选择", padding=10)
        version_frame.pack(fill=tk.X, pady=10)
        
        self.version_var = tk.StringVar(value="localize")
        
        ttk.Radiobutton(version_frame, text="仅汉化 (适合已有会员的用户)", 
                        variable=self.version_var, value="localize").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(version_frame, text="汉化+试用 (消除升级提示，适合试用用户)", 
                        variable=self.version_var, value="localize-trial").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(version_frame, text="汉化+跳过登录 (适合离线用户)", 
                        variable=self.version_var, value="localize-skip").pack(anchor=tk.W, pady=2)
        
        # 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        self.apply_btn = ttk.Button(btn_frame, text="应用汉化", command=self.apply_chinese, width=15)
        self.apply_btn.pack(side=tk.LEFT, padx=10)
        
        self.restore_btn = ttk.Button(btn_frame, text="恢复原版", command=self.restore_original, width=15)
        self.restore_btn.pack(side=tk.LEFT, padx=10)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", 
                                       length=550, mode="determinate", 
                                       variable=self.progress_var)
        self.progress.pack(pady=10, fill=tk.X)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=5)
        
        # 底部信息
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        
        version_label = ttk.Label(footer_frame, text=f"版本: {VERSION}")
        version_label.pack(side=tk.LEFT)
        
        github_link = ttk.Label(footer_frame, text="GitHub 项目", foreground="blue", cursor="hand2")
        github_link.pack(side=tk.RIGHT)
        github_link.bind("<Button-1>", lambda e: webbrowser.open(f"https://github.com/{GITHUB_REPO}"))
    
    def browse_path(self):
        path = filedialog.askdirectory(title="选择 Termius 安装目录")
        if path:
            self.path_var.set(path)
    
    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def update_progress(self, current, total):
        if total > 0:
            progress_value = (current / total) * 100
            self.progress_var.set(progress_value)
            self.update_status(f"下载中... {current/1024/1024:.1f}MB / {total/1024/1024:.1f}MB ({progress_value:.1f}%)")
    
    def enable_controls(self, enable=True):
        state = "normal" if enable else "disabled"
        self.apply_btn["state"] = state
        self.restore_btn["state"] = state
    
    def apply_chinese(self):
        # 获取安装路径
        termius_path = self.path_var.get().strip()
        if not termius_path or not os.path.exists(termius_path):
            messagebox.showerror("错误", "请选择有效的 Termius 安装目录")
            return
        
        # 检查 resources 目录
        resources_path = os.path.join(termius_path, "resources")
        if not os.path.exists(resources_path):
            messagebox.showerror("错误", "无法找到 Termius 的 resources 目录，请确认安装路径是否正确")
            return
        
        # 检查 app.asar 文件
        app_asar_path = os.path.join(resources_path, "app.asar")
        if not os.path.exists(app_asar_path):
            messagebox.showerror("错误", "无法找到 app.asar 文件，请确认安装路径是否正确")
            return
        
        # 禁用控件
        self.enable_controls(False)
        
        # 在新线程中执行汉化操作
        threading.Thread(target=self._apply_chinese_thread, args=(termius_path,), daemon=True).start()
    
    def _apply_chinese_thread(self, termius_path):
        try:
            # 更新状态
            self.update_status("正在获取最新版本信息...")
            
            # 获取最新版本信息
            release_info = get_latest_release_info()
            if not release_info:
                self.update_status("获取版本信息失败，请检查网络连接")
                messagebox.showerror("错误", "获取版本信息失败，请检查网络连接或直接访问GitHub下载")
                self.enable_controls()
                return
            
            # 获取系统类型
            system_type = get_system_type()
            if system_type == "unknown":
                self.update_status("不支持的操作系统")
                messagebox.showerror("错误", "不支持的操作系统")
                self.enable_controls()
                return
            
            # 获取选择的汉化版本
            version_type = self.version_var.get()
            
            # 查找对应的资源文件
            asset_name = f"app-{system_type}-{version_type}.asar"
            asset_url = None
            
            for asset in release_info.get("assets", []):
                if asset["name"] == asset_name:
                    asset_url = asset["browser_download_url"]
                    break
            
            if not asset_url:
                self.update_status(f"未找到适用于 {system_type} 的 {version_type} 汉化包")
                messagebox.showerror("错误", f"未找到适用于 {system_type} 的 {version_type} 汉化包，请直接访问GitHub下载")
                self.enable_controls()
                return
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 下载文件
                download_path = os.path.join(temp_dir, "app.asar")
                self.update_status(f"正在下载汉化包: {asset_name}...")
                
                # 重置进度条
                self.progress_var.set(0)
                
                # 下载文件
                if not download_file(asset_url, download_path, self.update_progress):
                    self.update_status("下载汉化包失败")
                    messagebox.showerror("错误", "下载汉化包失败，请检查网络连接或直接访问GitHub下载")
                    self.enable_controls()
                    return
                
                # 备份原始文件
                self.update_status("正在备份原始文件...")
                app_asar_path = os.path.join(termius_path, "resources", "app.asar")
                backup_path = backup_original_file(app_asar_path)
                
                if not backup_path:
                    self.update_status("备份原始文件失败")
                    messagebox.showerror("错误", "备份原始文件失败，操作已取消")
                    self.enable_controls()
                    return
                
                # 替换文件
                self.update_status("正在替换文件...")
                try:
                    shutil.copy2(download_path, app_asar_path)
                    self.update_status("汉化完成！请重启 Termius 以应用更改")
                    messagebox.showinfo("成功", "汉化完成！请重启 Termius 以应用更改\n\n原始文件已备份为:\n" + backup_path)
                except Exception as e:
                    self.update_status(f"替换文件失败: {e}")
                    messagebox.showerror("错误", f"替换文件失败: {e}\n\n请确保 Termius 已关闭，并尝试以管理员身份运行此工具")
        except Exception as e:
            self.update_status(f"发生错误: {e}")
            messagebox.showerror("错误", f"发生错误: {e}")
        finally:
            self.enable_controls()
    
    def restore_original(self):
        # 获取安装路径
        termius_path = self.path_var.get().strip()
        if not termius_path or not os.path.exists(termius_path):
            messagebox.showerror("错误", "请选择有效的 Termius 安装目录")
            return
        
        # 禁用控件
        self.enable_controls(False)
        
        # 在新线程中执行恢复操作
        threading.Thread(target=self._restore_original_thread, args=(termius_path,), daemon=True).start()
    
    def _restore_original_thread(self, termius_path):
        try:
            self.update_status("正在恢复原始文件...")
            success, message = restore_backup(termius_path)
            
            if success:
                self.update_status("恢复完成！请重启 Termius 以应用更改")
                messagebox.showinfo("成功", "恢复完成！请重启 Termius 以应用更改")
            else:
                self.update_status(f"恢复失败: {message}")
                messagebox.showerror("错误", f"恢复失败: {message}")
        except Exception as e:
            self.update_status(f"发生错误: {e}")
            messagebox.showerror("错误", f"发生错误: {e}")
        finally:
            self.enable_controls()

# 主函数
def main():
    # 检查是否以管理员权限运行（仅在 Windows 上）
    if platform.system().lower() == "windows":
        try:
            # 尝试创建一个文件在 Program Files 目录下，如果成功则有管理员权限
            test_path = os.path.join(os.environ["ProgramFiles"], "test_admin_rights.txt")
            with open(test_path, "w") as f:
                f.write("test")
            os.remove(test_path)
        except:
            # 如果失败，提示用户以管理员身份运行
            if sys.executable.endswith(".exe"):
                # 如果是 exe 文件，使用 UAC 提示
                ctypes_import = "import ctypes\nctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, ' '.join(sys.argv), None, 1)\nsys.exit(0)"
                exec(ctypes_import)
            else:
                # 如果是 Python 脚本，提示用户手动以管理员身份运行
                print("请以管理员身份运行此程序")
                input("按回车键退出...")
                sys.exit(1)
    
    # 创建 GUI
    root = tk.Tk()
    app = TermiusChineseApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()