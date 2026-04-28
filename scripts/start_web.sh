#!/bin/bash
# Web服务启动脚本
# Web Server Startup Script

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 设置Python路径
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 检查配置文件
CONFIG_FILE="${PROJECT_ROOT}/config/default_config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误: 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 启动守护进程（包含Web服务器）
echo "启动无人机安全防御系统（Web模式）..."
echo "配置文件: $CONFIG_FILE"
echo ""

cd "$PROJECT_ROOT"

# 启动主程序
python3 -m src.main --config "$CONFIG_FILE"
