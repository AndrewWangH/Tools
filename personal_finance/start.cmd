@echo off
chcp 65001 >nul
echo ================================================
echo       个人财务管理系统 - 启动脚本
echo ================================================
echo.

:: 设置虚拟环境路径
set VENV_PATH=e:\pythonStore\.venv

:: 检查虚拟环境是否存在
if not exist "%VENV_PATH%\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在: %VENV_PATH%
    echo 请先创建虚拟环境
    pause
    exit /b 1
)

:: 激活虚拟环境
echo [1/3] 激活虚拟环境...
call "%VENV_PATH%\Scripts\activate.bat"

:: 安装依赖
echo [2/3] 检查并安装依赖...
pip install -r requirements.txt -q

:: 启动服务
echo [3/3] 启动 Flask 服务...
echo.
echo ================================================
echo   服务地址:
echo   - 登录页面: http://localhost:5000/login
echo   - 主页面:   http://localhost:5000/
echo   - API文档:  查看 personal_finance_api_doc.md
echo ================================================
echo.
echo 按 Ctrl+C 停止服务
echo.

python app.py

pause
