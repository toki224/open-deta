#!/usr/bin/env python3
"""
CSVファイルからstationsテーブルにデータをインポートするスクリプト
Docker環境の初期化時に自動実行されます
"""

import os
import sys
import csv
import mysql.connector
from mysql.connector import Error

def get_mysql_config():
    """環境変数からMySQL接続情報を取得"""
    return {
        "host": os.getenv("MYSQL_HOST", "db"),  # Docker環境ではサービス名を使用
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "barrier_user"),
        "password": os.getenv("MYSQL_PASSWORD", "barrier_password"),
        "database": os.getenv("MYSQL_DATABASE", "station")
    }

def import_csv_to_mysql(csv_file_path, mysql_config):
    """CSVファイルをMySQLデータベースにインポート"""
    connection = None
    cursor = None
    
    try:
        # MySQLに接続
        print(f"MySQLに接続中: {mysql_config['host']}:{mysql_config['port']}")
        connection = mysql.connector.connect(**mysql_config)
        cursor = connection.cursor()
        
        # CSVファイルが存在するか確認
        if not os.path.exists(csv_file_path):
            print(f"警告: CSVファイルが見つかりません: {csv_file_path}")
            return False
        
        # 既存データを削除（オプション）
        print("既存のstationsデータを削除中...")
        cursor.execute("DELETE FROM stations")
        connection.commit()
        
        # CSVファイルを読み込む（文字エンコーディングを自動検出）
        print(f"CSVファイルを読み込み中: {csv_file_path}")
        encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932', 'latin-1']
        csv_data = None
        encoding_used = None
        
        for encoding in encodings:
            try:
                with open(csv_file_path, 'r', encoding=encoding, newline='') as f:
                    csv_data = list(csv.DictReader(f))
                    encoding_used = encoding
                    print(f"文字エンコーディング: {encoding}")
                    break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if csv_data is None:
            print("エラー: CSVファイルの読み込みに失敗しました（文字エンコーディングの問題）")
            return False
        
        # データを挿入
        print(f"データをインポート中... ({len(csv_data)}件)")
        
        # カラム名のマッピング（CSVのカラム名 → データベースのカラム名）
        # CSVのヘッダーが日本語の場合、適切にマッピングする必要があります
        insert_query = """
        INSERT INTO stations (
            id, railway_operator, station_name, line_name, prefecture, city,
            step_response_status, num_platforms, num_step_free_platforms,
            num_elevators, num_compliant_elevators, num_escalators, num_compliant_escalators,
            num_other_lifts, num_slopes, num_compliant_slopes,
            has_tactile_paving, has_guidance_system, has_accessible_restroom,
            has_accessible_gate, has_accessible_ticket_machine,
            num_wheelchair_accessible_platforms, has_fall_prevention
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        # CSVの最初の行からカラム名を取得
        if not csv_data:
            print("警告: CSVファイルにデータが含まれていません")
            return False
        
        first_row = csv_data[0]
        column_mapping = {}
        
        # カラム名のマッピングを試行（日本語ヘッダーまたは英語ヘッダーに対応）
        possible_mappings = {
            'id': ['ID', 'id', 'Id'],
            'railway_operator': ['鉄道事業者名', 'railway_operator', 'Railway Operator'],
            'station_name': ['鉄道駅の名称', 'station_name', 'Station Name'],
            'line_name': ['路線名', 'line_name', 'Line Name'],
            'prefecture': ['都道府県', 'prefecture', 'Prefecture'],
            'city': ['市', 'city', 'City'],
            'step_response_status': ['段差への対応', 'step_response_status'],
            'num_platforms': ['プラットホームの数', 'num_platforms'],
            'num_step_free_platforms': ['段差が解消されているプラットホームの数', 'num_step_free_platforms'],
            'num_elevators': ['エレベーターの設置基数', 'num_elevators'],
            'num_compliant_elevators': ['移動等円滑化基準に適合しているエレベーターの設置基数', 'num_compliant_elevators'],
            'num_escalators': ['エスカレーターの設置基数', 'num_escalators'],
            'num_compliant_escalators': ['移動等円滑化基準に適合しているエスカレーターの設置基数', 'num_compliant_escalators'],
            'num_other_lifts': ['その他の昇降機の設置基数', 'num_other_lifts'],
            'num_slopes': ['傾斜路の設置箇所数', 'num_slopes'],
            'num_compliant_slopes': ['移動等円滑化基準に適合している傾斜路の設置箇所数', 'num_compliant_slopes'],
            'has_tactile_paving': ['視覚障害者誘導用ブロックの設置の有無', 'has_tactile_paving'],
            'has_guidance_system': ['案内設備の設置の有無', 'has_guidance_system'],
            'has_accessible_restroom': ['障害者対応型便所の設置の有無', 'has_accessible_restroom'],
            'has_accessible_gate': ['障害者対応型改札口の設置の有無', 'has_accessible_gate'],
            'has_accessible_ticket_machine': ['障害者対応型券売機の設置の有無', 'has_accessible_ticket_machine'],
            'num_wheelchair_accessible_platforms': ['車いす使用者の円滑な乗降が可能なプラットホームの数', 'num_wheelchair_accessible_platforms'],
            'has_fall_prevention': ['転落防止のための設備の設置の有無', 'has_fall_prevention']
        }
        
        # CSVのカラム名を確認してマッピングを作成
        csv_columns = list(first_row.keys())
        print(f"CSVカラム数: {len(csv_columns)}")
        print(f"最初のカラム名（サンプル）: {csv_columns[:5]}")
        
        for db_column, possible_names in possible_mappings.items():
            for csv_column in csv_columns:
                if csv_column in possible_names or csv_column.strip() in possible_names:
                    column_mapping[db_column] = csv_column
                    break
        
        # マッピングが不足している場合は、順序でマッピングを試行
        if len(column_mapping) < len(possible_mappings):
            print("警告: 一部のカラムマッピングが見つかりません。順序でマッピングを試行します。")
            # CSVのカラム順序に基づいてマッピング
            db_columns_order = [
                'id', 'railway_operator', 'station_name', 'line_name', 'prefecture', 'city',
                'step_response_status', 'num_platforms', 'num_step_free_platforms',
                'num_elevators', 'num_compliant_elevators', 'num_escalators', 'num_compliant_escalators',
                'num_other_lifts', 'num_slopes', 'num_compliant_slopes',
                'has_tactile_paving', 'has_guidance_system', 'has_accessible_restroom',
                'has_accessible_gate', 'has_accessible_ticket_machine',
                'num_wheelchair_accessible_platforms', 'has_fall_prevention'
            ]
            for i, db_column in enumerate(db_columns_order):
                if i < len(csv_columns) and db_column not in column_mapping:
                    column_mapping[db_column] = csv_columns[i]
        
        # データを挿入
        inserted_count = 0
        for row in csv_data:
            try:
                # 値を取得（マッピングに基づく）
                values = []
                for db_column in [
                    'id', 'railway_operator', 'station_name', 'line_name', 'prefecture', 'city',
                    'step_response_status', 'num_platforms', 'num_step_free_platforms',
                    'num_elevators', 'num_compliant_elevators', 'num_escalators', 'num_compliant_escalators',
                    'num_other_lifts', 'num_slopes', 'num_compliant_slopes',
                    'has_tactile_paving', 'has_guidance_system', 'has_accessible_restroom',
                    'has_accessible_gate', 'has_accessible_ticket_machine',
                    'num_wheelchair_accessible_platforms', 'has_fall_prevention'
                ]:
                    csv_column = column_mapping.get(db_column)
                    if csv_column and csv_column in row:
                        value = row[csv_column].strip() if row[csv_column] else None
                        # 数値型のカラムは数値に変換
                        if db_column in ['id', 'step_response_status', 'num_platforms', 'num_step_free_platforms',
                                       'num_elevators', 'num_compliant_elevators', 'num_escalators', 'num_compliant_escalators',
                                       'num_other_lifts', 'num_slopes', 'num_compliant_slopes',
                                       'has_tactile_paving', 'has_guidance_system', 'has_accessible_restroom',
                                       'has_accessible_gate', 'has_accessible_ticket_machine',
                                       'num_wheelchair_accessible_platforms', 'has_fall_prevention']:
                            try:
                                value = int(value) if value and value != '' else None
                            except (ValueError, TypeError):
                                value = None
                        values.append(value)
                    else:
                        values.append(None)
                
                cursor.execute(insert_query, tuple(values))
                inserted_count += 1
                
                if inserted_count % 100 == 0:
                    print(f"  {inserted_count}件をインポートしました...")
                    connection.commit()
            
            except Exception as e:
                print(f"警告: 行のインポートに失敗しました: {e}")
                print(f"  データ: {row}")
                continue
        
        connection.commit()
        print(f"完了: {inserted_count}件のデータをインポートしました")
        return True
        
    except Error as e:
        print(f"MySQLエラー: {e}")
        if connection:
            connection.rollback()
        return False
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def main():
    """メイン関数"""
    mysql_config = get_mysql_config()
    
    # CSVファイルのパス（Docker環境では/app/にマウントされる）
    csv_file_path = os.getenv("CSV_FILE_PATH", "/app/tokyo_stations.csv")
    
    # ファイルが存在しない場合は、現在のディレクトリを確認
    if not os.path.exists(csv_file_path):
        csv_file_path = os.path.join(os.path.dirname(__file__), "tokyo_stations.csv")
    
    print("=" * 60)
    print("CSVデータインポートスクリプト")
    print("=" * 60)
    
    # データベース接続を待機（Docker環境でMySQLが起動するまで待つ）
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            test_conn = mysql.connector.connect(**mysql_config)
            # 既存データを確認
            cursor = test_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stations")
            count = cursor.fetchone()[0]
            cursor.close()
            test_conn.close()
            
            if count > 0:
                print(f"stationsテーブルには既に{count}件のデータが存在します。インポートをスキップします。")
                return True
            
            break
        except Error:
            retry_count += 1
            if retry_count < max_retries:
                print(f"MySQL接続を待機中... ({retry_count}/{max_retries})")
                import time
                time.sleep(2)
            else:
                print("エラー: MySQLに接続できませんでした")
                return False
    
    # CSVデータをインポート
    success = import_csv_to_mysql(csv_file_path, mysql_config)
    
    if success:
        print("=" * 60)
        print("CSVデータのインポートが完了しました")
        print("=" * 60)
        return True
    else:
        print("=" * 60)
        print("CSVデータのインポートに失敗しました")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

