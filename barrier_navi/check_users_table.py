"""
usersテーブルの構造を確認するスクリプト
"""

import os
from dotenv import load_dotenv
from database_connection import DatabaseConnection

# .envファイルから環境変数を読み込む
load_dotenv()

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "station")
}

try:
    db = DatabaseConnection(**MYSQL_CONFIG)
    
    # usersテーブルの構造を確認
    print("=== usersテーブルの構造 ===")
    result = db.execute_query("DESCRIBE users")
    for row in result:
        print(f"カラム名: {row['Field']}, 型: {row['Type']}, NULL: {row['Null']}, キー: {row['Key']}, デフォルト: {row['Default']}")
    
    # サンプルデータを確認（最初の1件）
    print("\n=== usersテーブルのサンプルデータ（最初の1件） ===")
    users = db.execute_query("SELECT * FROM users LIMIT 1")
    if users:
        for key, value in users[0].items():
            print(f"{key}: {value}")
    else:
        print("データがありません")
    
    db.close()
except Exception as e:
    print(f"エラー: {e}")

