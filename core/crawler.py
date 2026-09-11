"""爬虫核心模块：登录、Cookie 管理、抓取公告列表与详情。

run() 返回所有抓取到的公告，每条带 is_new 标记，
用于前端区分「新数据」与「已存数据」。
"""

import os
import re
import json
import time
import tempfile
import requests
from pathlib import Path
from urllib.parse import quote

from DrissionPage import ChromiumPage, ChromiumOptions
from lxml import etree

from .database import DatabaseManager
from .notifier import EmailNotifier


class SzuCrawler:
    """深圳大学公告板爬虫，协调 Cookie、数据库与邮件通知。"""

    LOGIN_URL = "https://www1.szu.edu.cn/"
    BOARD_URL = "https://www1.szu.edu.cn/board/"
    SEARCH_URL = "https://www1.szu.edu.cn/board/infolist.asp"
    BOARD_BASE = "https://www1.szu.edu.cn/board/"

    def __init__(self, config, callback=None):
        self.config = config
        self.callback = callback
        self.db = DatabaseManager(config, callback)
        self.notifier = EmailNotifier(config, callback)

    def log(self, message):
        if self.callback:
            self.callback(message)

    # ------------------------------------------------------------------
    #  Cookie 管理
    # ------------------------------------------------------------------
    def save_cookies(self, cookies_dict):
        with open(self.config.COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"cookies": cookies_dict, "timestamp": time.time()},
                f,
                ensure_ascii=False,
                indent=2,
            )

    def load_cookies(self):
        if not os.path.exists(self.config.COOKIES_FILE):
            return None
        try:
            with open(self.config.COOKIES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if time.time() - data.get("timestamp", 0) > 12 * 3600:
                return None
            return data["cookies"]
        except Exception:
            return None

    def get_cookies(self):
        cookies = self.load_cookies()
        if cookies:
            return cookies

        self.log("正在登录...")
        co = ChromiumOptions()
        co.set_browser_path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        co.set_user_data_path(str(Path(tempfile.gettempdir()) / "szu_chrome_data"))
        co.set_local_port(9333)
        co.headless(True)
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-gpu")
        page = ChromiumPage(co)
        try:
            page.get(self.LOGIN_URL)
            page.wait(1)
            page.ele('xpath=//div/input[@id="username"]').input(self.config.ACCOUNT)
            page.wait(1)
            page.ele(
                'xpath=//div[@class="password item"]/input[@id="password"]'
            ).input(self.config.PASSWORD)
            page.wait(1)
            page.ele('xpath=//div/a[@id="login_submit"]').click()
            page.wait(3)
            page.get(self.BOARD_URL)
            page.wait(2)
            all_cookies = page.cookies()
            cookies_dict = {c["name"]: c["value"] for c in all_cookies}
            self.save_cookies(cookies_dict)
            return cookies_dict
        except Exception as e:
            self.log(f"登录失败：{e}")
            return None
        finally:
            page.close()

    def verify_cookies(self, cookies):
        try:
            r = requests.get(self.SEARCH_URL, cookies=cookies, timeout=10)
            return "authserver" not in r.url and r.status_code != 302
        except Exception:
            return False

    # ------------------------------------------------------------------
    #  公告抓取
    # ------------------------------------------------------------------
    def _parse_meta(self, meta_text, extra_text=""):
        """从元信息文本中提取发文学院、发文时间、浏览量。

        页面结构：
          <font color="#808080">计划财务部　2026/8/31 10:34:00</font>
          <font color="#F8F8F8">（张三2026000000 2026/9/8 23:31:51浏览）</font>
        发文学院和发文时间在同一个灰色 font 里，用全角空格分隔。
        浏览量在接近白色的 font 里，格式如 "xxx浏览"。
        """
        author = publish_time = view_count = ""

        # 解析灰色 font：发文学院 + 全角空格 + 发文时间
        if meta_text:
            # 去掉前后空白
            meta_text = meta_text.strip()
            # 用全角空格（\u3000）或多个空格分割
            parts = re.split(r"[\u3000\s]{2,}", meta_text)
            if len(parts) >= 2:
                author = parts[0].strip()
                publish_time = parts[1].strip()
            else:
                # 退而求其次：尝试匹配日期时间格式
                time_match = re.search(r"(\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)", meta_text)
                if time_match:
                    publish_time = time_match.group(1).strip()
                    author = meta_text[:time_match.start()].strip().rstrip("　 ")

        # 解析浏览量（从隐藏的白色 font 里提取，如 "xxx浏览"）
        if extra_text:
            view_match = re.search(r"(\d+)\s*浏览", extra_text)
            if view_match:
                view_count = view_match.group(1)

        return author, publish_time, view_count

    def _fetch_detail(self, session, headers, cookies, announcement_id):
        """抓取单条公告详情页，返回结构化字典。"""
        url = self.BOARD_BASE + announcement_id
        resp = session.get(url, headers=headers, cookies=cookies)
        resp.encoding = "gbk"
        if resp.status_code != 200:
            return None

        tree = etree.HTML(resp.text)
        content_nodes = tree.xpath('//tr/td/p/text()')
        title_nodes = tree.xpath('//td[@align="center"]/span/text()')

        # 灰色 font：发文学院 + 发文时间（同一个节点，全角空格分隔）
        meta_gray = tree.xpath('//td[@align="center"]//font[@color="#808080"]/text()')
        # 接近白色的 font：隐藏的浏览量等信息
        meta_light = tree.xpath('//td[@align="center"]//font[contains(@color, "#F8F8")]/text()')

        author, publish_time, view_count = "", "", ""
        if meta_gray:
            meta_text = meta_gray[0].strip()
            extra = " ".join(meta_light) if meta_light else ""
            author, publish_time, view_count = self._parse_meta(meta_text, extra)

        return {
            "announcement_id": announcement_id,
            "title": title_nodes[0] if title_nodes else "",
            "content": "".join(content_nodes).strip() if content_nodes else "",
            "author": author,
            "publish_time": publish_time,
            "view_count": view_count,
            "url": url,
            "keyword": self.config.QUOTES,
        }

    def run(self):
        """执行完整爬取流程。

        返回列表，每条包含 is_new 字段：
        - True=新数据，False=已存在（数据库启用时）
        - None=未启用数据库，不区分新旧
        同时触发邮件通知（根据 EMAIL_SEND_MODE 决定发送内容）。
        """
        self.log(f"开始抓取，关键词：{self.config.QUOTES}，时间范围：{self.config.TIME_RANGE}")

        if self.config.MYSQL_ENABLED:
            if not self.db.init_database():
                self.log("数据库连接失败，本次跳过数据库功能")
                self.config.MYSQL_ENABLED = False

        cookies = self.get_cookies()
        if not cookies or not self.verify_cookies(cookies):
            self.log("Cookie 失效，重新获取...")
            cookies = self.get_cookies()
            if not cookies:
                self.log("获取 Cookie 失败")
                return []

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        dayy_gbk = quote(self.config.TIME_RANGE, encoding="gbk")
        search_type_gbk = quote("标题", encoding="gbk")
        keyword_gbk = quote(self.config.QUOTES, encoding="gbk")
        url = (
            f"{self.SEARCH_URL}?dayy={dayy_gbk}&from_username=&search_type={search_type_gbk}"
            f"&keyword={keyword_gbk}&searchb1=%CB%D1%CB%F7"
        )

        session = requests.Session()
        response = session.post(url, headers=headers, cookies=cookies)
        response.encoding = "gbk"
        if response.status_code != 200:
            self.log(f"请求失败：{response.status_code}")
            return []

        tree = etree.HTML(response.text)
        ids = tree.xpath('//tr/td[@align="left"]/a/@href')
        titles = tree.xpath('//tr/td[@align="left"]/a/text()')

        self.log(f"找到 {len(ids)} 条公告")

        # 预取已存 ID 集合，减少逐条查询
        existing_ids = set()
        if self.config.MYSQL_ENABLED:
            existing_ids = set(self.db.get_all_announcements())

        all_data = []
        new_data = []

        for idx, (announcement_id, title) in enumerate(zip(ids, titles), 1):
            self.log(f"  处理 {idx}/{len(ids)}")

            data = self._fetch_detail(session, headers, cookies, announcement_id)
            if not data:
                continue
            if not data["title"]:
                data["title"] = title

            if self.config.MYSQL_ENABLED:
                is_new = announcement_id not in existing_ids
                data["is_new"] = is_new
                if is_new:
                    self.db.save_announcement(data)
                    new_data.append(data)
                    self.log(f"    新增：{data['title'][:30]}...")
                else:
                    self.log(f"    已存在：{data['title'][:30]}...")
            else:
                data["is_new"] = None
                self.log(f"    已抓取：{data['title'][:30]}...")

            all_data.append(data)

        if self.config.MYSQL_ENABLED:
            self.log(f"完成！共抓取 {len(all_data)} 条，其中新增 {len(new_data)} 条")
        else:
            self.log(f"完成！共抓取 {len(all_data)} 条（数据库未启用）")

        # 邮件通知：根据用户选择的模式发送
        if self.config.EMAIL_ENABLED:
            self.notifier.send_by_mode(all_data, new_data)

        return all_data

    def get_stored_data(self, page=1, per_page=20):
        """查询数据库中已存储的公告（分页）。"""
        return self.db.get_announcements(page, per_page, self.config.QUOTES or None)
