"""
ローカルMySQLデータベースに接続してデータを取得するプログラム
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()


class DatabaseConnection:
    """データベース接続を管理するクラス"""
    
    def __init__(self, host: str = "localhost", port: int = 3306, 
                 database: str = "mysql", user: str = "root", 
                 password: str = "", **kwargs):
        """
        MySQLデータベース接続を初期化
        
        Args:
            host: MySQLサーバーのホスト名（デフォルト: localhost）
            port: MySQLサーバーのポート番号（デフォルト: 3306）
            database: データベース名（デフォルト: mysql）
            user: ユーザー名（デフォルト: root）
            password: パスワード（デフォルト: 空文字列）
            **kwargs: その他の接続パラメータ
        """
        try:
            import mysql.connector
            from mysql.connector import Error
        except ImportError:
            raise ImportError(
                "MySQLを使用するには mysql-connector-python をインストールしてください: "
                "pip install mysql-connector-python"
            )
        
        self.connection = None
        self.cursor = None
        
        try:
            self.connection = mysql.connector.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                **kwargs
            )
            self.cursor = self.connection.cursor(dictionary=True)  # 辞書形式で結果を取得
            print(f"MySQLデータベース '{database}' に接続しました。")
        except Error as e:
            print(f"MySQL接続エラー: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        SQLクエリを実行して結果を取得
        
        Args:
            query: 実行するSQLクエリ（プレースホルダーは %s を使用）
            params: クエリパラメータ（タプルまたはリスト）
        
        Returns:
            クエリ結果のリスト（辞書形式）
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # 辞書形式で結果を取得（cursor(dictionary=True)で既に設定済み）
            return self.cursor.fetchall()
        except Exception as e:
            print(f"クエリ実行エラー: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None):
        """
        INSERT、UPDATE、DELETEなどのクエリを実行（結果を返さない）
        
        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            print(f"クエリが正常に実行されました。影響を受けた行数: {self.cursor.rowcount}")
        except Exception as e:
            self.connection.rollback()
            print(f"クエリ実行エラー: {e}")
            raise
    
    def close(self):
        """データベース接続を閉じる"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("データベース接続を閉じました。")


# def create_sample_database(host: str = "localhost", port: int = 3306,
#                            user: str = "root", password: str = "",
#                            database: str = "sample_db"):
#     """
#     サンプルデータベースとテーブルを作成（MySQL用）
    
#     Args:
#         host: MySQLサーバーのホスト名
#         port: MySQLサーバーのポート番号
#         user: ユーザー名
#         password: パスワード
#         database: 作成するデータベース名
#     """
#     try:
#         import mysql.connector
#         from mysql.connector import Error
        
#         # まずデータベースを作成するために接続（databaseパラメータなし）
#         temp_conn = mysql.connector.connect(
#             host=host,
#             port=port,
#             user=user,
#             password=password
#         )
#         temp_cursor = temp_conn.cursor()
        
#         # データベースが存在しない場合は作成
#         temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
#         temp_cursor.close()
#         temp_conn.close()
        
#         # 作成したデータベースに接続
#         db = DatabaseConnection(host=host, port=port, user=user, 
#                                password=password, database=database)
        
#         # サンプルテーブルを作成
#         create_table_query = """
#         CREATE TABLE IF NOT EXISTS users (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             name VARCHAR(100) NOT NULL,
#             email VARCHAR(255) UNIQUE NOT NULL,
#             age INT,
#             created_at DATETIME DEFAULT CURRENT_TIMESTAMP
#         ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
#         """
#         db.execute_non_query(create_table_query)
        
#         # 既存データをクリア（オプション）
#         db.execute_non_query("DELETE FROM users")
        
#         # サンプルデータを挿入
#         sample_data = [
#             ("山田太郎", "yamada@example.com", 30),
#             ("佐藤花子", "sato@example.com", 25),
#             ("鈴木一郎", "suzuki@example.com", 35),
#         ]
        
#         insert_query = "INSERT INTO users (name, email, age) VALUES (%s, %s, %s)"
#         for data in sample_data:
#             db.execute_non_query(insert_query, data)
        
#         db.close()
#         print(f"サンプルデータベース '{database}' を作成しました。")
        
#     except Error as e:
#         print(f"データベース作成エラー: {e}")
#         raise


def main():
    """メイン関数 - stationデータベースのstationsテーブルからデータを取得"""
    
    # MySQL接続情報を設定（環境変数から取得）
    MYSQL_CONFIG = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "station")
    }
    
    # データベースに接続
    try:
        db = DatabaseConnection(**MYSQL_CONFIG)
        
        # テーブルのレコード数を取得
        count_result = db.execute_query("SELECT COUNT(*) as total FROM stations")
        total_count = count_result[0]['total']
        print(f"\n=== stationsテーブルの総レコード数: {total_count}件 ===\n")
        
        # 全データを取得（最初の10件のみ表示）
        print("=== stationsテーブルのデータ（最初の10件） ===")
        stations = db.execute_query("SELECT * FROM stations LIMIT 10")
        for station in stations:
            print(f"\nID: {station['id']}")
            print(f"  鉄道事業者: {station['railway_operator']}")
            print(f"  駅名: {station['station_name']}")
            print(f"  路線名: {station['line_name']}")
            print(f"  都道府県: {station['prefecture']}")
            print(f"  市: {station['city']}")
            print(f"  プラットホーム数: {station['num_platforms']}")
            print(f"  エレベーター数: {station['num_elevators']}")
            print(f"  エスカレーター数: {station['num_escalators']}")
        
        # 都道府県別の駅数を取得
        print("\n=== 都道府県別の駅数 ===")
        prefecture_count = db.execute_query("""
            SELECT prefecture, COUNT(*) as count 
            FROM stations 
            WHERE prefecture IS NOT NULL 
            GROUP BY prefecture 
            ORDER BY count DESC 
            LIMIT 10
        """)
        for row in prefecture_count:
            print(f"{row['prefecture']}: {row['count']}駅")
        
        # エレベーターが設置されている駅を取得
        print("\n=== エレベーターが設置されている駅（最初の5件） ===")
        elevators = db.execute_query("""
            SELECT station_name, railway_operator, num_elevators, prefecture, city
            FROM stations 
            WHERE num_elevators > 0 
            ORDER BY num_elevators DESC 
            LIMIT 5
        """)
        for station in elevators:
            print(f"{station['station_name']} ({station['railway_operator']}) - "
                  f"エレベーター: {station['num_elevators']}基, "
                  f"{station['prefecture']} {station['city']}")
        
        # 特定の都道府県の駅を検索（例: 東京都）
        print("\n=== 東京都の駅（最初の5件） ===")
        tokyo_stations = db.execute_query("""
            SELECT station_name, railway_operator, line_name, city
            FROM stations 
            WHERE prefecture = %s 
            LIMIT 5
        """, ("東京都",))
        for station in tokyo_stations:
            print(f"{station['station_name']} - {station['railway_operator']} "
                  f"({station['line_name']}) - {station['city']}")
        
        # バリアフリー設備の統計
        print("\n=== バリアフリー設備の統計 ===")
        stats = db.execute_query("""
            SELECT 
                COUNT(*) as total_stations,
                SUM(CASE WHEN has_tactile_paving = 1 THEN 1 ELSE 0 END) as with_tactile_paving,
                SUM(CASE WHEN has_guidance_system = 1 THEN 1 ELSE 0 END) as with_guidance_system,
                SUM(CASE WHEN has_accessible_restroom = 1 THEN 1 ELSE 0 END) as with_accessible_restroom,
                SUM(CASE WHEN has_accessible_gate = 1 THEN 1 ELSE 0 END) as with_accessible_gate
            FROM stations
        """)
        if stats:
            s = stats[0]
            print(f"総駅数: {s['total_stations']}")
            print(f"視覚障害者誘導用ブロック設置: {s['with_tactile_paving']}駅")
            print(f"案内設備設置: {s['with_guidance_system']}駅")
            print(f"障害者対応型便所設置: {s['with_accessible_restroom']}駅")
            print(f"障害者対応型改札口設置: {s['with_accessible_gate']}駅")
        
        db.close()
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("\n接続情報を確認してください:")
        print(f"  ホスト: {MYSQL_CONFIG['host']}")
        print(f"  ポート: {MYSQL_CONFIG['port']}")
        print(f"  ユーザー: {MYSQL_CONFIG['user']}")
        print(f"  データベース: {MYSQL_CONFIG['database']}")
        print("\nMySQLサーバーが起動しているか確認してください。")


if __name__ == "__main__":
    main()

