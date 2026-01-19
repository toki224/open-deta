# RDS DBサブネットグループの修正ガイド

「DB subnet group doesn't meet Availability Zone (AZ) coverage requirement」エラーの解決方法

## 問題の原因

RDSは高可用性のため、**少なくとも2つの異なる可用性ゾーン（AZ）にサブネットが必要**です。現在のDBサブネットグループには1つのAZ（us-east-1a）しか含まれていません。

## 解決方法

### 方法1: AWS Consoleを使用（推奨）

#### ステップ1: 現在のVPCとサブネットを確認

1. **VPC Console**に移動
2. 左メニューから「サブネット」を選択
3. あなたのVPCのサブネットを確認
   - 現在のサブネットがどのAZにあるか確認
   - 例：`us-east-1a`にサブネットが1つだけある場合

#### ステップ2: 2つ目のAZにサブネットを作成

1. **VPC Console**で「サブネット」→「サブネットを作成」をクリック
2. 以下の設定で作成：
   - **VPC**: 既存のVPCを選択（例：barrier-navi-vpc）
   - **サブネット名**: `barrier-navi-db-subnet-2` など
   - **可用性ゾーン**: **us-east-1b** または **us-east-1c** を選択（1つ目のサブネットと異なるAZ）
   - **IPv4 CIDRブロック**: `10.0.21.0/24` など（既存のサブネットと重複しない範囲）
     - 例：既存が `10.0.20.0/24` なら、`10.0.21.0/24` を使用

3. 「サブネットを作成」をクリック

#### ステップ3: DBサブネットグループを修正または再作成

**オプションA: 既存のDBサブネットグループを修正**

1. **RDS Console**に移動
2. 左メニューから「サブネットグループ」を選択
3. 既存のDBサブネットグループを選択
4. 「編集」をクリック
5. 「サブネットの追加」をクリック
6. ステップ2で作成したサブネットを選択
7. 「変更を保存」をクリック

**オプションB: 新しいDBサブネットグループを作成**

1. **RDS Console**で「サブネットグループ」→「DBサブネットグループを作成」をクリック
2. 設定：
   - **名前**: `barrier-navi-db-subnet-group`
   - **説明**: `Subnet group for RDS MySQL`
   - **VPC**: 既存のVPCを選択
   - **可用性ゾーン**: 
     - **us-east-1a**: 既存のサブネットを選択
     - **us-east-1b** または **us-east-1c**: ステップ2で作成したサブネットを選択
3. 「作成」をクリック

#### ステップ4: RDSインスタンスを作成

1. **RDS Console**で「データベース」→「データベースの作成」をクリック
2. 設定：
   - **エンジンのタイプ**: MySQL
   - **DBインスタンス識別子**: `barrier-navi-mysql`
   - **マスターユーザー名**: `barrier_user`
   - **マスターパスワード**: 強力なパスワードを設定
   - **DBインスタンスクラス**: `db.t3.micro`
   - **ストレージ**: 20GB
   - **VPC**: 既存のVPCを選択
   - **DBサブネットグループ**: ステップ3で作成/修正したサブネットグループを選択
   - **パブリックアクセス**: はい（開発用）
   - **VPCセキュリティグループ**: 既存のセキュリティグループを選択または新規作成
3. 「データベースの作成」をクリック

---

### 方法2: AWS CLIを使用

#### ステップ1: 現在のサブネットを確認

```powershell
# PowerShellで実行
# VPC IDを確認（例：vpc-xxxxxxxxx）
$VPC_ID = "vpc-xxxxxxxxx"  # 実際のVPC IDに置き換え

# 現在のサブネットを確認
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].[SubnetId,AvailabilityZone,CidrBlock]' --output table
```

#### ステップ2: 2つ目のAZにサブネットを作成

```powershell
# リージョンを設定
$AWS_REGION = "us-east-1"

# 2つ目のAZにサブネットを作成（us-east-1bを使用）
$SUBNET_2 = aws ec2 create-subnet `
    --vpc-id $VPC_ID `
    --cidr-block 10.0.21.0/24 `
    --availability-zone ${AWS_REGION}b `
    --query 'Subnet.SubnetId' `
    --output text

# サブネットに名前を付ける
aws ec2 create-tags `
    --resources $SUBNET_2 `
    --tags Key=Name,Value=barrier-navi-db-subnet-2

Write-Host "作成したサブネットID: $SUBNET_2"
```

#### ステップ3: DBサブネットグループを作成

```powershell
# 既存のサブネットIDを取得（us-east-1aのサブネット）
# ステップ1の結果から、us-east-1aのサブネットIDを取得
$SUBNET_1 = "subnet-xxxxxxxxx"  # 実際のサブネットIDに置き換え

# DBサブネットグループを作成
aws rds create-db-subnet-group `
    --db-subnet-group-name barrier-navi-db-subnet-group `
    --db-subnet-group-description "Subnet group for RDS MySQL" `
    --subnet-ids $SUBNET_1 $SUBNET_2 `
    --region $AWS_REGION
```

#### ステップ4: RDSインスタンスを作成

```powershell
# 変数を設定
$RDS_PASSWORD = "your-secure-password"  # 強力なパスワードに置き換え
$RDS_SG_ID = "sg-xxxxxxxxx"  # RDS用セキュリティグループIDに置き換え

# RDSインスタンスを作成
aws rds create-db-instance `
    --db-instance-identifier barrier-navi-mysql `
    --db-instance-class db.t3.micro `
    --engine mysql `
    --engine-version 8.0.35 `
    --master-username barrier_user `
    --master-user-password $RDS_PASSWORD `
    --allocated-storage 20 `
    --storage-type gp3 `
    --db-name station `
    --vpc-security-group-ids $RDS_SG_ID `
    --db-subnet-group-name barrier-navi-db-subnet-group `
    --backup-retention-period 7 `
    --publicly-accessible `
    --storage-encrypted `
    --region $AWS_REGION

Write-Host "RDSインスタンスの作成を開始しました。完了まで10-15分かかります。"
```

---

## 利用可能な可用性ゾーンの確認

リージョン内の利用可能なAZを確認する方法：

```powershell
# PowerShell
aws ec2 describe-availability-zones --region us-east-1 --query 'AvailabilityZones[*].[ZoneName,State]' --output table
```

一般的なus-east-1のAZ：
- `us-east-1a`
- `us-east-1b`
- `us-east-1c`
- `us-east-1d`
- `us-east-1e`
- `us-east-1f`

**重要**: アカウントによって利用可能なAZが異なる場合があります。必ず上記のコマンドで確認してください。

---

## サブネットCIDRブロックの推奨値

VPCが `10.0.0.0/16` の場合、以下のようにサブネットを分割することを推奨します：

| サブネット | CIDRブロック | 用途 | AZ |
|-----------|------------|------|-----|
| DBサブネット1 | 10.0.20.0/24 | RDS | us-east-1a |
| DBサブネット2 | 10.0.21.0/24 | RDS | us-east-1b または us-east-1c |

---

## トラブルシューティング

### 問題: サブネットを作成できない

**原因**: CIDRブロックが既存のサブネットと重複している

**解決方法**:
- VPC内の既存サブネットのCIDRブロックを確認
- 重複しない範囲を選択（例：`10.0.22.0/24`、`10.0.23.0/24`など）

### 問題: DBサブネットグループにサブネットを追加できない

**原因**: サブネットが異なるVPCに属している

**解決方法**:
- すべてのサブネットが同じVPCに属していることを確認
- VPC IDが一致しているか確認

---

## まとめ

1. ✅ **2つ目のAZにサブネットを作成**（例：us-east-1b）
2. ✅ **DBサブネットグループに2つのサブネットを追加**
3. ✅ **RDSインスタンスを作成**

これでRDSの要件を満たし、インスタンスを作成できるようになります。
