#!/bin/bash

echo "======================================"
echo "简历风险评估器 - 启动脚本"
echo "======================================"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "首次运行，正在创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "正在安装依赖..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo ""
echo "请确保已设置 ANTHROPIC_API_KEY 环境变量"
echo ""
echo "启动应用..."
echo ""

streamlit run app.py
