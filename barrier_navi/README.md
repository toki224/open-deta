# バリアナビ（Barrier Navi）

駅のバリアフリー情報を提供し、障害者や高齢者など、移動に配慮が必要な方々が駅を利用する際の判断材料を提供するWebアプリケーションです。

## 概要

バリアナビは、MySQLデータベースに保存されている駅のバリアフリー設備情報を、身体障害・聴覚障害・視覚障害の3つのカテゴリに分けて評価し、スコアとして見える化するWebアプリケーションです。

### 主な特徴

- **3つの障害カテゴリに対応**
  - 身体障害向け（12項目評価）
  - 聴覚障害向け（4項目評価）
  - 視覚障害向け（9項目評価）

- **ユーザー認証機能**
  - ログイン・新規アカウント作成
  - プロフィール管理（お気に入り駅、優先機能設定）
  - ゲストモード（ログインなしで利用可能）

- **スコアリング機能**
  - 各駅のバリアフリー設備を評価項目に基づいてスコア化
  - 「達成項目数/総項目数 点」の形式で表示（例：8/12点）

- **検索・フィルタ機能**
  - 駅名検索
  - 都道府県フィルタ
  - バリアフリー設備フィルタ

## 構成

- **バックエンド**: Python Flask APIサーバー
- **フロントエンド**: TypeScript + HTML + CSS
- **データベース**: MySQL (stationデータベース)

## 必要な環境

- Python 3.x
- MySQL 8.0以上
- Node.js（TypeScriptコンパイル用、オプション）
- ブラウザ（Chrome、Firefox、Edgeなど）

## セットアップ

### 1. 環境変数ファイルの設定

`.env`ファイルを作成して、MySQL接続情報を設定してください。

**Windowsの場合:**
```bash
# .envファイルを新規作成
notepad .env
```

**Mac/Linuxの場合:**
```bash
# .envファイルを新規作成
touch .env
# または
nano .env
```

`.env`ファイルに以下の内容を記述してください：
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=station
```

`your_password_here`の部分を実際のMySQLパスワードに置き換えてください。

**重要**: `.env`ファイルには機密情報が含まれるため、Gitにコミットしないでください。`.gitignore`に追加されています。

### 2. Pythonパッケージのインストール

```bash
py -m pip install -r config/requirements.txt
```

または

```bash
pip install -r config/requirements.txt
```

### 3. TypeScriptのビルド（任意）

`frontend/dist/`フォルダにはコンパイル済みのJavaScriptファイルが含まれているため、Node.jsがなくてもブラウザ表示は可能です。  
TypeScriptを編集して再ビルドしたい場合のみ、下記手順を実行してください。

```bash
cd frontend
npm install          # 依存関係の取得
npm run build        # もしくは tsc
```

ビルド後は `frontend/dist/` フォルダ内のJavaScriptファイルが更新されます。

### 4. データベースの準備

1. MySQLサーバーを起動
2. `station`データベースを作成
3. `stations`テーブルを作成し、駅データをインポート
4. `users`テーブルと`users_preferences`テーブルを作成

テーブル作成スクリプトは`setup_users_preferences_table.py`を参考にしてください。

## 実行方法

### 1. APIサーバーの起動

```bash
py backend/api_server.py
```

または、Windowsの場合：

```bash
scripts\start.bat
```

APIサーバーは `http://localhost:5000` で起動します。

### 2. ブラウザでアクセス

ブラウザで以下のURLにアクセスしてください：

```
http://localhost:5000
```

ログイン画面が表示されます。

## 機能

### 認証機能

- **ログイン**: ユーザー名またはメールアドレスとパスワードでログイン
- **新規アカウント作成**: ユーザー名、メールアドレス、パスワードでアカウント作成
- **ゲストモード**: ログインなしで利用可能（個人設定の保存は不可）
- **パスワードリセット**: メールアドレスを入力してパスワードリセット用リンクを送信（メール送信機能は未実装）

### プロフィール機能

- **ユーザー情報管理**: ユーザー名の表示・編集
- **障害情報設定**: 障害の種類を選択（身体障害、聴覚障害、視覚障害）
- **お気に入り駅登録**: よく利用する駅を登録・管理
- **優先したい機能設定**: バリアフリー設備の優先度を設定

### 駅情報表示機能

- **ホーム画面**: 障害カテゴリ選択画面
- **一覧画面**: 駅一覧の表示（検索・フィルタ・ページネーション機能付き）
- **詳細画面**: 選択した駅のバリアフリー設備の詳細を表示

### スコアリング機能

各駅のバリアフリー度を、カテゴリごとに定義された評価項目をもとにスコア化します。

- **身体障害向け**: 12項目（フラグ型5項目、割合型3項目、数値型4項目）
- **聴覚障害向け**: 4項目（すべてフラグ型）
- **視覚障害向け**: 9項目（フラグ型6項目、割合型1項目、数値型3項目）

詳細は`スコア計算ロジック説明.txt`を参照してください。

## APIエンドポイント

### 認証関連

- `POST /api/auth/login` - ログイン処理
- `POST /api/auth/signup` - 新規ユーザー登録
- `POST /api/auth/reset-password` - パスワードリセット
- `GET /api/auth/profile` - プロフィール情報取得
- `PUT /api/auth/profile` - プロフィール情報更新

### 駅情報関連

- `GET /api/body/stations` - 身体障害向け駅一覧取得（スコア付き）
  - クエリ: `keyword`, `prefecture`, `limit`, `offset`, `weights` (JSON文字列)
- `GET /api/body/stations/<id>` - 身体障害向け駅詳細取得（スコア付き）
  - クエリ: `weights` (JSON文字列)
- `GET /api/hearing/stations` - 聴覚障害向け駅一覧取得（スコア付き）
- `GET /api/hearing/stations/<id>` - 聴覚障害向け駅詳細取得（スコア付き）
- `GET /api/vision/stations` - 視覚障害向け駅一覧取得（スコア付き）
- `GET /api/vision/stations/<id>` - 視覚障害向け駅詳細取得（スコア付き）

### その他のエンドポイント

- `GET /api/stations` - 駅一覧取得（生データ）
- `GET /api/stations/<id>` - 駅詳細取得（生データ）
- `GET /api/stations/prefectures` - 都道府県一覧取得
- `GET /api/stations/count` - 駅数取得
- `GET /api/stations/statistics` - 統計情報取得
- `GET /api/lines` - 路線一覧取得

### 静的ファイル

- `GET /` - ログイン画面
- `GET /login` - ログイン画面
- `GET /home` - ホーム画面
- `GET /index` - 一覧画面
- `GET /profile` - プロフィール画面
- `GET /detail` - 詳細画面

## ファイル構成

```
.
├── backend/                         # バックエンド（Python/Flask）
│   ├── api_server.py               # Flask APIサーバー
│   ├── database_connection.py      # データベース接続クラス
│   ├── setup_users_preferences_table.py # users_preferencesテーブルセットアップ
│   ├── check_*.py                  # データベース確認用スクリプト
│   └── test_*.py                   # テストスクリプト
├── frontend/                        # フロントエンド（TypeScript/HTML/CSS）
│   ├── src/                         # TypeScriptソースファイル
│   │   ├── login.ts                # ログイン画面のロジック
│   │   ├── home.ts                 # ホーム画面のロジック
│   │   ├── index.ts                # 一覧画面のロジック
│   │   ├── detail.ts               # 詳細画面のロジック
│   │   └── profile.ts              # プロフィール画面のロジック
│   ├── dist/                        # コンパイル済みJavaScriptファイル
│   │   ├── login.js
│   │   ├── home.js
│   │   ├── index.js
│   │   ├── detail.js
│   │   └── profile.js
│   ├── view/                        # HTMLファイル
│   │   ├── login.html              # ログイン画面
│   │   ├── home.html               # ホーム画面
│   │   ├── index.html              # 一覧画面（身体障害向け）
│   │   ├── detail.html             # 詳細画面
│   │   ├── profile.html            # プロフィール画面
│   │   ├── hearing.html            # 聴覚障害向け画面
│   │   └── vision.html             # 視覚障害向け画面
│   ├── styles.css                   # スタイルシート
│   ├── package.json                # Node.js依存関係
│   └── tsconfig.json               # TypeScript設定
├── database/                        # データベース関連
│   ├── init.sql                    # データベース初期化スクリプト
│   ├── DDL.sql                     # テーブル定義
│   ├── tokyo_stations.csv          # 駅データCSVファイル
│   ├── import_csv_data.py          # CSVインポートスクリプト
│   ├── import_csv.sql              # CSVインポートSQL
│   └── import_csv.sh               # CSVインポートシェルスクリプト
├── docker/                          # Docker関連
│   ├── Dockerfile                  # Dockerイメージ定義
│   ├── docker-compose.yml          # Docker Compose設定
│   ├── docker-entrypoint.sh        # エントリーポイントスクリプト
│   └── .dockerignore               # Docker除外設定
├── docs/                            # ドキュメント
│   ├── README.md                   # このファイル
│   ├── DOCKER_README.md            # Docker使用ガイド
│   ├── barianavi_spec.md           # バリアナビの詳細仕様書
│   ├── WEBアプリケーション概要.txt # アプリケーション概要
│   ├── スコア計算ロジック説明.txt  # スコア計算の詳細説明
│   ├── プログラム概要.txt          # 初心者向けプログラム説明
│   └── 優先機能自動絞り込み機能説明.txt # 優先機能自動絞り込み機能の説明
├── scripts/                         # スクリプト
│   └── start.bat                   # サーバー起動用バッチファイル（Windows）
├── config/                          # 設定ファイル
│   └── requirements.txt            # Python依存関係
├── .env                             # 環境変数ファイル（.gitignoreに含まれる）
└── .gitignore                       # Git除外設定
```

## 開発

### TypeScriptのビルド

TypeScriptファイルを変更した場合は、再度ビルドが必要です：

```bash
npm run build
```

または、ウォッチモードで自動ビルド：

```bash
npm run watch
```

### データベース確認スクリプト

以下のスクリプトでデータベースの状態を確認できます：

- `check_users_table.py` - usersテーブルの確認
- `check_users_preferences_table.py` - users_preferencesテーブルの確認
- `check_disability_data.py` - 障害データの確認
- `check_password.py` - パスワード確認
- `check_testuser.py` - テストユーザーの確認

## 注意事項

- MySQLサーバーが起動していることを確認してください
- `.env`ファイルにMySQL接続情報を設定してください
- CORSは開発環境用に有効化されています。本番環境では適切に設定してください
- バリアフリー設備の有無などのフラグ列は、データベース上で「1=○（設置あり）」「2=×（設置なし）」「3=-（該当なし）」として保存されています。本アプリでは値が1のときのみ設備があると判定して表示します
- パスワードはbcryptでハッシュ化して保存されます
- ゲストモードでは個人設定の保存はできません

## ドキュメント

- `WEBアプリケーション概要.txt` - アプリケーション全体の概要
- `スコア計算ロジック説明.txt` - スコア計算の詳細な仕組み
- `プログラム概要.txt` - 初心者向けプログラム説明
- `docs/barianavi_spec.md` - バリアナビの詳細仕様書

## ライセンス

（ライセンス情報を記載してください）

## 貢献

（貢献方法を記載してください）

## 更新履歴

- 2025年1月: 初版リリース
  - 身体障害・聴覚障害・視覚障害の3カテゴリ対応
  - ユーザー認証機能の実装
  - プロフィール機能の実装
