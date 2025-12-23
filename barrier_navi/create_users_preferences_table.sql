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
