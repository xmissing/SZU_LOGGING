"""Flask 后端：提供页面路由和 REST API。

路由总览：
  GET  /                   主页面
  GET  /api/config          获取当前配置
  POST /api/config          保存配置（数据库 / 邮件）
  POST /api/crawler/run     启动爬虫
  GET  /api/crawler/status  查询爬虫运行状态
  GET  /api/data            分页查询已存储数据
  GET  /api/data/<id>       查询单条详情
  POST /api/email/send      手动发送邮件
"""

import threading
import time
from datetime import datetime, timedelta

from flask import Flask, render_template, jsonify, request

from config import Config, TIME_RANGES, EMAIL_SEND_MODES
from core.crawler import SzuCrawler
from core.database import DatabaseManager

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

# 全局状态
crawler_state = {
    "running": False,
    "logs": [],
    "results": None,       # 最近一次抓取的全部数据
    "error": None,
    "started_at": None,
    "finished_at": None,
}

# 定时调度器状态
scheduler_state = {
    "running": False,          # 调度器线程是否运行中
    "next_run_time": None,     # 下次运行时间（ISO 格式字符串）
    "last_run_result": None,   # 最近一次运行结果：success / error / None
    "last_run_time": None,     # 最近一次运行时间
    "last_run_error": None,    # 最近一次运行错误信息
    "last_run_count": 0,       # 最近一次抓取数量
}

_scheduler_stop_event = threading.Event()


def _calculate_next_run(target_time_str):
    """计算下一次运行时间。target_time_str 格式为 'HH:MM'。"""
    now = datetime.now()
    try:
        hour, minute = map(int, target_time_str.split(":"))
    except (ValueError, AttributeError):
        hour, minute = 8, 0

    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def _scheduler_log(message):
    """调度器日志回调，写入爬虫日志区（带前缀）。"""
    _log_callback(f"[定时任务] {message}")


def _run_scheduled_crawler():
    """执行定时触发的爬虫任务。"""
    if crawler_state["running"]:
        scheduler_state["last_run_result"] = "error"
        scheduler_state["last_run_error"] = "爬虫正在运行中，跳过本次定时任务"
        scheduler_state["last_run_time"] = datetime.now().isoformat()
        return

    # 使用保存的配置
    account = Config.ACCOUNT
    password = Config.PASSWORD
    keyword = Config.SCHEDULER_KEYWORD or Config.QUOTES
    time_range = Config.SCHEDULER_TIME_RANGE
    email_send_mode = Config.SCHEDULER_EMAIL_MODE

    if not account or not password or not keyword:
        scheduler_state["last_run_result"] = "error"
        scheduler_state["last_run_error"] = "账号、密码或关键词未配置，无法执行定时任务"
        scheduler_state["last_run_time"] = datetime.now().isoformat()
        _scheduler_log("跳过：账号、密码或关键词未配置")
        return

    _scheduler_log("定时触发，开始运行爬虫...")

    try:
        Config.QUOTES = keyword
        Config.TIME_RANGE = time_range
        Config.EMAIL_SEND_MODE = email_send_mode

        crawler_state["running"] = True
        crawler_state["logs"] = []
        crawler_state["results"] = None
        crawler_state["error"] = None
        crawler_state["started_at"] = datetime.now().isoformat()
        crawler_state["finished_at"] = None

        crawler = SzuCrawler(Config, _log_callback)
        results = crawler.run()
        crawler_state["results"] = results

        scheduler_state["last_run_result"] = "success"
        scheduler_state["last_run_error"] = None
        scheduler_state["last_run_count"] = len(results) if results else 0
        _scheduler_log(f"定时任务完成，共抓取 {len(results) if results else 0} 条")
    except Exception as e:
        crawler_state["error"] = str(e)
        scheduler_state["last_run_result"] = "error"
        scheduler_state["last_run_error"] = str(e)
        scheduler_state["last_run_count"] = 0
        _scheduler_log(f"运行出错：{e}")
    finally:
        crawler_state["running"] = False
        crawler_state["finished_at"] = datetime.now().isoformat()
        scheduler_state["last_run_time"] = datetime.now().isoformat()


def _scheduler_thread():
    """调度器主线程：循环检测时间，到达指定时间触发爬虫。"""
    _scheduler_log("调度器已启动")

    while not _scheduler_stop_event.is_set():
        if not Config.SCHEDULER_ENABLED:
            # 未启用时，每 10 秒检查一次配置变化
            scheduler_state["next_run_time"] = None
            time.sleep(10)
            continue

        target_time = _calculate_next_run(Config.SCHEDULER_TIME)
        scheduler_state["next_run_time"] = target_time.isoformat()

        # 计算距离下次运行的秒数
        now = datetime.now()
        seconds_until = (target_time - now).total_seconds()

        if seconds_until <= 0:
            # 刚好到点或已过，立即执行
            _run_scheduled_crawler()
            # 执行完后重新计算下一次
            continue

        # 分段 sleep，每 30 秒醒来一次检查配置变化和停止信号
        sleep_interval = min(30, seconds_until)
        if _scheduler_stop_event.wait(timeout=sleep_interval):
            break

    _scheduler_log("调度器已停止")


def _log_callback(message):
    """爬虫日志回调，写入全局状态。"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = {"time": timestamp, "message": message}
    crawler_state["logs"].append(entry)
    if len(crawler_state["logs"]) > 500:
        crawler_state["logs"] = crawler_state["logs"][-200:]


def _run_crawler_thread(account, password, keyword, time_range, email_send_mode):
    """爬虫工作线程。"""
    Config.ACCOUNT = account
    Config.PASSWORD = password
    Config.QUOTES = keyword
    Config.TIME_RANGE = time_range
    Config.EMAIL_SEND_MODE = email_send_mode
    Config.save_settings()

    crawler_state["running"] = True
    crawler_state["logs"] = []
    crawler_state["results"] = None
    crawler_state["error"] = None
    crawler_state["started_at"] = datetime.now().isoformat()
    crawler_state["finished_at"] = None

    try:
        crawler = SzuCrawler(Config, _log_callback)
        results = crawler.run()
        crawler_state["results"] = results
    except Exception as e:
        crawler_state["error"] = str(e)
        _log_callback(f"运行出错：{e}")
    finally:
        crawler_state["running"] = False
        crawler_state["finished_at"] = datetime.now().isoformat()


# ======================================================================
#  页面路由
# ======================================================================
@app.route("/")
def index():
    return render_template("index.html")


# ======================================================================
#  API 路由
# ======================================================================
@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(Config.to_dict())


@app.route("/api/config", methods=["POST"])
def save_config():
    data = request.json

    if "mysql_enabled" in data:
        Config.MYSQL_ENABLED = bool(data["mysql_enabled"])
    if "mysql_host" in data:
        Config.MYSQL_HOST = data["mysql_host"]
    if "mysql_port" in data:
        Config.MYSQL_PORT = int(data["mysql_port"])
    if "mysql_user" in data:
        Config.MYSQL_USER = data["mysql_user"]
    if "mysql_password" in data:
        Config.MYSQL_PASSWORD = data["mysql_password"]
    if "mysql_database" in data:
        Config.MYSQL_DATABASE = data["mysql_database"]
    if "email_enabled" in data:
        Config.EMAIL_ENABLED = bool(data["email_enabled"])
    if "sender_email" in data:
        Config.SENDER_EMAIL = data["sender_email"]
    if "sender_password" in data:
        Config.SENDER_PASSWORD = data["sender_password"]
    if "receiver_email" in data:
        Config.RECEIVER_EMAIL = data["receiver_email"]
    if "email_send_mode" in data:
        Config.EMAIL_SEND_MODE = data["email_send_mode"]

    Config.save_settings()
    return jsonify({"ok": True, "config": Config.to_dict()})


@app.route("/api/database/test", methods=["POST"])
def test_db_connection():
    """测试数据库连接，返回详细错误信息。"""
    data = request.json
    host = data.get("host", "localhost")
    port = int(data.get("port", 3306))
    user = data.get("user", "root")
    password = data.get("password", "")
    database = data.get("database", "szu_board")

    import pymysql
    try:
        conn = pymysql.connect(
            host=host, port=port, user=user,
            password=password, charset="utf8mb4",
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database} "
                       f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.close()

        conn = pymysql.connect(
            host=host, port=port, user=user,
            password=password, database=database, charset="utf8mb4",
        )
        conn.close()
        return jsonify({"ok": True, "message": "连接成功"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@app.route("/api/crawler/run", methods=["POST"])
def run_crawler():
    if crawler_state["running"]:
        return jsonify({"ok": False, "error": "爬虫正在运行中，请等待完成"}), 409

    data = request.json
    account = data.get("account", "").strip()
    password = data.get("password", "").strip()
    keyword = data.get("keyword", "").strip()
    time_range = data.get("time_range", "30#1个月内")
    email_send_mode = data.get("email_send_mode", "new_only")

    if not account or not password or not keyword:
        return jsonify({"ok": False, "error": "账号、密码和关键词为必填项"}), 400

    thread = threading.Thread(
        target=_run_crawler_thread,
        args=(account, password, keyword, time_range, email_send_mode),
        daemon=True,
    )
    thread.start()

    return jsonify({"ok": True, "message": "爬虫已启动"})


@app.route("/api/crawler/status", methods=["GET"])
def crawler_status():
    return jsonify({
        "running": crawler_state["running"],
        "logs": crawler_state["logs"],
        "results": crawler_state["results"],
        "error": crawler_state["error"],
        "started_at": crawler_state["started_at"],
        "finished_at": crawler_state["finished_at"],
    })


@app.route("/api/data", methods=["GET"])
def get_data():
    """分页查询数据库中已存储的公告。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    keyword = request.args.get("keyword", None)

    if not Config.MYSQL_ENABLED:
        return jsonify({
            "ok": True,
            "data": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "message": "数据库未启用",
        })

    db = DatabaseManager(Config)
    rows, total = db.get_announcements(page, per_page, keyword)
    return jsonify({
        "ok": True,
        "data": rows,
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@app.route("/api/data/detail", methods=["GET"])
def get_detail():
    """查询单条公告详情，ID 通过 query 参数传递（避免 ID 中的 ? 破坏 URL）。"""
    announcement_id = request.args.get("id", "")
    if not announcement_id:
        return jsonify({"ok": False, "error": "缺少公告 ID"}), 400

    # 先从上次抓取结果中找
    if crawler_state["results"]:
        for item in crawler_state["results"]:
            if item.get("announcement_id") == announcement_id:
                return jsonify({"ok": True, "data": item})

    # 再从数据库查
    if Config.MYSQL_ENABLED:
        db = DatabaseManager(Config)
        row = db.get_announcement_detail(announcement_id)
        if row:
            return jsonify({"ok": True, "data": row})

    return jsonify({"ok": False, "error": "未找到该公告"}), 404


@app.route("/api/email/send", methods=["POST"])
def send_email():
    """手动触发邮件发送（使用上次抓取结果）。"""
    from core.notifier import EmailNotifier

    data = request.json
    mode = data.get("mode", "new_only")

    results = crawler_state.get("results") or []
    if not results:
        return jsonify({"ok": False, "error": "暂无抓取数据，请先运行爬虫"}), 400

    Config.EMAIL_SEND_MODE = mode
    notifier = EmailNotifier(Config, _log_callback)

    new_data = [d for d in results if d.get("is_new")]
    old_data = [d for d in results if not d.get("is_new")]

    if mode == "new_only":
        notifier.send_by_mode(results, new_data)
    elif mode == "all":
        notifier.send_by_mode(results, new_data)
    else:
        return jsonify({"ok": False, "error": "不支持的发送模式"}), 400

    return jsonify({"ok": True, "message": f"邮件已发送（模式：{mode}）"})


# ======================================================================
#  定时任务 API
# ======================================================================
@app.route("/api/scheduler", methods=["GET"])
def get_scheduler_status():
    """获取定时任务状态和配置。"""
    return jsonify({
        "enabled": Config.SCHEDULER_ENABLED,
        "scheduler_time": Config.SCHEDULER_TIME,
        "scheduler_keyword": Config.SCHEDULER_KEYWORD,
        "scheduler_time_range": Config.SCHEDULER_TIME_RANGE,
        "scheduler_email_mode": Config.SCHEDULER_EMAIL_MODE,
        "running": scheduler_state["running"],
        "next_run_time": scheduler_state["next_run_time"],
        "last_run_result": scheduler_state["last_run_result"],
        "last_run_time": scheduler_state["last_run_time"],
        "last_run_error": scheduler_state["last_run_error"],
        "last_run_count": scheduler_state["last_run_count"],
        "time_ranges": TIME_RANGES,
        "email_send_modes": EMAIL_SEND_MODES,
    })


@app.route("/api/scheduler", methods=["POST"])
def save_scheduler_config():
    """保存定时任务配置。"""
    data = request.json

    if "scheduler_time" in data:
        Config.SCHEDULER_TIME = data["scheduler_time"]
    if "scheduler_keyword" in data:
        Config.SCHEDULER_KEYWORD = data["scheduler_keyword"]
    if "scheduler_time_range" in data:
        Config.SCHEDULER_TIME_RANGE = data["scheduler_time_range"]
    if "scheduler_email_mode" in data:
        Config.SCHEDULER_EMAIL_MODE = data["scheduler_email_mode"]

    Config.save_settings()
    return jsonify({"ok": True, "message": "定时任务配置已保存"})


@app.route("/api/scheduler/toggle", methods=["POST"])
def toggle_scheduler():
    """开关定时任务。"""
    data = request.json
    enabled = bool(data.get("enabled", False))

    Config.SCHEDULER_ENABLED = enabled
    Config.save_settings()

    return jsonify({
        "ok": True,
        "enabled": Config.SCHEDULER_ENABLED,
        "message": "定时任务已" + ("启用" if enabled else "停用"),
    })


def create_app():
    """工厂函数，供 main.py 调用。"""
    Config.load_settings()

    # 启动调度器线程
    if not scheduler_state["running"]:
        scheduler_state["running"] = True
        t = threading.Thread(target=_scheduler_thread, daemon=True)
        t.start()

    return app
