@echo off
echo Flask APIサーバーを起動します...
echo ブラウザで index.html を開いてください。
echo.
echo データベース接続設定:
echo   - MYSQL_HOST=localhost
echo   - MYSQL_PORT=3306
echo   - MYSQL_USER=root
echo   - MYSQL_DATABASE=station
echo   - パスワードは .env ファイルから読み込みます
echo.
start python api_server.py
timeout /t 3
start index.html

