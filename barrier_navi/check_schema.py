"""データベースのスキーマを確認するスクリプト"""
import os
from dotenv import load_dotenv
from database_connection import DatabaseConnection

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
    
    # テーブルのカラム情報を取得
    result = db.execute_query("DESCRIBE stations")
    
    print("=== stationsテーブルのカラム一覧 ===\n")
    db_columns = []
    for r in result:
        col_name = r['Field']
        col_type = r['Type']
        db_columns.append(col_name)
        print(f"{col_name:40} {col_type}")
    
    print(f"\n総カラム数: {len(db_columns)}")
    
    # コードで使用しているカラムと比較
    print("\n=== コードで使用しているカラム ===\n")
    
    # BODY_QUERY_COLUMNS
    from api_server import BODY_QUERY_COLUMNS, BODY_METRIC_DEFINITIONS
    
    print("BODY_QUERY_COLUMNS:")
    for col in BODY_QUERY_COLUMNS:
        exists = "✓" if col in db_columns else "✗ 存在しない"
        print(f"  {col:40} {exists}")
    
    # 統計クエリで使用しているカラム
    print("\n統計クエリで使用しているカラム:")
    stats_columns = ['has_tactile_paving', 'has_guidance_system', 
                     'has_accessible_restroom', 'has_accessible_gate', 'num_elevators']
    for col in stats_columns:
        exists = "✓" if col in db_columns else "✗ 存在しない"
        print(f"  {col:40} {exists}")
    
    # データベースにあってコードで使っていないカラム
    print("\n=== データベースにあってコードで使っていないカラム ===")
    unused = [col for col in db_columns if col not in BODY_QUERY_COLUMNS and col not in stats_columns]
    if unused:
        for col in unused:
            print(f"  {col}")
    else:
        print("  なし")
    
    # コードで使っているがデータベースにないカラム
    print("\n=== コードで使っているがデータベースにないカラム ===")
    missing = []
    for col in BODY_QUERY_COLUMNS:
        if col not in db_columns:
            missing.append(col)
    for col in stats_columns:
        if col not in db_columns and col not in missing:
            missing.append(col)
    
    if missing:
        for col in missing:
            print(f"  ✗ {col}")
    else:
        print("  なし（すべて存在します）")
    
    db.close()
    
except Exception as e:
    print(f"エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()

