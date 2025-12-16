"""
usersテーブルにtestuserが存在するか確認するスクリプト
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
    
    # testuserを検索
    print("=== testuserの検索 ===")
    users = db.execute_query(
        "SELECT * FROM users WHERE username = %s OR email = %s",
        ("testuser", "testuser")
    )
    
    if users:
        print(f"testuserが見つかりました（{len(users)}件）:")
        for user in users:
            print("\n--- ユーザー情報 ---")
            for key, value in user.items():
                # パスワード情報は一部のみ表示
                if 'password' in key.lower():
                    if value:
                        print(f"{key}: {'*' * 20} (ハッシュ化済み)")
                    else:
                        print(f"{key}: (空)")
                else:
                    print(f"{key}: {value}")
    else:
        print("testuserは見つかりませんでした。")
        
        # 全ユーザー一覧を表示
        print("\n=== 全ユーザー一覧 ===")
        all_users = db.execute_query("SELECT id, username, email, created_at FROM users LIMIT 10")
        if all_users:
            print(f"登録されているユーザー（最大10件）:")
            for user in all_users:
                print(f"  - ID: {user.get('id')}, ユーザー名: {user.get('username')}, メール: {user.get('email')}, 作成日: {user.get('created_at')}")
        else:
            print("ユーザーが登録されていません。")
    
    db.close()
except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()

