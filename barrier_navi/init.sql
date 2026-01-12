-- データベース初期化スクリプト
-- Dockerコンテナ起動時に自動実行されます

-- stationsテーブルを作成
CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY,
    railway_operator VARCHAR(255),
    station_name VARCHAR(255),
    line_name TEXT,
    prefecture VARCHAR(255),
    city VARCHAR(255),
    step_response_status INTEGER,
    num_platforms INTEGER,
    num_step_free_platforms INTEGER,
    num_elevators INTEGER,
    num_compliant_elevators INTEGER,
    num_escalators INTEGER,
    num_compliant_escalators INTEGER,
    num_other_lifts INTEGER,
    num_slopes INTEGER,
    num_compliant_slopes INTEGER,
    has_tactile_paving INTEGER,
    has_guidance_system INTEGER,
    has_accessible_restroom INTEGER,
    has_accessible_gate INTEGER,
    has_accessible_ticket_machine INTEGER,
    num_wheelchair_accessible_platforms INTEGER,
    has_fall_prevention INTEGER
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- usersテーブルを作成
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- users_preferencesテーブルを作成
CREATE TABLE IF NOT EXISTS users_preferences (
    user_id INT PRIMARY KEY,
    disability_type TEXT NULL COMMENT '障害の種類（JSON配列形式）',
    favorite_stations TEXT NULL COMMENT 'お気に入りの駅のIDリスト（JSON配列形式）',
    preferred_features TEXT NULL COMMENT '優先したい機能のリスト（JSON配列形式）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

