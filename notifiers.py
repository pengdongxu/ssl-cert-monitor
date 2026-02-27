"""通知渠道实现：邮件 / 企业微信 / 钉钉 / Slack，统一签名 (config, message, subject)。"""

import json
import smtplib
import hashlib
import hmac
import base64
import time
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(config: dict, message: str, subject: str) -> None:
    """通过 SMTP 发送邮件告警，支持 SSL/STARTTLS。"""
    host = config["smtp_host"]
    port = config.get("smtp_port", 465)
    user = config["smtp_user"]
    password = config["smtp_password"]
    sender = config.get("sender", user)
    recipients = config["recipients"]
    if isinstance(recipients, str):
        recipients = [r.strip() for r in recipients.split(",") if r.strip()]
    use_ssl = config.get("use_ssl", True)

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain", "utf-8"))

    if use_ssl:
        with smtplib.SMTP_SSL(host, port) as server:
            server.login(user, password)
            server.sendmail(sender, recipients, msg.as_string())
    else:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, recipients, msg.as_string())


def send_wecom(config: dict, message: str, subject: str) -> None:
    """通过企业微信 Webhook 发送 markdown 格式告警。"""
    webhook_url = config["webhook_url"]
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": f"## {subject}\n\n{message}"},
    }
    _post_json(webhook_url, payload)


def send_dingtalk(config: dict, message: str, subject: str) -> None:
    """通过钉钉 Webhook 发送告警，支持加签认证。"""
    webhook_url = config["webhook_url"]
    secret = config.get("secret")

    if secret:
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    payload = {
        "msgtype": "markdown",
        "markdown": {"title": subject, "text": f"## {subject}\n\n{message}"},
    }
    _post_json(webhook_url, payload)


def send_slack(config: dict, message: str, subject: str) -> None:
    """通过 Slack Webhook 发送告警。"""
    webhook_url = config["webhook_url"]
    payload = {"text": f"*{subject}*\n\n{message}"}
    _post_json(webhook_url, payload)


def _post_json(url: str, payload: dict) -> None:
    """通用 JSON POST 请求（使用 urllib，不依赖 requests）。"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()
