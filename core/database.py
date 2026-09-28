"""数据库操作模块：建表、查重、插入公告、分页查询。"""

import pymysql


class DatabaseManager:
    """封装 MySQL 连接、建表、查重与写入逻辑。"""

    def __init__(self, config, callback=None):
        self.config = config
        self.callback = callback

    def log(self, message):
        if self.callback:
            self.callback(message)

    def get_connection(self):
        if not self.config.MYSQL_ENABLED:
            return None
        try:
            return pymysql.connect(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                database=self.config.MYSQL_DATABASE,
                charset="utf8mb4",
            )
        except Exception as e:
            self.log(f"数据库连接失败：{e}")
            return None

    def init_database(self):
        """创建数据库和表（如果不存在）。"""
        if not self.config.MYSQL_ENABLED:
            return True
        try:
            conn = pymysql.connect(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                charset="utf8mb4",
            )
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {self.config.MYSQL_DATABASE} "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            conn.close()

            conn = self.get_connection()
            if not conn:
                return False
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS board_announcements (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    announcement_id VARCHAR(100) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    content TEXT,
                    author VARCHAR(200),
                    publish_time VARCHAR(200),
                    view_count VARCHAR(50),
                    url VARCHAR(500),
                    keyword VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_announcement_id (announcement_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.log(f"数据库初始化失败：{e}")
            return False

    def check_exists(self, announcement_id):
        if not self.config.MYSQL_ENABLED:
            return False
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM board_announcements WHERE announcement_id = %s",
                (announcement_id,),
            )
            return cursor.fetchone() is not None
        except Exception:
            return False
        finally:
            conn.close()

    def save_announcement(self, data):
        if not self.config.MYSQL_ENABLED:
            return True
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO board_announcements
                (announcement_id, title, content, author, publish_time, view_count, url, keyword)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title), content = VALUES(content),
                    author = VALUES(author), publish_time = VALUES(publish_time),
                    view_count = VALUES(view_count), url = VALUES(url)
                """,
                (
                    data.get("announcement_id"),
                    data.get("title"),
                    data.get("content"),
                    data.get("author"),
                    data.get("publish_time"),
                    data.get("view_count"),
                    data.get("url"),
                    data.get("keyword"),
                ),
            )
            conn.commit()
            return True
        except Exception as e:
            self.log(f"保存失败：{e}")
            return False
        finally:
            conn.close()

    def get_announcements(self, page=1, per_page=20, keyword_filter=None):
        """分页查询已存储的公告，返回 (rows, total)。"""
        if not self.config.MYSQL_ENABLED:
            return [], 0
        conn = self.get_connection()
        if not conn:
            return [], 0
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            offset = (page - 1) * per_page

            where = ""
            params = []
            if keyword_filter:
                where = " WHERE keyword = %s"
                params.append(keyword_filter)

            cursor.execute(f"SELECT COUNT(*) as cnt FROM board_announcements{where}", params)
            total = cursor.fetchone()["cnt"]

            query = f"""
                SELECT announcement_id, title, content, author,
                       publish_time, view_count, url, keyword,
                       created_at, updated_at
                FROM board_announcements{where}
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, params + [per_page, offset])
            rows = cursor.fetchall()
            return rows, total
        except Exception as e:
            self.log(f"查询失败：{e}")
            return [], 0
        finally:
            conn.close()

    def get_all_announcements(self):
        """获取全部已存储公告（不分页），用于本地去重对比。"""
        if not self.config.MYSQL_ENABLED:
            return []
        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(
                "SELECT announcement_id FROM board_announcements"
            )
            return [row["announcement_id"] for row in cursor.fetchall()]
        except Exception:
            return []
        finally:
            conn.close()

    def get_existing_titles(self):
        """获取全部已存储公告的标题集合，用于按标题去重。"""
        if not self.config.MYSQL_ENABLED:
            return set()
        conn = self.get_connection()
        if not conn:
            return set()
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT title FROM board_announcements")
            return {row["title"] for row in cursor.fetchall()}
        except Exception:
            return set()
        finally:
            conn.close()

    def search_by_keyword(self, keyword, time_range=None):
        """在数据库中按关键词搜索已存储的公告。
        
        Args:
            keyword: 搜索关键词，为空则返回全部
            time_range: 时间范围值如 "7#一周内"，None 则不限时间
        Returns:
            匹配的公告列表
        """
        if not self.config.MYSQL_ENABLED:
            return []
        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            where_parts = []
            params = []
            
            if keyword:
                where_parts.append("title LIKE %s")
                params.append(f"%{keyword}%")
            
            if time_range:
                days = self._parse_time_range_days(time_range)
                if days:
                    where_parts.append(
                        "publish_time >= DATE_FORMAT(DATE_SUB(NOW(), INTERVAL %s DAY), '%%Y/%%m/%%d')"
                    )
                    params.append(days)
            
            where_clause = " WHERE " + " AND ".join(where_parts) if where_parts else ""
            
            query = f"""
                SELECT announcement_id, title, content, author,
                       publish_time, view_count, url, keyword,
                       created_at, updated_at
                FROM board_announcements{where_clause}
                ORDER BY publish_time DESC
            """
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            self.log(f"数据库搜索失败：{e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def _parse_time_range_days(time_range_str):
        """从时间范围字符串中提取天数。"""
        if not time_range_str:
            return None
        try:
            return int(time_range_str.split("#")[0])
        except (ValueError, IndexError):
            return None

    def get_announcements_grouped_by_date(self, keyword=None, time_range=None):
        """按发布日期分组查询公告。
        
        Returns:
            {"2026/09/28": [公告列表], "2026/09/27": [...], ...}
        """
        if not self.config.MYSQL_ENABLED:
            return {}
        conn = self.get_connection()
        if not conn:
            return {}
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            where_parts = []
            params = []
            
            if keyword:
                where_parts.append("title LIKE %s")
                params.append(f"%{keyword}%")
            
            if time_range:
                days = self._parse_time_range_days(time_range)
                if days:
                    where_parts.append(
                        "publish_time >= DATE_FORMAT(DATE_SUB(NOW(), INTERVAL %s DAY), '%%Y/%%m/%%d')"
                    )
                    params.append(days)
            
            where_clause = " WHERE " + " AND ".join(where_parts) if where_parts else ""
            
            query = f"""
                SELECT announcement_id, title, content, author,
                       publish_time, view_count, url, keyword,
                       created_at, updated_at
                FROM board_announcements{where_clause}
                ORDER BY publish_time DESC
            """
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            grouped = {}
            for row in rows:
                pub_time = row.get("publish_time", "")
                date_key = pub_time.split(" ")[0] if pub_time else "未知日期"
                if date_key not in grouped:
                    grouped[date_key] = []
                grouped[date_key].append(row)
            
            return grouped
        except Exception as e:
            self.log(f"分组查询失败：{e}")
            return {}
        finally:
            conn.close()

    def get_announcement_detail(self, announcement_id):
        """查询单条公告详情。"""
        if not self.config.MYSQL_ENABLED:
            return None
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(
                "SELECT * FROM board_announcements WHERE announcement_id = %s",
                (announcement_id,),
            )
            return cursor.fetchone()
        except Exception:
            return None
        finally:
            conn.close()
