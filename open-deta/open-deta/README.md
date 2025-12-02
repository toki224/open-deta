## Gitの使い方

ここでは、このリポジトリでGitを利用する際によく使う基本的なコマンドと手順をまとめています。PowerShellなどのターミナルで実行してください。

### 初期設定
- **ユーザー名とメールアドレスの設定**
  ```powershell
  git config --global user.name "あなたの名前"
  git config --global user.email "you@example.com"
  ```
- **現在の設定を確認**
  ```powershell
  git config --list
  ```

### リポジトリの取得
- **初めて取得する場合**
  ```powershell
  git clone <リポジトリのURL>
  ```
- **既に取得済みの場合、最新状態へ更新**
  ```powershell
  git pull
  ```

### 変更内容の確認
- **現在の作業状況を確認**
  ```powershell
  git status
  ```
- **変更差分を確認**
  ```powershell
  git diff
  ```

### 変更の登録とコミット
- **すべての変更をステージング**
  ```powershell
  git add .
  ```
- **特定ファイルのみステージング**
  ```powershell
  git add <ファイルパス>
  ```
- **ステージング済みの内容をコミット**
  ```powershell
  git commit -m "変更内容を表すメッセージ"
  ```

### リモートリポジトリへの反映
- **変更をプッシュ**
  ```powershell
  git push
  ```
- **初めてブランチをプッシュする場合**
  ```powershell
  git push -u origin <ブランチ名>
  ```

### ブランチ操作
- **ブランチ一覧を確認**
  ```powershell
  git branch
  ```
- **新しいブランチを作成して切り替え**
  ```powershell
  git checkout -b <ブランチ名>
  ```
- **既存のブランチへ切り替え**
  ```powershell
  git checkout <ブランチ名>
  ```

### 変更を取り消す
- **ステージング前の変更を元に戻す**
  ```powershell
  git checkout -- <ファイルパス>
  ```
- **ステージングを解除**
  ```powershell
  git reset HEAD <ファイルパス>
  ```
- **コミットをやり直す（直前のコミットを変更）**
  ```powershell
  git commit --amend
  ```

### よくあるワークフロー
1. `git pull` で最新の変更を取得
2. 変更を加える
3. `git status` や `git diff` で確認
4. `git add` でステージング
5. `git commit` でコミット
6. `git push` で共有

### トラブルシューティング
- **マージやプル時の競合が発生した場合**
  1. 競合箇所をエディタで修正
  2. 修正済みファイルを `git add`
  3. `git commit` または `git merge --continue`

- **履歴をきれいに保ちたい場合**
  - 作業ごとにブランチを分け、完了後にメインブランチへマージする
  - 意味のあるコミットメッセージを付ける
