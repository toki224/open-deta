#!/bin/bash
# Webコンテナのエントリーポイントスクリプト
# データベースが準備できたらCSVデータをインポートしてからFlaskを起動

set -e

echo "=========================================="
echo "バリアナビ Webコンテナを起動します"
echo "=========================================="

# 環境変数の確認
echo "環境変数:"
echo "  MYSQL_HOST: ${MYSQL_HOST}"
echo "  MYSQL_DATABASE: ${MYSQL_DATABASE}"
echo "  MYSQL_USER: ${MYSQL_USER}"

# MySQL接続を待機
echo "MySQL接続を待機中..."
max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    result=$(python3 -c "
import mysql.connector
import os
import sys
try:
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'db'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'barrier_user'),
        password=os.getenv('MYSQL_PASSWORD', 'barrier_password'),
        database=os.getenv('MYSQL_DATABASE', 'station')
    )
    conn.close()
    print('SUCCESS')
    sys.exit(0)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)
    
    if echo "$result" | grep -q "SUCCESS"; then
        echo "MySQL接続成功"
        break
    else
        retry_count=$((retry_count + 1))
        echo "MySQL接続を待機中... ($retry_count/$max_retries)"
        if [ $retry_count -lt $max_retries ]; then
            echo "  エラー: $result"
        fi
        sleep 2
    fi
done

if [ $retry_count -eq $max_retries ]; then
    echo "警告: MySQLに接続できませんでした。続行します..."
fi

# CSVデータのインポート（データが存在しない場合のみ）
echo "CSVデータのインポートを確認中..."
if [ -f /app/database/import_csv_data.py ]; then
    python3 /app/database/import_csv_data.py || echo "警告: CSVデータのインポートに失敗しました（既にデータが存在する可能性があります）"
else
    echo "警告: import_csv_data.pyが見つかりません"
fi

# Flaskアプリケーションを起動
echo "=========================================="
echo "Flaskアプリケーションを起動します"
echo "=========================================="
exec python backend/api_server.py

