# 駅データ表示アプリケーション（バリアナビ・身体障害モード）

MySQLの駅データをもとに、身体障害の方向けにバリアフリー指標を見える化するWebアプリケーションです。  
現在は「バリアナビ」の身体障害カテゴリに特化したUIとAPIを実装しています。

## 構成

- **バックエンド**: Python Flask APIサーバー
- **フロントエンド**: TypeScript + HTML + CSS
- **データベース**: MySQL (stationデータベース)

## セットアップ

### 1. Pythonパッケージのインストール

```bash
py -m pip install -r requirements.txt
```

### 2. TypeScriptのビルド（任意）

`dist/index.js`は同梱済みのため、Node.jsがなくてもブラウザ表示は可能です。  
TypeScriptを編集して再ビルドしたい場合のみ、下記手順を実行してください。

```bash
npm install          # 依存関係の取得
npm run build        # もしくは tsc
```

ビルド後は `dist/index.js` が更新されます。

## 実行方法

### 1. APIサーバーの起動

```bash
py api_server.py
```

APIサーバーは `http://localhost:5000` で起動します。

### 2. ブラウザで表示

`index.html`をブラウザで開いてください。

または、簡単なHTTPサーバーを使用する場合：

```bash
# Python 3の場合
py -m http.server 8000
```

その後、ブラウザで `http://localhost:8000` にアクセスしてください。

## 機能

- 身体障害カテゴリに特化した駅スコアの一覧表示
- 駅名検索／都道府県フィルタ／重み付け設定による絞り込み
- 15項目のバリアフリー設備をもとにしたスコアリング（`8/15点` など）
- 駅カードをクリックすると専用の詳細画面に遷移し、項目内訳を確認可能
- フロント（TypeScript）とバックエンド（Flask）のAPI連携

## APIエンドポイント

- `GET /api/body/stations`  
  - クエリ: `keyword`, `prefecture`, `limit`, `offset`, `weights` (JSON文字列)  
  - 返却: 身体障害向けスコア付きの駅一覧
- `GET /api/body/stations/<id>`  
  - クエリ: `weights` (JSON文字列)  
  - 返却: 指定駅の身体障害向け内訳
- 既存エンドポイント（統計や生データ取得用）  
  - `GET /api/stations`, `/api/stations/<id>`, `/api/stations/prefectures` など

## ファイル構成

```
.
├── api_server.py          # Flask APIサーバー
├── database_connection.py  # データベース接続クラス
├── index.html             # 一覧ページ
├── detail.html            # 詳細ページ
├── styles.css             # スタイルシート
├── src/
│   ├── index.ts          # 一覧ページのTypeScript
│   └── detail.ts         # 詳細ページのTypeScript
├── dist/
│   ├── index.js          # 一覧ページのJavaScript
│   └── detail.js         # 詳細ページのJavaScript
├── package.json          # Node.js依存関係
├── tsconfig.json         # TypeScript設定
└── requirements.txt     # Python依存関係
```

## 開発

TypeScriptファイルを変更した場合は、再度ビルドが必要です：

```bash
npm run build
```

または、ウォッチモードで自動ビルド：

```bash
npm run watch
```

## 注意事項

- MySQLサーバーが起動していることを確認してください
- `api_server.py`内のMySQL接続情報を環境に合わせて設定してください
- CORSは開発環境用に有効化されています。本番環境では適切に設定してください
- バリアフリー設備の有無などのフラグ列は、データベース上で「1=○（設置あり）」「2=×（設置なし）」「3=-（該当なし）」として保存されています。本アプリでは値が1のときのみ設備があると判定して表示します
- 「バリアナビ」構想の詳細仕様は `docs/barianavi_spec.md` に記載しています（身体障害カテゴリの指標・必要値など）
