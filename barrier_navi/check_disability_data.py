"""
users_preferencesテーブルの障害情報データを確認するスクリプト
"""

import os
import json
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
    
    print("=== users_preferencesテーブルの全データ ===")
    
    # 全データを取得
    preferences = db.execute_query("SELECT * FROM users_preferences")
    
    if preferences:
        for pref in preferences:
            print(f"\nユーザーID: {pref.get('user_id')}")
            print(f"障害の種類 (disability_type): {pref.get('disability_type')}")
            
            # JSONをパースして表示
            disability_type = pref.get('disability_type')
            if disability_type:
                try:
                    parsed = json.loads(disability_type)
                    print(f"  パース後: {parsed}")
                except:
                    print(f"  (JSONパース失敗: {disability_type})")
            
            print(f"お気に入りの駅 (favorite_stations): {pref.get('favorite_stations')}")
            print(f"優先したい機能 (preferred_features): {pref.get('preferred_features')}")
    else:
        print("データがありません")
    
    db.close()
except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()

