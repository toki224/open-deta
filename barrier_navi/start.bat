@echo off
echo Flask APIサーバーを起動します...
echo ブラウザで http://localhost:5000 にアクセスしてください。
echo.
start py api_server.py
timeout /t 3
start http://localhost:5000

