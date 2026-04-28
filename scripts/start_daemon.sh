#!/bin/bash

###############################################################################
# 无人机网络安全防御系统 - 启动脚本
# Drone Security Defense System - Start Script
###############################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
CONFIG_PATH="${1:-/etc/drone_security/default_config.yaml}"
PID_FILE="${2:-/var/run/drone_security.pid}"
LOG_PATH="/var/log/drone_security"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 激活虚拟环境
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
else
    echo -e "${RED}错误: 虚拟环境不存在${NC}"
    echo "请先运行 install.sh"
    exit 1
fi

# 检查配置文件
if [ ! -f "$CONFIG_PATH" ]; then
    echo -e "${RED}错误: 配置文件不存在: $CONFIG_PATH${NC}"
    exit 1
fi

# 检查守护进程是否已运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}守护进程已在运行 (PID: $PID)${NC}"
        exit 0
    else
        echo "清理旧的PID文件"
        rm -f "$PID_FILE"
    fi
fi

# 创建日志目录
mkdir -p "$LOG_PATH"

# 启动守护进程
echo "启动守护进程..."
echo "  配置文件: $CONFIG_PATH"
echo "  PID文件: $PID_FILE"
echo "  日志目录: $LOG_PATH"
echo ""

nohup python "$PROJECT_ROOT/src/main.py" \
    --config "$CONFIG_PATH" \
    --daemon \
    --pid "$PID_FILE" \
    > "$LOG_PATH/daemon.log" 2>&1 &

NEW_PID=$!
echo -e "${GREEN}守护进程已启动，PID: $NEW_PID${NC}"

# 等待进程启动
sleep 2

if ps -p "$NEW_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}进程运行正常${NC}"
else
    echo -e "${RED}进程启动失败，请检查日志${NC}"
    echo "  日志文件: $LOG_PATH/daemon.log"
    exit 1
fi

echo ""
echo "查看日志: tail -f $LOG_PATH/daemon.log"
echo "查看状态: python $PROJECT_ROOT/src/main.py --config $CONFIG_PATH --status --pid $PID_FILE"
echo "停止进程: $SCRIPT_DIR/stop_daemon.sh $PID_FILE"
