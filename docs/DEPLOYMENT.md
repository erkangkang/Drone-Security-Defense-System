# 部署指南

# Deployment Guide

本文档提供无人机安全防御系统的详细部署说明。

## 系统要求

### 硬件要求

#### 最低配置

- CPU: 双核处理器
- 内存: 512MB RAM
- 存储: 100MB 可用空间
- 网络: 以太网或WiFi（用于远程访问）

#### 推荐配置

- CPU: 四核处理器
- 内存: 2GB RAM
- 存储: 500MB 可用空间
- 网络: 以太网连接

### 软件要求

- 操作系统: Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+), Android, 嵌入式Linux
- Python: 3.8 或更高版本
- Node.js: 14+ (仅构建前端时需要)
- 浏览器: Chrome 90+, Firefox 88+, Safari 14+ (Web界面)

## 安装步骤

### 1. 获取源代码

```bash
# 克隆仓库
git clone https://github.com/drone-security/drone-security-defense.git
cd drone-security-defense

# 或下载发布版本
wget https://github.com/drone-security/drone-security-defense/archive/v1.0.0.tar.gz
tar -xzf v1.0.0.tar.gz
cd drone-security-defense-1.0.0
```

### 2. 安装Python依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 创建必要目录

```bash
# 创建日志目录
mkdir -p logs

# 创建数据目录
mkdir -p data
```

### 4. 配置系统

```bash
# 复制默认配置
cp config/default_config.yaml config/production_config.yaml

# 编辑配置文件
nano config/production_config.yaml
```

### 5. 构建前端（可选）

```bash
# 进入前端目录
cd src/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 返回项目根目录
cd ../..
```

## 部署模式

### 模式一：独立守护进程

适用于嵌入式设备或资源受限环境。

```bash
# 启动守护进程（无Web界面）
python src/main.py --config config/default_config.yaml

# 或作为后台服务运行
python src/main.py --config config/default_config.yaml --daemon
```

### 模式二：Web服务模式

适用于需要远程管理和可视化监控的场景。

```bash
# 启动Web服务模式
./scripts/start_web.sh

# 服务将在以下地址可用：
# - API: http://localhost:8080/api
# - Web界面: http://localhost:8080
```

### 模式三：系统服务模式

适用于生产环境部署。

#### Linux systemd

创建服务文件 `/etc/systemd/system/drone-security.service`:

```ini
[Unit]
Description=Drone Security Defense System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/drone-security-defense
Environment="PYTHONPATH=/opt/drone-security-defense/src"
ExecStart=/opt/drone-security-defense/venv/bin/python src/main.py --config config/production_config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动服务:

```bash
# 复制服务文件
sudo cp scripts/drone-security.service /etc/systemd/system/

# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable drone-security

# 启动服务
sudo systemctl start drone-security

# 查看状态
sudo systemctl status drone-security
```

#### Docker部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/ src/
COPY config/ config/

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "-m", "src.main", "--config", "config/default_config.yaml"]
```

构建并运行:

```bash
# 构建镜像
docker build -t drone-security-defense:latest .

# 运行容器
docker run -d \
  --name drone-security \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  drone-security-defense:latest
```

#### Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  drone-security:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
```

启动:

```bash
docker-compose up -d
```

## 配置优化

### 资源受限环境

编辑 `config/default_config.yaml`:

```yaml
platform:
  resource_profile: "minimal"  # 使用最小资源配置

# 禁用部分检测器
detectors:
  mavlink:
    enabled: true
  gps:
    enabled: false  # 禁用GPS检测器
  sensor:
    enabled: false  # 禁用传感器检测器
  dos:
    enabled: false  # 禁用DoS检测器

# 禁用分析器
analyzers:
  statistical:
    enabled: false
  correlation:
    enabled: false
  ml:
    enabled: false

# 禁用Web界面
web:
  enabled: false
```

### 高性能环境

```yaml
platform:
  resource_profile: "full"  # 使用完整资源配置

# 启用所有检测器
detectors:
  mavlink:
    enabled: true
    interval: 0.05  # 更高的检测频率
  gps:
    enabled: true
    interval: 0.1
  sensor:
    enabled: true
    interval: 0.05
  dos:
    enabled: true
    interval: 0.5

# 启用所有分析器
analyzers:
  statistical:
    enabled: true
    window_size: 200
  correlation:
    enabled: true
  ml:
    enabled: true
    model_path: "models/threat_detector.pkl"

# Web服务器配置
web:
  enabled: true
  broadcaster:
    interval: 1.0  # 更频繁的数据更新
```

## 网络配置

### 防火墙配置

```bash
# Ubuntu/Debian
sudo ufw allow 8080/tcp
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

### 反向代理配置

#### Nginx

创建配置文件 `/etc/nginx/sites-available/drone-security`:

```nginx
server {
    listen 80;
    server_name drone-security.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置:

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/drone-security /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

#### Apache

创建配置文件 `/etc/apache2/sites-available/drone-security.conf`:

```apache
<VirtualHost *:80>
    ServerName drone-security.example.com

    ProxyPreserveHost On
    ProxyRequests Off

    ProxyPass / ws://localhost:8080/ retry=0
    ProxyPassReverse / ws://localhost:8080/

    ProxyPass /api/ http://localhost:8080/api/ retry=0
    ProxyPassReverse /api/ http://localhost:8080/api/
</VirtualHost>
```

启用模块和站点:

```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod proxy_wstunnel
sudo a2ensite drone-security
sudo systemctl restart apache2
```

## 安全加固

### 1. 启用认证

编辑配置文件:

```yaml
web:
  auth:
    enabled: true
    jwt_secret: "your-secret-key-here"
    api_keys:
      - "your-api-key-here"
```

### 2. 配置HTTPS

使用Let's Encrypt获取免费SSL证书:

```bash
# 安装certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d drone-security.example.com
```

### 3. 限制访问来源

```yaml
web:
  cors_origins:
    - "https://drone-security.example.com"
    - "https://admin.example.com"
```

### 4. 配置速率限制

```yaml
web:
  rate_limit:
    enabled: true
    requests_per_minute: 60
    burst: 10
```

## 监控和维护

### 日志管理

配置日志轮转 `/etc/logrotate.d/drone-security`:

```
/opt/drone-security-defense/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        systemctl reload drone-security > /dev/null 2>&1 || true
    endscript
}
```

### 健康检查

创建健康检查脚本 `health_check.sh`:

```bash
#!/bin/bash

# 检查服务状态
curl -f http://localhost:8080/api/system/health || exit 1

# 检查进程
pgrep -f "src.main.py" > /dev/null || exit 1

echo "Service is healthy"
exit 0
```

### 备份

```bash
#!/bin/bash

# 备份脚本
BACKUP_DIR="/backup/drone-security/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 备份配置
cp -r config/ "$BACKUP_DIR/"

# 备份日志（最近7天）
find logs/ -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;

# 压缩备份
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

# 删除30天前的备份
find /backup/drone-security/ -name "*.tar.gz" -mtime +30 -delete
```

## 故障排查

### 服务无法启动

1. 检查日志文件
2. 验证配置文件语法
3. 确认端口未被占用
4. 检查文件权限

### 性能问题

1. 检查系统资源使用
2. 调整资源配置
3. 禁用不必要的检测器

### 网络连接问题

1. 验证防火墙规则
2. 检查网络配置
3. 测试端口连通性

## 升级

### 升级步骤

```bash
# 1. 停止服务
sudo systemctl stop drone-security

# 2. 备份当前版本
cp -r /opt/drone-security-defense /opt/drone-security-defense.backup

# 3. 获取新版本
git pull origin main
# 或下载新版本并解压

# 4. 更新依赖
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 5. 更新配置（如有必要）
# 检查配置文件是否有新选项

# 6. 重启服务
sudo systemctl start drone-security

# 7. 验证升级
sudo systemctl status drone-security
curl http://localhost:8080/api/system/health
```

### 回滚

```bash
# 停止服务
sudo systemctl stop drone-security

# 恢复备份
rm -rf /opt/drone-security-defense
mv /opt/drone-security-defense.backup /opt/drone-security-defense

# 重启服务
sudo systemctl start drone-security
```
