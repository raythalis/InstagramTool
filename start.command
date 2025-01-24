#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本所在目录
cd "$SCRIPT_DIR"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并启动程序
echo "正在启动程序..."
source venv/bin/activate

# 启动 web_ui.py
python web_ui.py

# 捕获程序退出状态
EXIT_CODE=$?

# 如果程序异常退出，等待用户按键
if [ $EXIT_CODE -ne 0 ]; then
    echo "程序异常退出 (退出码: $EXIT_CODE)"
    echo "按任意键继续..."
    read -n 1
fi 