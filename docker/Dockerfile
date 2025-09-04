FROM python:3.11-slim
RUN apt-get update && apt-get install -y gcc libfreetype6-dev libpng-dev tzdata && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY automation/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && pip install -r requirements.txt
COPY automation /app/automation
RUN mkdir -p /app/data_analytics/reports
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
