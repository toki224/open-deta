"""
testuserのパスワード情報を確認するスクリプト
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
    
    # testuserの全カラムを取得
    print("=== testuserの全情報 ===")
    users = db.execute_query(
        "SELECT * FROM users WHERE username = 'testuser'"
    )
    
    if users:
        user = users[0]
        print("全カラム名と値:")
        for key, value in user.items():
            if value is not None:
                # パスワード関連のカラムを確認
                if 'password' in key.lower():
                    # ハッシュ化されているかどうかを確認
                    if isinstance(value, str):
                        if value.startswith('$2b$') or value.startswith('$2a$') or value.startswith('$2y$'):
                            print(f"{key}: bcryptハッシュ (復元不可)")
                        else:
                            print(f"{key}: {value} (ハッシュ化されていない可能性)")
                    else:
                        print(f"{key}: {type(value).__name__}")
                else:
                    print(f"{key}: {value}")
        
        # パスワードカラムを直接確認
        print("\n=== パスワード関連カラムの確認 ===")
        password_cols = [k for k in user.keys() if 'password' in k.lower()]
        if password_cols:
            for col in password_cols:
                value = user[col]
                if value:
                    if isinstance(value, str):
                        if len(value) > 50 and (value.startswith('$2b$') or value.startswith('$2a$') or value.startswith('$2y$')):
                            print(f"{col}: bcryptハッシュ化済み（元のパスワードは復元できません）")
                        else:
                            print(f"{col}: {value}")
                    else:
                        print(f"{col}: {type(value).__name__}")
        else:
            print("パスワード関連のカラムが見つかりませんでした")
    else:
        print("testuserが見つかりませんでした")
    
    db.close()
except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()

