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
        """发送一封纯文本邮件，成功返回 True。"""
        if not self.config.EMAIL_ENABLED:
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = Header(self.config.SENDER_EMAIL)
            msg["To"] = Header(self.config.RECEIVER_EMAIL)
            msg["Subject"] = Header(subject, "utf-8")
            msg.attach(MIMEText(body, "plain", "utf-8"))

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
        """构造邮件正文。"""
        new_count = sum(1 for d in data_list if d.get("is_new"))
        old_count = len(data_list) - new_count

        body = f"关键词「{self.config.QUOTES}」{label}\n"
        body += f"共 {len(data_list)} 条（新数据 {new_count} 条，已存在 {old_count} 条）\n\n"

        for i, item in enumerate(data_list, 1):
            tag = "[新]" if item.get("is_new") else "[旧]"
            body += f"{i}. {tag} {item['title']}\n   {item['url']}\n\n"

        return body
