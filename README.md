# 深圳大学公告监控系统

一个基于 Flask Web 界面的深大公告自动抓取、去重存储、邮件通知、定时监控工具。

## 功能特点

- 🔍 **关键词搜索**：按关键词搜索公告，支持自定义时间范围
- ⏰ **定时自动运行**：每日指定时间自动抓取，无需手动操作
- 🆕 **新旧数据区分**：自动识别新公告和已存公告，分 Tab 展示
- 💾 **数据库存储**：可选 MySQL 存储，自动去重
- 📧 **邮件通知**：可选邮件推送，支持「仅新数据」或「全部数据」模式
- 🌐 **Web 界面**：浏览器访问，界面美观，操作直观
- ⚙️ **配置弹窗**：数据库、邮箱配置以弹窗形式管理，主界面简洁

## 快速开始（推荐：免安装版）

### 方式一：下载免安装版（推荐新手）

1. 从 [Releases](https://github.com/xmissing/SZU_LOGGING/releases) 下载最新的 `SZU_Board_Monitor_vX.X.zip`
2. 解压到任意目录
3. 双击 `启动.bat` 即可运行
4. 浏览器会自动打开 http://127.0.0.1:5000/

> 免安装版已内置 Python 环境和所有依赖，无需额外安装任何软件。

### 方式二：开发者方式

#### 环境要求

- Python 3.8+
- Chrome 浏览器（DrissionPage 调用）
- **必须连接校园网（插网线）**：本工具通过访问深大内网网站抓取公告，电脑必须通过有线方式连接校园网。使用 WiFi 连接校园网或开启 WebVPN 均无法正常使用。

#### 安装依赖

```bash
pip install -r requirements.txt
```

#### 启动

```bash
python main.py
```

启动后会自动打开浏览器，访问 http://127.0.0.1:5000/

## 使用说明

### 1. 基本搜索

- 填写深大统一认证**账号**和**密码**
- 输入要监控的**关键词**
- 选择**查询时间范围**（一周/1个月/3个月/半年/1年）
- 选择**邮件发送模式**
- 点击「运行爬虫」

> ⚠️ 首次登录时会弹出浏览器窗口，请手动输入验证码完成登录。Cookie 会保存 12 小时，期间无需重复登录。

### 2. 定时自动运行

在「定时任务」卡片中：

- 开启定时任务开关
- 设置每日运行时间（如 `08:00`）
- 填写搜索关键词和时间范围
- 选择邮件发送模式
- 点击「保存配置」

程序会在每天指定时间自动运行爬虫，并根据配置发送邮件通知。

> 💡 定时任务需要程序保持运行状态。关闭程序后定时任务停止。

### 3. 数据库配置

点击右上角「数据库配置」按钮：

- 勾选「启用数据库存储」
- 填写 MySQL 连接信息
- 保存后，爬取的数据会自动存入数据库并去重

### 4. 邮箱配置

点击右上角「邮箱配置」按钮：

- 勾选「启用邮件通知」
- 填写发件人邮箱和 SMTP 授权码（以 QQ 邮箱为例，需在邮箱设置中开启 SMTP 服务）
- 填写收件人邮箱
- 保存

> **注意**：授权码不是邮箱登录密码，需在邮箱设置 → 账户 → SMTP 服务中获取。

### 5. 查看数据

运行爬虫后，数据列表分为三个 Tab：

| Tab | 说明 |
|-----|------|
| 全部数据 | 本次抓取到的所有公告 |
| 🆕 新数据 | 数据库中不存在的新增公告 |
| 📦 已存数据 | 数据库中已有的公告 |

点击标题或「查看」按钮可查看公告详情。

## 配置文件

程序配置保存在以下位置（优先级从高到低）：

1. **程序同目录 `config.json`**：手动创建，优先级最高
2. **用户目录 `~/.szu_board_monitor/settings.json`**：Web 界面保存的配置

首次使用可复制 `config.example.json` 为 `config.json`，然后填写相关信息。

## 项目结构

```
SZU_LOGGING/
├── 启动.bat                # 启动脚本（双击运行）
├── main.py                 # 入口：启动 Flask
├── config.py               # 配置管理（含持久化）
├── config.example.json     # 配置模板
├── requirements.txt        # 依赖清单
├── README.md               # 本文档
├── core/                   # 核心逻辑
│   ├── crawler.py          # 爬虫核心
│   ├── database.py         # 数据库操作
│   └── notifier.py         # 邮件通知
└── web/                    # Web 层
    ├── app.py              # Flask 后端
    ├── templates/
    │   └── index.html      # 主页 HTML
    └── static/
        ├── css/style.css   # 样式
        └── js/app.js       # 前端逻辑
```

## 打包为免安装版

### 准备工作

1. 安装 Python 3.8+
2. 安装依赖：`pip install -r requirements.txt`
3. 安装 PyInstaller：`pip install pyinstaller`

### 方法一：单文件 exe

```bash
pyinstaller --name "SZU公告监控" --onefile --add-data "web/templates;web/templates" --add-data "web/static;web/static" main.py
```

### 方法二：免安装版（含 Python 环境，推荐）

1. 下载 [embeddable Python](https://www.python.org/downloads/windows/)
2. 解压到项目目录下的 `python/` 文件夹
3. 在 `python/` 目录中安装依赖：
   ```bash
   python\python.exe -m pip install -r requirements.txt --target python\Lib\site-packages
   ```
4. 将以下文件打包成 zip：
   - `启动.bat`
   - `config.example.json`
   - `README.md`
   - `main.py`
   - `config.py`
   - `requirements.txt`
   - `core/` 目录
   - `web/` 目录
   - `python/` 目录（内嵌 Python 环境）

## 常见问题

**Q: 为什么登录时会弹出浏览器窗口？**
A: 深大统一认证需要输入验证码，程序会弹出浏览器让你手动输入。登录成功后 Cookie 会保存 12 小时，期间无需重复登录。

**Q: 密码安全吗？**
A: 密码仅用于登录深大官方网站，不会上传到任何第三方服务器。配置中的密码保存在本地。

**Q: 支持哪些邮箱？**
A: 默认使用 QQ 邮箱 SMTP 服务器，其他邮箱（163、Gmail 等）可在配置中修改 SMTP 服务器和端口。

**Q: 数据保存在哪里？**
A: 启用数据库后保存在 MySQL 中；未启用则仅在本次运行内存中，关闭程序即消失。

**Q: 定时任务需要一直开着程序吗？**
A: 是的，程序需要保持运行状态才能执行定时任务。可以将程序最小化到后台运行。

**Q: 怎么开机自启动？**
A: 将 `启动.bat` 的快捷方式放入 `shell:startup` 目录（Win+R 输入该命令打开），即可实现开机自动启动。
