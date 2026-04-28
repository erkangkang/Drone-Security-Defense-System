#!/bin/bash

###############################################################################
# 无人机网络安全防御系统 - 安装脚本
# Drone Security Defense System - Installation Script
###############################################################################

set -e

echo "============================================="
echo "  无人机网络安全防御系统 - 安装"
echo "  Drone Security Defense System - Install"
echo "============================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python版本
echo "检查Python版本..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}错误: Python版本必须 >= 3.8${NC}"
    echo "当前版本: $PYTHON_VERSION"
    exit 1
fi

echo -e "${GREEN}Python版本: $PYTHON_VERSION${NC}"
echo ""

# 检查是否为root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}警告: 不建议以root用户运行安装脚本${NC}"
    echo "如需systemd服务，请使用sudo"
    echo ""
fi

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "项目目录: $PROJECT_ROOT"
cd "$PROJECT_ROOT"
echo ""

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    echo -e "${GREEN}虚拟环境创建完成${NC}"
else
    echo "虚拟环境已存在，跳过创建"
fi
echo ""

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate
echo -e "${GREEN}虚拟环境已激活${NC}"
echo ""

# 升级pip
echo "升级pip..."
pip install --upgrade pip
echo ""

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt
echo -e "${GREEN}依赖包安装完成${NC}"
echo ""

# 创建必要的目录
echo "创建目录结构..."
mkdir -p /var/log/drone_security
mkdir -p /etc/drone_security
mkdir -p logs
echo -e "${GREEN}目录创建完成${NC}"
echo ""

# 复制配置文件
echo "复制配置文件..."
if [ ! -f "/etc/drone_security/default_config.yaml" ]; then
    cp config/default_config.yaml /etc/drone_security/
    echo -e "${GREEN}配置文件已复制到 /etc/drone_security/${NC}"
else
    echo "配置文件已存在，跳过复制"
fi

# 复制规则文件
if [ ! -d "/etc/drone_security/rules" ]; then
    cp -r config/rules /etc/drone_security/
    echo -e "${GREEN}规则文件已复制到 /etc/drone_security/rules/${NC}"
fi
echo ""

# 设置权限（如果不是root）
if [ "$EUID" -ne 0 ]; then
    echo "注意: 请手动设置日志目录权限:"
    echo "  sudo chown -R \$USER:\$USER /var/log/drone_security"
    echo "  sudo chown -R \$USER:\$USER /etc/drone_security"
    echo ""
fi

# 安装systemd服务（Linux）
if [ -d /etc/systemd/system ] && [ "$EUID" -eq 0 ]; then
    echo "安装systemd服务..."
    cat > /etc/systemd/system/drone-security.service << EOF
[Unit]
Description=Drone Security Defense System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_ROOT
Environment="PATH=$PROJECT_ROOT/venv/bin"
ExecStart=$PROJECT_ROOT/venv/bin/python $PROJECT_ROOT/src/main.py \\
    --config /etc/drone_security/default_config.yaml \\
    --daemon \\
    --pid /var/run/drone_security.pid
ExecStop=/bin/kill -15 \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    echo -e "${GREEN}systemd服务已安装${NC}"
    echo "启动服务: sudo systemctl start drone-security"
    echo "查看状态: sudo systemctl status drone-security"
    echo ""
fi

echo "============================================="
echo -e "${GREEN}安装完成！${NC}"
echo "============================================="
echo ""
echo "使用方法:"
echo "  激活虚拟环境: source venv/bin/activate"
echo "  启动守护进程: python src/main.py --config config/default_config.yaml"
echo "  启动守护进程（后台）: python src/main.py --config config/default_config.yaml --daemon"
echo ""
echo "更多信息请参考 README.md"
