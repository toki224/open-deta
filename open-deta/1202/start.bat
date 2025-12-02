@echo off
echo Flask APIサーバーを起動します...
echo ブラウザで index.html を開いてください。
echo.
start py api_server.py
timeout /t 3
start index.html

