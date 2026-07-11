#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import platform
import queue
import re
import shutil
import sys
import tempfile
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox, ttk


VERSION = "1.1.0"

TOOL_REPO = "k08255-lxm/termius-chinese"
GITHUB_REPO = "ArcSurge/Termius-Pro-zh_CN"
GITHUB_RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases?per_page=100"
GITHUB_RELEASE_URL = f"https://github.com/{GITHUB_REPO}/releases"
TOOL_LATEST_RELEASE_API_URL = f"https://api.github.com/repos/{TOOL_REPO}/releases/latest"
HTTP_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": f"termius-chinese/{VERSION}",
}


def get_default_install_path():
    system = platform.system().lower()
    if system == "windows":
        return os.path.expandvars(r"%LOCALAPPDATA%\Programs\Termius")
    if system == "darwin":
        return "/Applications/Termius.app/Contents"
    if system == "linux":
        return "/opt/Termius"
    return ""


def get_system_type():
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"
    if system == "linux":
        return "linux"
    return "unknown"


def get_releases_info():
    try:
        request = urllib.request.Request(GITHUB_RELEASES_API_URL, headers=HTTP_HEADERS)
        with urllib.request.urlopen(request, timeout=30) as response:
            releases = json.loads(response.read().decode("utf-8"))
        return [release for release in releases if not release.get("draft")]
    except Exception as error:
        print(f"获取版本信息失败: {error}")
        return []


def get_tool_latest_release():
    try:
        request = urllib.request.Request(TOOL_LATEST_RELEASE_API_URL, headers=HTTP_HEADERS)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as error:
        print(f"检查工具更新失败: {error}")
        return None


def version_tuple(version):
    numbers = [int(part) for part in re.findall(r"\d+", version)]
    return tuple((numbers + [0, 0, 0])[:3])


def is_newer_version(latest, current):
    return version_tuple(latest) > version_tuple(current)


def find_tool_update_asset(release):
    system = platform.system().lower()
    expected_name = {
        "windows": "termius_chinese.exe",
        "linux": "termius_chinese-linux",
    }.get(system, "termius_chinese.py")
    for asset in release.get("assets", []):
        if asset.get("name") == expected_name:
            return asset.get("browser_download_url")
    return release.get("html_url", f"https://github.com/{TOOL_REPO}/releases/latest")


def filter_releases(releases, query):
    query = query.strip().casefold()
    if not query:
        return releases
    return [
        release
        for release in releases
        if query in release.get("tag_name", "").casefold()
        or query in release.get("name", "").casefold()
    ]


def get_default_release(releases):
    if not releases:
        return None
    return next((release for release in releases if not release.get("prerelease")), releases[0])


def find_release_asset(release, system_type, version_type):
    asset_name = f"app-{system_type}-{version_type}.asar"
    for asset in release.get("assets", []):
        if asset.get("name") == asset_name:
            return asset_name, asset.get("browser_download_url")
    return asset_name, None


def format_size(byte_count):
    value = float(byte_count)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024


def download_file(url, dest_path, progress_callback=None):
    try:
        request = urllib.request.Request(url, headers={"User-Agent": HTTP_HEADERS["User-Agent"]})
        with urllib.request.urlopen(request, timeout=60) as response:
            file_size = int(response.info().get("Content-Length", 0))
            downloaded = 0
            started_at = time.monotonic()
            last_at = started_at
            last_downloaded = 0
            speed = 0.0
            with open(dest_path, "wb") as out_file:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    now = time.monotonic()
                    elapsed = now - last_at
                    if elapsed >= 0.1:
                        speed = (downloaded - last_downloaded) / elapsed
                        last_at = now
                        last_downloaded = downloaded
                    elif speed == 0:
                        speed = downloaded / max(now - started_at, 0.001)
                    if progress_callback:
                        progress_callback(downloaded, file_size, speed)
        return True
    except Exception as error:
        print(f"下载文件失败: {error}")
        return False


def backup_original_file(file_path):
    if not os.path.exists(file_path):
        return False
    backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as error:
        print(f"备份文件失败: {error}")
        return False


def restore_backup(termius_path):
    app_asar_path = os.path.join(termius_path, "resources", "app.asar")
    resources_path = os.path.dirname(app_asar_path)
    if not os.path.isdir(resources_path):
        return False, "未找到 resources 目录"
    backup_files = [name for name in os.listdir(resources_path) if name.startswith("app.asar.bak.")]
    if not backup_files:
        return False, "未找到备份文件"
    latest_backup = sorted(backup_files)[-1]
    backup_path = os.path.join(resources_path, latest_backup)
    try:
        shutil.copy2(backup_path, app_asar_path)
        return True, f"已恢复备份: {latest_backup}"
    except Exception as error:
        return False, f"恢复备份失败: {error}"


def is_termius_install_path(path):
    return bool(path) and os.path.isfile(os.path.join(path, "resources", "app.asar"))


def _windows_registry_paths():
    paths = []
    try:
        import winreg
    except ImportError:
        return paths

    access_modes = [winreg.KEY_READ]
    if hasattr(winreg, "KEY_WOW64_64KEY"):
        access_modes.extend([winreg.KEY_READ | winreg.KEY_WOW64_64KEY, winreg.KEY_READ | winreg.KEY_WOW64_32KEY])

    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for access in access_modes:
            try:
                with winreg.OpenKey(
                    hive,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Termius.exe",
                    0,
                    access,
                ) as key:
                    executable, _ = winreg.QueryValueEx(key, None)
                    paths.append(os.path.dirname(executable.strip('"')))
            except OSError:
                pass

    uninstall_roots = (
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    )
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for root_name in uninstall_roots:
            try:
                with winreg.OpenKey(hive, root_name) as root:
                    for index in range(winreg.QueryInfoKey(root)[0]):
                        try:
                            with winreg.OpenKey(root, winreg.EnumKey(root, index)) as key:
                                display_name, _ = winreg.QueryValueEx(key, "DisplayName")
                                if "termius" not in display_name.casefold():
                                    continue
                                install_path, _ = winreg.QueryValueEx(key, "InstallLocation")
                                paths.append(install_path)
                        except OSError:
                            continue
            except OSError:
                continue
    return paths


def find_termius_install_paths():
    system = platform.system().lower()
    candidates = [get_default_install_path()]
    if system == "windows":
        candidates.extend(
            [
                os.path.expandvars(r"%LOCALAPPDATA%\Termius"),
                os.path.expandvars(r"%PROGRAMFILES%\Termius"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%\Termius"),
            ]
        )
        candidates.extend(_windows_registry_paths())
    elif system == "darwin":
        candidates.append(os.path.expanduser("~/Applications/Termius.app/Contents"))
    elif system == "linux":
        candidates.extend(["/usr/lib/termius", "/usr/local/lib/termius"])

    results = []
    seen = set()
    for candidate in candidates:
        normalized = os.path.normpath(os.path.expandvars(os.path.expanduser(candidate or "")))
        key = os.path.normcase(normalized)
        if key not in seen and is_termius_install_path(normalized):
            seen.add(key)
            results.append(normalized)
    return results


class TermiusChineseApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Termius 汉化工具 v{VERSION}")
        self.root.geometry("720x590")
        self.root.minsize(650, 550)
        self.ui_queue = queue.Queue()
        self.releases = []

        main_frame = ttk.Frame(root, padding="12")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Termius 一键汉化工具", font=("Arial", 16, "bold")).pack(pady=8)
        ttk.Label(
            main_frame,
            text="选择匹配的 Termius 版本和汉化模式。操作前请关闭 Termius。",
            wraplength=650,
            justify="center",
        ).pack(pady=6)

        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=8)
        ttk.Label(path_frame, text="安装路径:").pack(side=tk.LEFT, padx=(0, 5))
        self.path_var = tk.StringVar(value=get_default_install_path())
        ttk.Entry(path_frame, textvariable=self.path_var).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        self.find_btn = ttk.Button(path_frame, text="查找", command=self.find_installation)
        self.find_btn.pack(side=tk.LEFT, padx=4)
        ttk.Button(path_frame, text="浏览...", command=self.browse_path).pack(side=tk.LEFT, padx=(4, 0))

        release_frame = ttk.LabelFrame(main_frame, text="Termius 版本（可输入搜索）", padding=10)
        release_frame.pack(fill=tk.X, pady=8)
        self.release_var = tk.StringVar(value="正在加载版本...")
        self.release_combo = ttk.Combobox(release_frame, textvariable=self.release_var, state="disabled")
        self.release_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.release_combo.bind("<KeyRelease>", self.filter_release_options)
        self.release_combo.bind("<Return>", self.search_releases)
        self.release_combo.bind("<KP_Enter>", self.search_releases)
        self.refresh_btn = ttk.Button(release_frame, text="刷新", command=self.load_releases)
        self.refresh_btn.pack(side=tk.RIGHT)
        self.search_btn = ttk.Button(release_frame, text="搜索", command=self.search_releases)
        self.search_btn.pack(side=tk.RIGHT, padx=(0, 8))

        mode_frame = ttk.LabelFrame(main_frame, text="汉化模式", padding=10)
        mode_frame.pack(fill=tk.X, pady=8)
        self.version_var = tk.StringVar(value="localize")
        ttk.Radiobutton(
            mode_frame,
            text="仅汉化（适合已有会员的用户）",
            variable=self.version_var,
            value="localize",
        ).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(
            mode_frame,
            text="汉化 + 试用（消除升级提示）",
            variable=self.version_var,
            value="localize-trial",
        ).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(
            mode_frame,
            text="汉化 + 跳过登录（适合离线用户）",
            variable=self.version_var,
            value="localize-skip",
        ).pack(anchor=tk.W, pady=2)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=12)
        self.apply_btn = ttk.Button(button_frame, text="应用汉化", command=self.apply_chinese, width=15)
        self.apply_btn.pack(side=tk.LEFT, padx=10)
        self.restore_btn = ttk.Button(button_frame, text="恢复原版", command=self.restore_original, width=15)
        self.restore_btn.pack(side=tk.LEFT, padx=10)

        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(main_frame, mode="determinate", variable=self.progress_var).pack(pady=8, fill=tk.X)
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.status_var, wraplength=650, justify="center").pack(pady=5)

        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(8, 0))
        ttk.Label(footer_frame, text=f"版本: {VERSION}").pack(side=tk.LEFT)
        ttk.Button(footer_frame, text="关于", command=self.show_about).pack(side=tk.RIGHT, padx=(8, 0))
        self.update_btn = ttk.Button(footer_frame, text="检查更新", command=lambda: self.check_for_updates(True))
        self.update_btn.pack(side=tk.RIGHT, padx=(8, 0))
        github_link = ttk.Label(footer_frame, text="项目主页", foreground="blue", cursor="hand2")
        github_link.pack(side=tk.RIGHT)
        github_link.bind("<Button-1>", lambda _event: webbrowser.open(f"https://github.com/{TOOL_REPO}"))

        self.root.after(50, self.process_ui_queue)
        self.load_releases()
        self.root.after(1200, self.check_for_updates)

    def process_ui_queue(self):
        try:
            while True:
                callback, args = self.ui_queue.get_nowait()
                callback(*args)
        except queue.Empty:
            pass
        self.root.after(50, self.process_ui_queue)

    def run_on_ui(self, callback, *args):
        if threading.current_thread() is threading.main_thread():
            callback(*args)
        else:
            self.ui_queue.put((callback, args))

    def browse_path(self):
        path = filedialog.askdirectory(title="选择 Termius 安装目录")
        if path:
            self.path_var.set(path)

    def find_installation(self):
        paths = find_termius_install_paths()
        if not paths:
            messagebox.showinfo("查找结果", "未自动找到 Termius，请使用“浏览”手动选择。")
            return
        self.path_var.set(paths[0])
        self.update_status(f"已找到 Termius: {paths[0]}")
        if len(paths) > 1:
            messagebox.showinfo("查找结果", "找到多个安装位置，已选择第一个：\n\n" + "\n".join(paths))

    def load_releases(self):
        self.release_combo.configure(state="disabled")
        self.refresh_btn.configure(state="disabled")
        self.search_btn.configure(state="disabled")
        self.release_var.set("正在加载版本...")
        self.update_status("正在获取 Termius 版本列表...")
        threading.Thread(target=self._load_releases_thread, daemon=True).start()

    def _load_releases_thread(self):
        releases = get_releases_info()
        self.run_on_ui(self.finish_release_load, releases)

    def finish_release_load(self, releases):
        self.releases = releases
        self.refresh_btn.configure(state="normal")
        self.search_btn.configure(state="normal")
        self.release_combo.configure(state="normal")
        tags = [release.get("tag_name", "") for release in releases]
        self.release_combo["values"] = tags
        if tags:
            default_release = get_default_release(releases)
            default_tag = default_release.get("tag_name", tags[0])
            self.release_var.set(default_tag)
            self.update_status(f"已加载 {len(tags)} 个版本，默认选择最新稳定版 {default_tag}")
        else:
            self.release_var.set("")
            self.update_status("版本列表加载失败，请检查网络后刷新")

    def filter_release_options(self, event=None):
        if event and event.keysym in {"Up", "Down", "Return", "Escape", "Tab"}:
            return
        matches = filter_releases(self.releases, self.release_var.get())
        self.release_combo["values"] = [release.get("tag_name", "") for release in matches]
        self.update_status(f"匹配 {len(matches)} 个版本")

    def search_releases(self, event=None):
        matches = filter_releases(self.releases, self.release_var.get())
        self.release_combo["values"] = [release.get("tag_name", "") for release in matches]
        if not matches:
            self.update_status("未找到匹配版本")
            messagebox.showinfo("搜索结果", "未找到匹配版本，请换一个版本号搜索。")
        else:
            self.update_status(f"找到 {len(matches)} 个版本，请从结果中选择")
            self.release_combo.focus_set()
            self.root.after_idle(self.show_release_dropdown)
        return "break" if event else None

    def show_release_dropdown(self):
        try:
            self.release_combo.tk.call("ttk::combobox::Post", str(self.release_combo))
        except tk.TclError:
            self.release_combo.event_generate("<Button-1>")

    def selected_release(self):
        value = self.release_var.get().strip().casefold()
        exact = [release for release in self.releases if release.get("tag_name", "").casefold() == value]
        if exact:
            return exact[0]
        matches = filter_releases(self.releases, value)
        if len(matches) == 1:
            self.release_var.set(matches[0].get("tag_name", ""))
            return matches[0]
        if matches:
            messagebox.showerror("版本错误", "匹配到多个版本，请从下拉列表选择一个。")
        else:
            messagebox.showerror("版本错误", "未找到匹配版本，请刷新版本列表后重试。")
        return None

    def update_status(self, message):
        if threading.current_thread() is not threading.main_thread():
            self.run_on_ui(self.update_status, message)
            return
        self.status_var.set(message)

    def update_progress(self, current, total, speed):
        if threading.current_thread() is not threading.main_thread():
            self.run_on_ui(self.update_progress, current, total, speed)
            return
        if total > 0:
            progress_value = current / total * 100
            self.progress_var.set(progress_value)
            total_text = f"{format_size(current)} / {format_size(total)} ({progress_value:.1f}%)"
        else:
            total_text = format_size(current)
        self.status_var.set(f"下载中... {total_text} · {format_size(speed)}/s")

    def show_message(self, kind, title, message):
        if threading.current_thread() is not threading.main_thread():
            self.run_on_ui(self.show_message, kind, title, message)
            return
        getattr(messagebox, kind)(title, message)

    def enable_controls(self, enable=True):
        if threading.current_thread() is not threading.main_thread():
            self.run_on_ui(self.enable_controls, enable)
            return
        state = "normal" if enable else "disabled"
        self.apply_btn.configure(state=state)
        self.restore_btn.configure(state=state)
        self.find_btn.configure(state=state)
        self.refresh_btn.configure(state=state)
        self.search_btn.configure(state=state)
        self.release_combo.configure(state=state)

    def check_for_updates(self, manual=False):
        self.update_btn.configure(state="disabled")
        if manual:
            self.update_status("正在检查工具更新...")
        threading.Thread(target=self._check_for_updates_thread, args=(manual,), daemon=True).start()

    def _check_for_updates_thread(self, manual):
        release = get_tool_latest_release()
        self.run_on_ui(self.finish_update_check, release, manual)

    def finish_update_check(self, release, manual):
        self.update_btn.configure(state="normal")
        if not release:
            if manual:
                self.update_status("检查更新失败")
                messagebox.showerror("检查更新", "无法获取更新信息，请检查网络连接。")
            return
        latest_tag = release.get("tag_name", "")
        if is_newer_version(latest_tag, VERSION):
            should_update = messagebox.askyesno(
                "发现新版本",
                f"当前版本：v{VERSION}\n最新版本：{latest_tag}\n\n是否下载更新？",
            )
            if should_update:
                webbrowser.open(find_tool_update_asset(release))
                self.update_status(f"已打开 {latest_tag} 下载地址")
            else:
                self.update_status(f"已暂缓更新到 {latest_tag}")
        elif manual:
            self.update_status("当前已是最新版本")
            messagebox.showinfo("检查更新", f"当前版本 v{VERSION} 已是最新版本。")

    def apply_chinese(self):
        termius_path = self.path_var.get().strip()
        if not is_termius_install_path(termius_path):
            messagebox.showerror("错误", "请选择包含 resources/app.asar 的 Termius 安装目录。")
            return
        release = self.selected_release()
        if not release:
            return
        version_type = self.version_var.get()
        self.enable_controls(False)
        threading.Thread(
            target=self._apply_chinese_thread,
            args=(termius_path, release, version_type),
            daemon=True,
        ).start()

    def _apply_chinese_thread(self, termius_path, release, version_type):
        try:
            system_type = get_system_type()
            if system_type == "unknown":
                self.update_status("不支持的操作系统")
                self.show_message("showerror", "错误", "不支持的操作系统")
                return

            asset_name, asset_url = find_release_asset(release, system_type, version_type)
            if not asset_url:
                tag = release.get("tag_name", "所选版本")
                self.update_status(f"{tag} 未提供 {asset_name}")
                self.show_message("showerror", "错误", f"{tag} 未提供所选汉化包：\n{asset_name}")
                return

            with tempfile.TemporaryDirectory() as temp_dir:
                download_path = os.path.join(temp_dir, "app.asar")
                self.update_status(f"正在下载 {release.get('tag_name', '')}: {asset_name}")
                self.run_on_ui(self.progress_var.set, 0)
                if not download_file(asset_url, download_path, self.update_progress):
                    self.update_status("下载汉化包失败")
                    self.show_message("showerror", "错误", "下载失败，请检查网络连接后重试。")
                    return

                app_asar_path = os.path.join(termius_path, "resources", "app.asar")
                self.update_status("正在备份原始文件...")
                backup_path = backup_original_file(app_asar_path)
                if not backup_path:
                    self.update_status("备份原始文件失败")
                    self.show_message("showerror", "错误", "备份失败，操作已取消。")
                    return

                self.update_status("正在替换文件...")
                try:
                    shutil.copy2(download_path, app_asar_path)
                    self.run_on_ui(self.progress_var.set, 100)
                    self.update_status("汉化完成，请重启 Termius")
                    self.show_message("showinfo", "成功", f"汉化完成！\n\n原始文件已备份为：\n{backup_path}")
                except Exception as error:
                    self.update_status(f"替换文件失败: {error}")
                    self.show_message(
                        "showerror",
                        "错误",
                        f"替换文件失败：{error}\n\n请关闭 Termius；受保护目录请以管理员身份运行。",
                    )
        except Exception as error:
            self.update_status(f"发生错误: {error}")
            self.show_message("showerror", "错误", f"发生错误：{error}")
        finally:
            self.enable_controls()

    def restore_original(self):
        termius_path = self.path_var.get().strip()
        if not is_termius_install_path(termius_path):
            messagebox.showerror("错误", "请选择有效的 Termius 安装目录。")
            return
        self.enable_controls(False)
        threading.Thread(target=self._restore_original_thread, args=(termius_path,), daemon=True).start()

    def _restore_original_thread(self, termius_path):
        try:
            self.update_status("正在恢复原始文件...")
            success, message = restore_backup(termius_path)
            if success:
                self.update_status("恢复完成，请重启 Termius")
                self.show_message("showinfo", "成功", "恢复完成！请重启 Termius。")
            else:
                self.update_status(f"恢复失败: {message}")
                self.show_message("showerror", "错误", f"恢复失败：{message}")
        except Exception as error:
            self.update_status(f"发生错误: {error}")
            self.show_message("showerror", "错误", f"发生错误：{error}")
        finally:
            self.enable_controls()

    def show_about(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("关于 Termius 汉化工具")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=22)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Termius 一键汉化工具", font=("Arial", 14, "bold")).pack(pady=(0, 8))
        ttk.Label(frame, text=f"版本 {VERSION}").pack()
        ttk.Label(frame, text="自动查找、下载、备份并应用 Termius 中文汉化包。", wraplength=380).pack(pady=10)
        ttk.Label(frame, text="启动时自动检查更新；是否下载由用户选择。", wraplength=380).pack(pady=2)
        link = ttk.Label(frame, text=f"github.com/{TOOL_REPO}", foreground="blue", cursor="hand2")
        link.pack(pady=5)
        link.bind("<Button-1>", lambda _event: webbrowser.open(f"https://github.com/{TOOL_REPO}"))
        ttk.Label(frame, text="汉化包来源：ArcSurge/Termius-Pro-zh_CN").pack(pady=5)
        ttk.Button(frame, text="关闭", command=dialog.destroy).pack(pady=(12, 0))
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")


def main():
    if "--health-check" in sys.argv:
        releases = [
            {"tag_name": "v1.3.0-beta", "name": "Beta", "prerelease": True},
            {"tag_name": "v1.2.3", "name": "Termius 1.2.3", "prerelease": False},
        ]
        matches = filter_releases(releases, "1.2")
        if (
            not matches
            or get_default_release(releases) != releases[1]
            or format_size(1024 * 1024) != "1.0 MB"
            or not is_newer_version("v1.2.0", "1.1.0")
        ):
            return 1
        print(f"termius-chinese {VERSION}: OK")
        return 0

    root = tk.Tk()
    TermiusChineseApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
