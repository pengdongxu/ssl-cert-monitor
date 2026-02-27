# SSL 证书过期监控工具

轻量级 SSL 证书过期监控，定时检查域名证书有效期，到期前通过邮件、企业微信、钉钉、Slack 发送告警。

## 特性

- 纯 Python 标准库实现证书检查（ssl + socket）
- 支持四种通知渠道：邮件 / 企业微信 / 钉钉 / Slack
- 多级告警阈值（默认 30、14、7、1 天）
- 敏感配置支持 `${ENV_VAR}` 环境变量替换
- Docker + cron 一键部署

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

编辑 `config.yaml`，添加要监控的域名和通知渠道：

```yaml
domains:
  - host: example.com
    port: 443
  - host: api.example.com

alert_thresholds: [30, 14, 7, 1]

notifiers:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
```

敏感字段使用 `${ENV_VAR}` 格式，运行时自动从环境变量读取。

### 运行

```bash
# 直接运行
python main.py

# 指定配置文件路径
python main.py /path/to/config.yaml
```

## Docker 部署

```bash
# 构建镜像
docker build -t ssl-cert-monitor .

# 运行（配置文件挂载 + 环境变量传入密码）
docker run -d --name ssl-monitor \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -e SMTP_USER=admin@example.com \
  -e SMTP_PASSWORD=your-password \
  -e SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx \
  ssl-cert-monitor
```

容器内通过 cron 每天北京时间 09:00（UTC 01:00）自动执行检查，日志写入 `/var/log/ssl-monitor.log`。

```bash
# 手动触发一次检查
docker exec ssl-monitor python /app/main.py

# 查看日志
docker exec ssl-monitor cat /var/log/ssl-monitor.log
```

## 通知渠道配置

### 邮件（SMTP）

```yaml
notifiers:
  email:
    enabled: true
    smtp_host: smtp.example.com
    smtp_port: 465
    smtp_user: ${SMTP_USER}
    smtp_password: ${SMTP_PASSWORD}
    recipients:
      - admin@example.com
      - ops@example.com
    use_ssl: true          # false 则使用 STARTTLS
```

### 企业微信

```yaml
notifiers:
  wecom:
    enabled: true
    webhook_url: ${WECOM_WEBHOOK_URL}
```

### 钉钉

```yaml
notifiers:
  dingtalk:
    enabled: true
    webhook_url: ${DINGTALK_WEBHOOK_URL}
    secret: ${DINGTALK_SECRET}       # 加签密钥，可选
```

### Slack

```yaml
notifiers:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
```
