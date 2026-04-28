#!/bin/bash

###############################################################################
# 无人机网络安全防御系统 - 停止脚本
# Drone Security Defense System - Stop Script
###############################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
PID_FILE="${1:-/var/run/drone_security.pid}"

# 检查PID文件
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}PID文件不存在: $PID_FILE${NC}"
    echo "守护进程可能未运行"
    exit 0
fi

# 读取PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}进程不存在 (PID: $PID)${NC}"
    echo "清理PID文件"
    rm -f "$PID_FILE"
    exit 0
fi

# 停止进程
echo "停止守护进程 (PID: $PID)..."

# 发送SIGTERM信号
kill -15 "$PID" 2>/dev/null

# 等待进程结束
TIMEOUT=10
COUNT=0
while ps -p "$PID" > /dev/null 2>&1; do
    if [ $COUNT -ge $TIMEOUT ]; then
        echo -e "${YELLOW}进程未在 ${TIMEOUT} 秒内停止，强制终止${NC}"
        kill -9 "$PID" 2>/dev/null
        break
    fi
    sleep 1
    COUNT=$((COUNT + 1))
done

# 再次检查
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${GREEN}守护进程已停止${NC}"
    rm -f "$PID_FILE"
else
    echo -e "${RED}无法停止进程${NC}"
    exit 1
fi
