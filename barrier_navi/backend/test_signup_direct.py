"""
新規登録を直接データベースでテストするスクリプト
"""

import os
from dotenv import load_dotenv
from database_connection import DatabaseConnection
import bcrypt

# .envファイルから環境変数を読み込む
load_dotenv()

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "station")
}

# テストデータ
test_username = "testuser3"
test_email = "test3@example.com"
test_password = "test12345"

print("=== 新規登録の直接テスト ===")
print(f"ユーザー名: {test_username}")
print(f"メール: {test_email}")
print(f"パスワード: {test_password}")
print()

try:
    db = DatabaseConnection(**MYSQL_CONFIG)
    
    # 重複チェック
    existing_user = db.execute_query(
        "SELECT id FROM users WHERE username = %s OR email = %s LIMIT 1",
        (test_username, test_email)
    )
    
    if existing_user:
        print(f"✗ エラー: ユーザー名またはメールアドレスが既に使用されています")
        print(f"  既存ユーザー: {existing_user[0]}")
    else:
        # パスワードをハッシュ化
        password_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"パスワードハッシュ: {password_hash[:50]}...")
        
        # ユーザーを登録
        try:
            db.execute_non_query(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (test_username, test_email, password_hash)
            )
            print("✓ 新規登録成功！")
            
            # 登録されたユーザーを確認
            new_user = db.execute_query(
                "SELECT id, username, email FROM users WHERE username = %s",
                (test_username,)
            )
            if new_user:
                print(f"  登録されたユーザー: {new_user[0]}")
        except Exception as e:
            print(f"✗ データベースエラー: {e}")
            import traceback
            traceback.print_exc()
    
    db.close()
except Exception as e:
    print(f"✗ エラー: {e}")
    import traceback
    traceback.print_exc()




