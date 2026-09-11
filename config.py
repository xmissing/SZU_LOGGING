"""全局配置类，集中管理所有可调参数。"""

import os
import sys
import json
import tempfile
from pathlib import Path


# 查询时间范围选项（dayy 参数编码值 -> 显示名称）
TIME_RANGES = [
    {"value": "7#一周内", "label": "一周内"},
    {"value": "30#1个月内", "label": "1个月内"},
    {"value": "90#3个月内", "label": "3个月内"},
    {"value": "180#半年内", "label": "半年内"},
    {"value": "365#1年内", "label": "1年内"},
]

# 邮件发送模式
EMAIL_SEND_MODES = {
    "none": "不发送",
    "new_only": "仅发送新数据",
    "all": "发送全部数据",
}


class Config:
    """运行时配置，由 Web 前端填充后传递给各模块。"""

    # ---- 账号 ----
    ACCOUNT = ""
    PASSWORD = ""
    QUOTES = ""

    # ---- 查询时间范围 ----
    TIME_RANGE = "30#1个月内"

    # ---- MySQL ----
    MYSQL_ENABLED = False
    MYSQL_HOST = "localhost"
    MYSQL_PORT = 3306
    MYSQL_USER = "root"
    MYSQL_PASSWORD = ""
    MYSQL_DATABASE = "szu_board"

    # ---- 邮件 ----
    EMAIL_ENABLED = False
    SMTP_SERVER = "smtp.qq.com"
    SMTP_PORT = 465
    SENDER_EMAIL = ""
    SENDER_PASSWORD = ""
    RECEIVER_EMAIL = ""
    EMAIL_SEND_MODE = "new_only"  # none / new_only / all

    # ---- 文件路径 ----
    BASE_DIR = Path(__file__).resolve().parent
    COOKIES_FILE = str(Path(tempfile.gettempdir()) / "szu_cookies.json")
    # exe 同目录的 config.json（用户手动配置），优先级最高
    _exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else BASE_DIR
    LOCAL_CONFIG_FILE = str(_exe_dir / "config.json")
    SETTINGS_FILE = str(Path.home() / ".szu_board_monitor" / "settings.json")

    @classmethod
    def save_settings(cls):
        """将配置持久化到 settings.json。"""
        data = {
            "account": cls.ACCOUNT,
            "keyword": cls.QUOTES,
            "time_range": cls.TIME_RANGE,
            "mysql_enabled": cls.MYSQL_ENABLED,
            "mysql_host": cls.MYSQL_HOST,
            "mysql_port": cls.MYSQL_PORT,
            "mysql_user": cls.MYSQL_USER,
            "mysql_password": cls.MYSQL_PASSWORD,
            "mysql_database": cls.MYSQL_DATABASE,
            "email_enabled": cls.EMAIL_ENABLED,
            "sender_email": cls.SENDER_EMAIL,
            "sender_password": cls.SENDER_PASSWORD,
            "receiver_email": cls.RECEIVER_EMAIL,
            "email_send_mode": cls.EMAIL_SEND_MODE,
        }
        try:
            settings_dir = Path(cls.SETTINGS_FILE).parent
            settings_dir.mkdir(parents=True, exist_ok=True)
            with open(cls.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def load_settings(cls):
        """读取配置：优先 exe 同目录 config.json，其次用户主目录 settings.json。"""
        config_path = None
        if os.path.exists(cls.LOCAL_CONFIG_FILE):
            config_path = cls.LOCAL_CONFIG_FILE
        elif os.path.exists(cls.SETTINGS_FILE):
            config_path = cls.SETTINGS_FILE
        else:
            return
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cls.ACCOUNT = data.get("account", "")
            cls.QUOTES = data.get("keyword", "")
            cls.TIME_RANGE = data.get("time_range", "30#1个月内")
            cls.MYSQL_ENABLED = data.get("mysql_enabled", False)
            cls.MYSQL_HOST = data.get("mysql_host", "localhost")
            cls.MYSQL_PORT = data.get("mysql_port", 3306)
            cls.MYSQL_USER = data.get("mysql_user", "root")
            cls.MYSQL_PASSWORD = data.get("mysql_password", "")
            cls.MYSQL_DATABASE = data.get("mysql_database", "szu_board")
            cls.EMAIL_ENABLED = data.get("email_enabled", False)
            cls.SENDER_EMAIL = data.get("sender_email", "")
            cls.SENDER_PASSWORD = data.get("sender_password", "")
            cls.RECEIVER_EMAIL = data.get("receiver_email", "")
            cls.EMAIL_SEND_MODE = data.get("email_send_mode", "new_only")
        except Exception:
            pass

    @classmethod
    def to_dict(cls):
        """导出为字典（脱敏，不包含密码）。"""
        return {
            "account": cls.ACCOUNT,
            "keyword": cls.QUOTES,
            "time_range": cls.TIME_RANGE,
            "time_ranges": TIME_RANGES,
            "mysql_enabled": cls.MYSQL_ENABLED,
            "mysql_host": cls.MYSQL_HOST,
            "mysql_port": cls.MYSQL_PORT,
            "mysql_user": cls.MYSQL_USER,
            "mysql_password": cls.MYSQL_PASSWORD,
            "mysql_database": cls.MYSQL_DATABASE,
            "email_enabled": cls.EMAIL_ENABLED,
            "sender_email": cls.SENDER_EMAIL,
            "sender_password": cls.SENDER_PASSWORD,
            "receiver_email": cls.RECEIVER_EMAIL,
            "email_send_mode": cls.EMAIL_SEND_MODE,
            "email_send_modes": EMAIL_SEND_MODES,
        }
