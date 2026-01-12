# Python Flaskアプリケーション用のDockerfile
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新と必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Node.jsとnpmをインストール（TypeScriptコンパイル用）
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# package.jsonとtsconfig.jsonをコピーしてTypeScript依存関係をインストール
COPY package.json package-lock.json* tsconfig.json ./
RUN npm install

# アプリケーションのソースコードをコピー
COPY . .

# TypeScriptをコンパイル
RUN npm run build

# ポート5000を公開
EXPOSE 5000

# 環境変数の設定（デフォルト値）
ENV FLASK_APP=api_server.py
ENV FLASK_ENV=production

# エントリーポイントスクリプトをコピー
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# アプリケーションを起動
ENTRYPOINT ["/app/docker-entrypoint.sh"]

