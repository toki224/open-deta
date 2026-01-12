CREATE TABLE stations (
id INTEGER PRIMARY KEY,           -- ID
railway_operator VARCHAR(255),    -- 鉄道事業者名
station_name VARCHAR(255),        -- 鉄道駅の名称
line_name TEXT,                   -- 路線名
prefecture VARCHAR(255),          -- 都道府県
city VARCHAR(255),                -- 市
step_response_status INTEGER,     -- 段差への対応
num_platforms INTEGER,            -- プラットホームの数
num_step_free_platforms INTEGER,  -- 段差が解消されているプラットホームの数
num_elevators INTEGER,            -- エレベーターの設置基数
num_compliant_elevators INTEGER,  -- 移動等円滑化基準に適合しているエレベーターの設置基数
num_escalators INTEGER,           -- エスカレーターの設置基数
num_compliant_escalators INTEGER, -- 移動等円滑化基準に適合しているエスカレーターの設置基数
num_other_lifts INTEGER,          -- その他の昇降機の設置基数
num_slopes INTEGER,               -- 傾斜路の設置箇所数
num_compliant_slopes INTEGER,     -- 移動等円滑化基準に適合している傾斜路の設置箇所数
has_tactile_paving INTEGER,       -- 視覚障害者誘導用ブロックの設置の有無
has_guidance_system INTEGER,      -- 案内設備の設置の有無
has_accessible_restroom INTEGER,  -- 障害者対応型便所の設置の有無
has_accessible_gate INTEGER,      -- 障害者対応型改札口の設置の有無
has_accessible_ticket_machine INTEGER, -- 障害者対応型券売機の設置の有無
num_wheelchair_accessible_platforms INTEGER, -- 車いす使用者の円滑な乗降が可能なプラットホームの数
has_fall_prevention INTEGER       -- 転落防止のための設備の設置の有無
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

-- users_preferencesテーブルを作成するSQLスクリプト
-- ユーザーのプロフィール設定を保存するテーブル

-- テーブルが存在しない場合のみ作成
CREATE TABLE IF NOT EXISTS users_preferences (
    user_id INT PRIMARY KEY,
    disability_type TEXT NULL COMMENT '障害の種類（JSON配列形式）',
    favorite_stations TEXT NULL COMMENT 'お気に入りの駅のIDリスト（JSON配列形式）',
    preferred_features TEXT NULL COMMENT '優先したい機能のリスト（JSON配列形式）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- テーブル構造の確認
-- DESCRIBE users_preferences;
