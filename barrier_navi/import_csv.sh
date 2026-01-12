#!/bin/bash
# CSVデータをインポートするシェルスクリプト
# MySQLコンテナの初期化時に実行されます

echo "=========================================="
echo "CSVデータインポートスクリプトを開始します"
echo "=========================================="

# Python3が利用可能か確認
if ! command -v python3 &> /dev/null; then
    echo "Python3が見つかりません。Python3をインストールしてください。"
    exit 1
fi

# MySQL接続を待機
echo "MySQL接続を待機中..."
max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD:-rootpassword} --silent; then
        echo "MySQL接続成功"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "MySQL接続を待機中... ($retry_count/$max_retries)"
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo "エラー: MySQLに接続できませんでした"
    exit 1
fi

# Pythonスクリプトを実行
echo "CSVデータをインポート中..."
python3 /docker-entrypoint-initdb.d/import_csv_data.py

if [ $? -eq 0 ]; then
    echo "=========================================="
    echo "CSVデータのインポートが完了しました"
    echo "=========================================="
else
    echo "=========================================="
    echo "CSVデータのインポートに失敗しました"
    echo "=========================================="
    exit 1
fi

