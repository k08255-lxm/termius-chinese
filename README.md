# Termius 一键汉化工具

## 📝 简介

这是一个简单易用的 Termius 一键汉化工具，可以帮助您快速将 Termius 软件界面汉化为中文，无需复杂操作，小白也能轻松上手。本工具基于 [ArcSurge/Termius-Pro-zh_CN](https://github.com/ArcSurge/Termius-Pro-zh_CN) 项目的汉化包。

## ✨ 功能特性

- **一键汉化** - 自动下载并应用汉化包
- **多版本选择** - 支持三种汉化模式（仅汉化/汉化+试用/汉化+跳过登录）
- **自动备份** - 自动备份原始文件，确保安全
- **一键恢复** - 支持一键恢复到原始版本
- **多平台支持** - 支持 Windows 和 Linux 系统
- **图形界面** - 简洁直观的操作界面

## 🚀 使用方法

### Windows 用户

1. 下载并解压 `termius_chinese_windows.zip` 文件
   - 您可以从 [GitHub Releases](https://github.com/ArcSurge/Termius-Pro-zh_CN/releases) 页面下载最新版本
   - 如果下载速度慢，可以尝试使用国内镜像站点
   - 下载完成后，右键点击zip文件，选择「解压到当前文件夹」或使用解压软件解压

2. 右键点击 `termius_chinese.exe`，选择「以管理员身份运行」
   - 如果出现"Windows已保护您的电脑"警告，点击"更多信息"，然后点击"仍要运行"
   - 如果出现"无法定位程序输入点"等错误，请确保您的系统已安装最新的Visual C++运行库

### Linux 用户

1. 下载并解压 `termius_chinese_linux.zip` 文件
2. 打开终端，进入解压后的目录
3. 执行以下命令赋予执行权限：
   ```bash
   chmod +x termius_chinese.py
   ```
4. 运行程序：
   ```bash
   sudo python3 termius_chinese.py
   ```
5. 在打开的界面中，确认 Termius 安装路径是否正确
    - 如果软件无法自动检测安装路径，请点击「浏览」按钮手动选择
    - 默认路径通常为 `/opt/Termius`

6. 选择需要的汉化版本：
   - **仅汉化**：适合已有会员的用户
   - **汉化+试用**：消除升级提示，适合试用用户
   - **汉化+跳过登录**：适合离线用户

7. 点击「应用汉化」按钮
    - 程序会自动下载汉化包并应用
    - 如果下载失败，请检查网络连接或参考常见问题中的解决方案

8. 等待下载和安装完成
    - 安装过程中请勿关闭程序
    - 如果出现权限不足的提示，请确保使用sudo运行

9. 重启 Termius 即可看到中文界面
    - 如果汉化后无法启动，请使用「恢复原版」功能

## 📋 使用须知

1. **请在使用前关闭 Termius 软件**
2. Windows 用户需要以管理员身份运行
3. Linux 用户需要使用 sudo 权限运行
4. 程序会自动备份原始文件，您可以随时恢复
5. 汉化后可能会影响 Termius 的自动更新功能

## ❓ 常见问题

### 汉化后无法启动 Termius

请使用本工具的「恢复原版」功能，或手动将备份文件（通常位于 resources 目录下，名为 app.asar.bak.xxxxxxxxxx）重命名为 app.asar。

### 找不到 Termius 安装目录

Termius 的默认安装目录通常为：
- Windows: `C:\Users\用户名\AppData\Local\Programs\Termius`
- Linux: `/opt/Termius`

您可以通过「浏览」按钮手动选择正确的安装目录。

### 下载汉化包失败

请检查您的网络连接，或者直接访问 [GitHub 项目页面](https://github.com/ArcSurge/Termius-Pro-zh_CN/releases) 下载对应的汉化包，然后手动替换。

### 权限不足无法替换文件

- Windows 用户请确保以管理员身份运行程序
- Linux 用户请使用 sudo 权限运行程序

## 📷 界面预览

![程序界面预览](screenshot.png)

## 📜 免责声明

- 本工具仅用于学习和研究，请勿用于商业用途
- 使用本工具产生的任何问题，开发者不承担任何责任
- 本工具不会收集任何个人信息或数据

## 🙏 致谢

- [ArcSurge/Termius-Pro-zh_CN](https://github.com/ArcSurge/Termius-Pro-zh_CN) - 提供汉化包
- 所有为汉化包做出贡献的开发者

## 📄 许可证

本项目采用 MIT 许可证，详情请参阅 [LICENSE](LICENSE) 文件。