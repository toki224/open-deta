#!/bin/bash
# バリアナビ AWSデプロイスクリプト
# 使用方法: ./scripts/aws-deploy.sh

set -e

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# エラーハンドリング
error_exit() {
    echo -e "${RED}エラー: $1${NC}" >&2
    exit 1
}

success_msg() {
    echo -e "${GREEN}✓ $1${NC}"
}

info_msg() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 前提条件のチェック
check_prerequisites() {
    info_msg "前提条件を確認中..."
    
    # AWS CLIの確認
    if ! command -v aws &> /dev/null; then
        error_exit "AWS CLIがインストールされていません"
    fi
    
    # Dockerの確認
    if ! command -v docker &> /dev/null; then
        error_exit "Dockerがインストールされていません"
    fi
    
    # AWS認証情報の確認
    if ! aws sts get-caller-identity &> /dev/null; then
        error_exit "AWS認証情報が設定されていません。'aws configure'を実行してください"
    fi
    
    success_msg "前提条件の確認が完了しました"
}

# 変数の設定
setup_variables() {
    info_msg "変数を設定中..."
    
    export PROJECT_NAME=${PROJECT_NAME:-barrier-navi}
    export AWS_REGION=${AWS_REGION:-ap-northeast-1}
    export AWS_DEFAULT_REGION=$AWS_REGION
    
    export ECR_REPO_NAME=${PROJECT_NAME}
    export ECS_CLUSTER_NAME=${PROJECT_NAME}-cluster
    export RDS_DB_NAME=station
    export RDS_USERNAME=${RDS_USERNAME:-barrier_user}
    
    # パスワードが設定されていない場合は生成
    if [ -z "$RDS_PASSWORD" ]; then
        if command -v openssl &> /dev/null; then
            export RDS_PASSWORD=$(openssl rand -base64 32)
        else
            error_exit "RDS_PASSWORDが設定されておらず、opensslも利用できません"
        fi
    fi
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    export ECR_REGISTRY=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
    
    success_msg "変数の設定が完了しました"
    echo "  プロジェクト名: $PROJECT_NAME"
    echo "  AWSリージョン: $AWS_REGION"
    echo "  ECRレジストリ: $ECR_REGISTRY"
}

# ECRリポジトリの作成
create_ecr_repo() {
    info_msg "ECRリポジトリを作成中..."
    
    if aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION &> /dev/null; then
        info_msg "ECRリポジトリは既に存在します"
    else
        aws ecr create-repository \
            --repository-name $ECR_REPO_NAME \
            --region $AWS_REGION \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256
        
        success_msg "ECRリポジトリを作成しました"
    fi
}

# Dockerイメージのビルドとプッシュ
build_and_push_image() {
    info_msg "Dockerイメージをビルド中..."
    
    # ECRにログイン
    aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin $ECR_REGISTRY || \
        error_exit "ECRへのログインに失敗しました"
    
    # プロジェクトルートに移動
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
    cd "$PROJECT_ROOT"
    
    # イメージをビルド
    docker build -f docker/Dockerfile -t ${ECR_REPO_NAME}:latest . || \
        error_exit "Dockerイメージのビルドに失敗しました"
    
    # タグを付ける
    docker tag ${ECR_REPO_NAME}:latest ${ECR_REGISTRY}/${ECR_REPO_NAME}:latest
    
    # プッシュ
    info_msg "DockerイメージをECRにプッシュ中..."
    docker push ${ECR_REGISTRY}/${ECR_REPO_NAME}:latest || \
        error_exit "Dockerイメージのプッシュに失敗しました"
    
    success_msg "Dockerイメージをビルドしてプッシュしました"
}

# メイン処理
main() {
    echo "=========================================="
    echo "バリアナビ AWSデプロイスクリプト"
    echo "=========================================="
    echo ""
    
    check_prerequisites
    setup_variables
    create_ecr_repo
    build_and_push_image
    
    echo ""
    success_msg "デプロイ準備が完了しました！"
    echo ""
    echo "次のステップ:"
    echo "1. AWS_DEPLOYMENT.mdの手順に従って、RDS、ECS、ALBを設定してください"
    echo "2. または、AWS Consoleから手動で設定してください"
    echo ""
    echo "設定された変数:"
    echo "  PROJECT_NAME: $PROJECT_NAME"
    echo "  AWS_REGION: $AWS_REGION"
    echo "  ECR_REGISTRY: $ECR_REGISTRY"
    echo "  ECR_REPO_NAME: $ECR_REPO_NAME"
    if [ -n "$RDS_PASSWORD" ]; then
        echo "  RDS_PASSWORD: (設定済み)"
    fi
}

# スクリプトを実行
main "$@"
