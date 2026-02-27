FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY crontab /etc/cron.d/ssl-monitor
RUN chmod 0644 /etc/cron.d/ssl-monitor \
    && crontab /etc/cron.d/ssl-monitor

VOLUME ["/var/log/ssl-monitor"]

# 将环境变量导入 cron 环境
CMD printenv > /etc/environment && cron && tail -f /var/log/ssl-monitor/ssl-monitor.log
