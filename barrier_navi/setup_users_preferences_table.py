"""
users_preferencesテーブルを作成するスクリプト
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
    
    print("=== users_preferencesテーブルの作成 ===")
    
    # テーブル作成SQL
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS users_preferences (
        user_id INT PRIMARY KEY,
        disability_type TEXT NULL COMMENT '障害の種類（JSON配列形式）',
        favorite_stations TEXT NULL COMMENT 'お気に入りの駅のIDリスト（JSON配列形式）',
        preferred_features TEXT NULL COMMENT '優先したい機能のリスト（JSON配列形式）',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    try:
        db.execute_non_query(create_table_sql)
        print("✓ users_preferencesテーブルを作成しました（または既に存在していました）")
        
        # テーブル構造を確認
        print("\n=== テーブル構造の確認 ===")
        result = db.execute_query("DESCRIBE users_preferences")
        for row in result:
            print(f"カラム名: {row['Field']}, 型: {row['Type']}, NULL: {row['Null']}, キー: {row['Key']}")
        
    except Exception as e:
        print(f"✗ エラー: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()
except Exception as e:
    print(f"✗ データベース接続エラー: {e}")
    import traceback
    traceback.print_exc()

