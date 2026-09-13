"""程序入口：启动 Flask Web 服务器。"""

import sys
import os
import json
import webbrowser
import threading

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app
from config import Config


def ensure_local_config():
    """exe 启动时在同级目录生成 config.json 模板（如不存在）。"""
    if not getattr(sys, 'frozen', False):
        return
    local_cfg = Config.LOCAL_CONFIG_FILE
    if not os.path.exists(local_cfg):
        template = {
            "account": "在此填写深大学号",
            "keyword": "在此填写搜索关键词",
            "time_range": "30#1个月内",
            "mysql_enabled": False,
            "mysql_host": "localhost",
            "mysql_port": 3306,
            "mysql_user": "root",
            "mysql_password": "",
            "mysql_database": "szu_board",
            "email_enabled": False,
            "sender_email": "",
            "sender_password": "",
            "receiver_email": "",
            "email_send_mode": "new_only",
        }
        try:
            with open(local_cfg, "w", encoding="utf-8") as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def open_browser():
    """延迟 1.5 秒后打开浏览器。"""
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    ensure_local_config()
    app = create_app()
    threading.Timer(1.5, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
