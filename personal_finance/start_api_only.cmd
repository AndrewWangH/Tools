@echo off
chcp 65001 >nul
echo ================================================
echo   个人财务管理系统 - 原始API启动脚本（无认证）
echo ================================================
echo.

:: 设置虚拟环境路径
set VENV_PATH=e:\pythonStore\.venv

:: 激活虚拟环境
echo [1/2] 激活虚拟环境...
call "%VENV_PATH%\Scripts\activate.bat"

:: 启动服务
echo [2/2] 启动 Flask API 服务（无认证版本）...
echo.
echo ================================================
echo   API地址: http://localhost:5000/api/
echo   此版本无需登录，直接访问API
echo ================================================
echo.
echo 按 Ctrl+C 停止服务
echo.

python personal_finance_api.py

pause
