"""邮件通知模块：根据用户选择的模式发送摘要邮件。"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


class EmailNotifier:
    """封装 SMTP 邮件发送逻辑，支持选择性发送。"""

    def __init__(self, config, callback=None):
        self.config = config
        self.callback = callback

    def log(self, message):
        if self.callback:
            self.callback(message)

    def send(self, subject, body):
        """发送一封 HTML 邮件，成功返回 True。"""
        if not self.config.EMAIL_ENABLED:
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = Header(self.config.SENDER_EMAIL)
            msg["To"] = Header(self.config.RECEIVER_EMAIL)
            msg["Subject"] = Header(subject, "utf-8")
            msg.attach(MIMEText(body, "html", "utf-8"))

            with smtplib.SMTP_SSL(
                self.config.SMTP_SERVER, self.config.SMTP_PORT
            ) as server:
                server.login(self.config.SENDER_EMAIL, self.config.SENDER_PASSWORD)
                server.sendmail(
                    self.config.SENDER_EMAIL,
                    [self.config.RECEIVER_EMAIL],
                    msg.as_string(),
                )
            return True
        except Exception as e:
            self.log(f"邮件发送失败：{e}")
            return False

    def send_by_mode(self, all_data, new_data):
        """根据 EMAIL_SEND_MODE 决定发送内容。

        - "none": 不发送
        - "new_only": 仅发送新数据
        - "all": 发送全部抓取到的数据
        """
        mode = self.config.EMAIL_SEND_MODE

        if mode == "none":
            self.log("邮件发送模式：不发送")
            return

        if mode == "new_only":
            if not new_data:
                self.log("无新数据，跳过邮件发送")
                return
            body = self._build_email_body(new_data, "新增公告")
            self.send(f"公告更新（新增） - {self.config.QUOTES}", body)
            self.log(f"已发送邮件：{len(new_data)} 条新公告")

        elif mode == "all":
            if not all_data:
                self.log("无数据，跳过邮件发送")
                return
            body = self._build_email_body(all_data, "全部抓取公告")
            self.send(f"公告更新（全部） - {self.config.QUOTES}", body)
            self.log(f"已发送邮件：{len(all_data)} 条公告")

    def _build_email_body(self, data_list, label):
        """构造邮件正文（HTML 格式，包含公告内容）。"""
        new_count = sum(1 for d in data_list if d.get("is_new"))
        old_count = len(data_list) - new_count

        rows = []
        for i, item in enumerate(data_list, 1):
            tag = '<span style="color:#e74c3c;font-weight:bold">[新]</span>' if item.get("is_new") else '<span style="color:#3498db;font-weight:bold">[旧]</span>'
            title = item.get("title", "")
            author = item.get("author", "")
            pub_time = item.get("publish_time", "")
            url = item.get("url", "")
            content = item.get("content", "") or "暂无内容"

            rows.append(f"""
            <tr>
                <td style="padding:12px;border-bottom:1px solid #eee;">
                    <p style="margin:0 0 8px 0;">{tag} <strong>{i}. {title}</strong></p>
                    <p style="margin:0 0 4px 0;color:#666;font-size:13px;">发布人：{author}　|　发布时间：{pub_time}</p>
                    <div style="margin:8px 0;padding:10px;background:#f9f9f9;border-radius:4px;font-size:14px;line-height:1.6;">{content}</div>
                    <a href="{url}" style="color:#3498db;font-size:13px;">查看原文</a>
                </td>
            </tr>""")

        html = f"""<html><body>
        <div style="max-width:800px;margin:0 auto;font-family:'Microsoft YaHei',sans-serif;">
        <h2 style="color:#333;">关键词「{self.config.QUOTES}」{label}</h2>
        <p style="color:#666;">共 {len(data_list)} 条（新数据 {new_count} 条，已存在 {old_count} 条）</p>
        <table style="width:100%;border-collapse:collapse;">{''.join(rows)}
        </table>
        </div>
        </body></html>"""

        return html
