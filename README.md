# SSL 证书过期监控工具

轻量级 SSL 证书过期监控，定时检查域名证书有效期，到期前通过邮件、企业微信、钉钉、Slack 发送告警。

## 特性

- 纯 Python 标准库实现证书检查（ssl + socket）
- 支持四种通知渠道：邮件 / 企业微信 / 钉钉 / Slack
- 多级告警阈值（默认 30、14、7、1 天）
- 配置支持 `${ENV_VAR}` 和 `${ENV_VAR:-default}` 环境变量替换
- Docker 部署时通过环境变量灵活配置发件人、收件人
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

### 使用 DockerHub 镜像

```bash
docker pull pengpdx/ssl-cert-monitor:latest
```

### 运行

```bash
docker run -d --name ssl-monitor \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/logs:/var/log/ssl-monitor \
  -e EMAIL_ENABLED=true \
  -e SMTP_HOST=smtp.example.com \
  -e SMTP_PORT=465 \
  -e SMTP_USER=your@email.com \
  -e SMTP_AUTH_CODE=your-auth-code \
  -e SMTP_SENDER=your@email.com \
  -e SMTP_RECIPIENTS=admin@example.com,ops@example.com \
  pengpdx/ssl-cert-monitor:latest
```

### 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `EMAIL_ENABLED` | 邮件通知开关 | `false` |
| `SMTP_HOST` | SMTP 服务器地址 | `smtp.example.com` |
| `SMTP_PORT` | SMTP 端口 | `465` |
| `SMTP_USER` | SMTP 登录账号 | - |
| `SMTP_AUTH_CODE` | SMTP 授权码（非登录密码） | - |
| `SMTP_SENDER` | 发件人地址 | 同 `SMTP_USER` |
| `SMTP_RECIPIENTS` | 收件人，多个用逗号分隔 | - |
| `WECOM_WEBHOOK_URL` | 企业微信 Webhook | - |
| `DINGTALK_WEBHOOK_URL` | 钉钉 Webhook | - |
| `DINGTALK_SECRET` | 钉钉加签密钥 | - |
| `SLACK_WEBHOOK_URL` | Slack Webhook | - |

容器内通过 cron 每天北京时间 09:00（UTC 01:00）自动执行检查，日志挂载到宿主机 `./logs/ssl-monitor.log`。

```bash
# 手动触发一次检查
docker exec ssl-monitor python /app/main.py

# 在宿主机上直接查看日志
tail -f ./logs/ssl-monitor.log
```

### 自行构建

```bash
docker build -t ssl-cert-monitor .
```

## 通知渠道配置

### 邮件（SMTP）

通过环境变量配置，Docker 部署时无需修改 config.yaml：

```bash
-e EMAIL_ENABLED=true \
-e SMTP_HOST=smtp.example.com \
-e SMTP_USER=your@email.com \
-e SMTP_AUTH_CODE=your-auth-code \
-e SMTP_SENDER=noreply@example.com \
-e SMTP_RECIPIENTS=admin@example.com,ops@example.com
```

也可以直接在 `config.yaml` 中配置：

```yaml
notifiers:
  email:
    enabled: true
    smtp_host: smtp.example.com
    smtp_port: 465
    smtp_user: ${SMTP_USER}
    smtp_auth_code: ${SMTP_AUTH_CODE}
    sender: ${SMTP_SENDER:-${SMTP_USER}}
    recipients: ${SMTP_RECIPIENTS}
    use_ssl: true
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
