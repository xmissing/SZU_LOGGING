"""程序入口：启动 Flask Web 服务器。"""

import sys
import os
import webbrowser
import threading

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app


def open_browser():
    """延迟 1.5 秒后打开浏览器。"""
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    app = create_app()
    threading.Timer(1.5, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
