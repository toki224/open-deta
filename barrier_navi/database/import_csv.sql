-- CSVファイルからstationsテーブルにデータをインポートするSQLスクリプト
-- MySQLコンテナの初期化時に実行されます

-- local_infileを有効化（セキュリティ上の理由でデフォルトで無効）
SET GLOBAL local_infile = 1;

-- 既存データを削除
DELETE FROM stations;

-- CSVファイルをインポート
-- 注意: カラムの順序とデータ型がCSVファイルと一致している必要があります
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/tokyo_stations.csv'
INTO TABLE stations
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    id,
    railway_operator,
    station_name,
    line_name,
    prefecture,
    city,
    step_response_status,
    num_platforms,
    num_step_free_platforms,
    num_elevators,
    num_compliant_elevators,
    num_escalators,
    num_compliant_escalators,
    num_other_lifts,
    num_slopes,
    num_compliant_slopes,
    has_tactile_paving,
    has_guidance_system,
    has_accessible_restroom,
    has_accessible_gate,
    has_accessible_ticket_machine,
    num_wheelchair_accessible_platforms,
    has_fall_prevention
);

-- インポート結果を確認
SELECT COUNT(*) as imported_count FROM stations;

