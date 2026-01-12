# Dockerを使用したバリアナビのセットアップ

このドキュメントでは、Dockerを使用してバリアナビをローカル環境に依存せずに実行する方法を説明します。

## 前提条件

- Docker Desktop（Windows/Mac）またはDocker Engine（Linux）がインストールされていること
- Docker Composeが利用可能であること（通常、Docker Desktopに含まれています）

## セットアップ手順

### 1. 環境変数ファイルの作成

プロジェクトのルートディレクトリ（`barrier_navi`フォルダ）に`.env`ファイルを作成し、以下の内容を記述してください：

```env
# MySQL設定
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=station
MYSQL_USER=barrier_user
MYSQL_PASSWORD=barrier_password
MYSQL_PORT=3307

# Flask設定
FLASK_PORT=5000
FLASK_ENV=production
```

**注意**: デフォルトでMySQLポートは3307に設定されています（ローカルのMySQLと競合しないように）。必要に応じて変更してください。

**重要**: 本番環境では必ず強力なパスワードに変更してください。

### 2. Dockerイメージのビルドと起動

以下のコマンドでDockerコンテナをビルドして起動します：

```bash
docker-compose up -d --build
```

初回起動時は、イメージのビルドとデータベースの初期化に時間がかかります。

### 3. データベースの初期化

`init.sql`ファイルが自動的に実行され、必要なテーブル（`stations`、`users`、`users_preferences`）が作成されます。

その後、`import_csv.sql`が自動実行され、`tokyo_stations.csv`ファイルから駅データがインポートされます。

**注意**: 初回起動時のみデータがインポートされます。既存のデータベースがある場合は、データはインポートされません。

データを再インポートしたい場合は、以下の手順を実行してください：

```bash
# コンテナとボリュームを削除（データベースデータも削除されます）
docker-compose down -v

# 再度起動（データが再インポートされます）
docker-compose up -d
```

### 4. アプリケーションへのアクセス

ブラウザで以下のURLにアクセスしてください：

```
http://localhost:5000
```

## よく使うコマンド

### コンテナの起動

```bash
docker-compose up -d
```

### コンテナの停止

```bash
docker-compose down
```

### コンテナの停止とボリュームの削除（データベースデータも削除）

```bash
docker-compose down -v
```

### ログの確認

```bash
# すべてのサービスのログ
docker-compose logs

# Webサーバーのログのみ
docker-compose logs web

# データベースのログのみ
docker-compose logs db

# リアルタイムでログを表示
docker-compose logs -f web
```

### コンテナ内でのコマンド実行

```bash
# Webコンテナ内でシェルを実行
docker-compose exec web bash

# データベースコンテナ内でMySQLに接続
docker-compose exec db mysql -u barrier_user -pbarrier_password station
```

### コンテナの再ビルド

```bash
# イメージを再ビルドして起動
docker-compose up -d --build

# キャッシュを使わずに再ビルド
docker-compose build --no-cache
```

## トラブルシューティング

### ポートが既に使用されている場合

デフォルトでMySQLポートは3307に設定されていますが、それでも競合する場合は`.env`ファイルでポート番号を変更してください：

```env
FLASK_PORT=5001
MYSQL_PORT=3308
```

**注意**: ポートを変更した場合、Webコンテナ内の`MYSQL_PORT`環境変数は変更しないでください（コンテナ間通信では内部ポート3306を使用します）。

### データベースに接続できない場合

1. データベースコンテナが起動しているか確認：
   ```bash
   docker-compose ps
   ```

2. データベースのログを確認：
   ```bash
   docker-compose logs db
   ```

3. データベースのヘルスチェックを確認：
   ```bash
   docker-compose exec db mysqladmin ping -h localhost -u root -prootpassword
   ```

### TypeScriptのコンパイルエラー

TypeScriptのコンパイルに失敗する場合、以下のコマンドでコンテナ内で直接ビルドできます：

```bash
docker-compose exec web npm run build
```

### データベースのデータをリセットしたい場合

```bash
# コンテナとボリュームを削除
docker-compose down -v

# 再度起動（データが再インポートされます）
docker-compose up -d
```

### CSVデータのインポートに失敗した場合

`import_csv.sql`での自動インポートに失敗した場合は、Pythonスクリプトを使用して手動でインポートできます：

```bash
# Webコンテナ内でPythonスクリプトを実行
docker-compose exec web python /app/import_csv_data.py
```

または、MySQLコンテナに直接接続して手動でインポート：

```bash
# MySQLコンテナに接続
docker-compose exec db bash

# コンテナ内で以下を実行
mysql -u barrier_user -pbarrier_password station
# その後、LOAD DATA INFILEコマンドを実行
```

## 開発時の注意事項

### ホットリロード（開発モード）

開発時にコードの変更を自動反映させたい場合は、`docker-compose.yml`の`web`サービスの`volumes`セクションのコメントを外してください：

```yaml
volumes:
  - .:/app
```

ただし、この場合、TypeScriptの変更は手動でビルドする必要があります。

### 環境変数の変更

`.env`ファイルを変更した後は、コンテナを再起動してください：

```bash
docker-compose restart
```

## 本番環境へのデプロイ

本番環境にデプロイする場合は、以下の点に注意してください：

1. **セキュリティ**:
   - `.env`ファイルに強力なパスワードを設定
   - 不要なポートを公開しない
   - HTTPSを使用する（リバースプロキシを使用）

2. **パフォーマンス**:
   - `FLASK_ENV=production`に設定
   - 本番用のWSGIサーバー（Gunicornなど）を使用することを検討

3. **データベース**:
   - データベースのバックアップを定期的に取得
   - 本番環境では専用のデータベースサーバーを使用することを推奨

## ファイル構成

Docker化に関連するファイル：

- `Dockerfile`: Python Flaskアプリケーション用のDockerイメージ定義
- `docker-compose.yml`: サービス（Web、DB）の定義と設定
- `.dockerignore`: Dockerイメージに含めないファイルのリスト
- `init.sql`: データベース初期化スクリプト（テーブル作成）
- `import_csv.sql`: CSVデータインポートスクリプト（自動実行）
- `tokyo_stations.csv`: 駅データのCSVファイル
- `import_csv_data.py`: Python版CSVインポートスクリプト（手動実行用）
- `.env`: 環境変数設定（Gitにコミットしない）

## サポート

問題が発生した場合は、以下の情報を含めてお問い合わせください：

- Dockerのバージョン（`docker --version`）
- Docker Composeのバージョン（`docker-compose --version`）
- エラーメッセージ（`docker-compose logs`の出力）

