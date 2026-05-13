@echo off
chcp 65001 >nul
echo ======================================
echo 简历风险评估器 - 启动脚本
echo ======================================
echo.

REM 检查虚拟环境
if not exist "venv" (
    echo 首次运行，正在创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo 正在安装依赖...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo 请确保已设置 ANTHROPIC_API_KEY 环境变量
echo.
echo 启动应用...
echo.

streamlit run app.py
