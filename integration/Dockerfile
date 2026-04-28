FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpcap-dev iproute2 net-tools iputils-ping tcpdump && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy defense system source code
COPY src/ /app/src/
COPY config/ /app/config/

# Copy Docker-specific integration files
COPY integration/config/docker_config.yaml /app/config/docker_config.yaml
COPY integration/start-defense.sh /app/start-defense.sh
RUN chmod +x /app/start-defense.sh && mkdir -p /app/logs /app/data

EXPOSE 9090

CMD ["/app/start-defense.sh"]
