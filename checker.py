"""SSL 证书检查模块：连接目标域名获取证书信息，计算剩余有效天数。"""

import ssl
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CertResult:
    host: str
    port: int
    days_remaining: Optional[int] = None
    expiry_date: Optional[str] = None
    issuer: Optional[str] = None
    error: Optional[str] = None


def check_cert(host: str, port: int = 443, timeout: int = 10) -> CertResult:
    """检查指定域名的 SSL 证书，返回 CertResult。异常不抛出，通过 error 字段返回。"""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
    except Exception as e:
        return CertResult(host=host, port=port, error=str(e))

    try:
        not_after = cert["notAfter"]
        # 格式示例: 'Sep  9 12:00:00 2025 GMT'
        expiry_dt = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=timezone.utc
        )
        days_remaining = (expiry_dt - datetime.now(timezone.utc)).days

        # 提取 issuer 组织名
        issuer_parts = dict(x[0] for x in cert.get("issuer", ()))
        issuer = issuer_parts.get("organizationName", "Unknown")

        return CertResult(
            host=host,
            port=port,
            days_remaining=days_remaining,
            expiry_date=expiry_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            issuer=issuer,
        )
    except Exception as e:
        return CertResult(host=host, port=port, error=f"解析证书失败: {e}")
