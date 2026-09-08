@echo off
chcp 65001 >nul
title 商品链接自动采集工具
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo 未找到项目虚拟环境：.venv
    echo 请先运行：python -m venv .venv
    echo 然后运行：.venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" "collector_gui.pyw"
