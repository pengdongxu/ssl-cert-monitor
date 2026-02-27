"""SSL 证书过期监控工具入口：加载配置、调度检查、分发通知。"""

import os
import re
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

from checker import check_cert, CertResult
from notifiers import send_email, send_wecom, send_dingtalk, send_slack

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

NOTIFIER_MAP = {
    "email": send_email,
    "wecom": send_wecom,
    "dingtalk": send_dingtalk,
    "slack": send_slack,
}

ENV_VAR_PATTERN = re.compile(r"\$\{(\w+)\}")


def _replace_env_vars(obj):
    """递归替换配置中的 ${ENV_VAR} 占位符为环境变量值。"""
    if isinstance(obj, str):
        def _replacer(m):
            return os.environ.get(m.group(1), m.group(0))
        return ENV_VAR_PATTERN.sub(_replacer, obj)
    if isinstance(obj, dict):
        return {k: _replace_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_replace_env_vars(item) for item in obj]
    return obj


def load_config(path: str = None) -> dict:
    """加载 YAML 配置文件并替换环境变量。"""
    if path is None:
        path = Path(__file__).parent / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return _replace_env_vars(config)


def check_domains(config: dict) -> list[CertResult]:
    """遍历域名列表执行证书检查，返回所有结果。"""
    results = []
    for domain in config.get("domains", []):
        host = domain["host"]
        port = domain.get("port", 443)
        log.info("检查 %s:%d ...", host, port)
        result = check_cert(host, port)
        if result.error:
            log.warning("  检查失败: %s", result.error)
        else:
            log.info("  剩余 %d 天，到期 %s", result.days_remaining, result.expiry_date)
        results.append(result)
    return results


def filter_alerts(results: list[CertResult], thresholds: list[int]) -> list[CertResult]:
    """筛选需要告警的结果：检查失败或剩余天数 <= 任一阈值。"""
    max_threshold = max(thresholds) if thresholds else 30
    alerts = []
    for r in results:
        if r.error:
            alerts.append(r)
        elif r.days_remaining is not None and r.days_remaining <= max_threshold:
            alerts.append(r)
    return alerts


def format_message(alerts: list[CertResult]) -> str:
    """将告警列表格式化为可读消息。"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"检查时间: {now}", ""]
    for r in alerts:
        if r.error:
            lines.append(f"- **{r.host}:{r.port}** — 检查失败: {r.error}")
        else:
            if r.days_remaining <= 0:
                status = "**已过期**"
            elif r.days_remaining <= 7:
                status = f"**仅剩 {r.days_remaining} 天**"
            else:
                status = f"剩余 {r.days_remaining} 天"
            lines.append(
                f"- **{r.host}:{r.port}** — {status}，"
                f"到期 {r.expiry_date}，签发者 {r.issuer}"
            )
    return "\n".join(lines)


def dispatch_notifications(config: dict, message: str, subject: str) -> None:
    """遍历已启用的通知渠道发送告警，单个渠道失败不影响其他渠道。"""
    notifiers_cfg = config.get("notifiers", {})
    for name, cfg in notifiers_cfg.items():
        if not cfg.get("enabled", False):
            continue
        send_fn = NOTIFIER_MAP.get(name)
        if send_fn is None:
            log.warning("未知通知渠道: %s，跳过", name)
            continue
        try:
            log.info("发送通知: %s", name)
            send_fn(cfg, message, subject)
            log.info("  %s 发送成功", name)
        except Exception as e:
            log.error("  %s 发送失败: %s", name, e)


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config(config_path)

    log.info("=== SSL 证书过期监控开始 ===")
    results = check_domains(config)

    thresholds = config.get("alert_thresholds", [30, 14, 7, 1])
    alerts = filter_alerts(results, thresholds)

    if not alerts:
        log.info("所有证书状态正常，无需告警。")
        return

    log.warning("发现 %d 个需要告警的域名", len(alerts))
    subject = f"SSL 证书告警：{len(alerts)} 个域名需要关注"
    message = format_message(alerts)
    dispatch_notifications(config, message, subject)
    log.info("=== SSL 证书过期监控结束 ===")


if __name__ == "__main__":
    main()
