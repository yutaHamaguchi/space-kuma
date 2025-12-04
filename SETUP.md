# Space Guardian セットアップガイド（詳細版）

## 目次
1. [事前準備](#事前準備)
2. [GCPプロジェクト設定](#gcpプロジェクト設定)
3. [LINE Bot設定](#line-bot設定)
4. [インフラ構築](#インフラ構築)
5. [アプリケーションデプロイ](#アプリケーションデプロイ)
6. [動作確認](#動作確認)

## 事前準備

### 必要なツール
```bash
# gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Terraform
# Windows: Chocolatey経由
choco install terraform

# または公式サイトからダウンロード
# https://www.terraform.io/downloads
```

### LINE Developers アカウント
1. https://developers.line.biz/ にアクセス
2. LINEアカウントでログイン
3. プロバイダーを作成

## GCPプロジェクト設定

### 1. プロジェクト作成
```bash
# プロジェクトID（グローバルで一意）を決定
export PROJECT_ID="space-guardian-XXXXX"

# プロジェクト作成
gcloud projects create $PROJECT_ID --name="Space Guardian"

# デフォルトプロジェクトに設定
gcloud config set project $PROJECT_ID
```

### 2. 課金設定
```bash
# 課金アカウント一覧
gcloud beta billing accounts list

# 課金アカウントを紐付け
gcloud beta billing projects link $PROJECT_ID \
  --billing-account=XXXXXX-XXXXXX-XXXXXX
```

### 3. 必要なAPIの有効化
```bash
gcloud services enable \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

## LINE Bot設定

### 1. Messaging APIチャネル作成
1. LINE Developers Console → プロバイダー選択
2. 「Messaging API」チャネルを作成
3. チャネル基本設定で以下を確認：
   - Channel ID
   - Channel Secret
   - Channel Access Token（発行）

### 2. Webhook設定
デプロイ後に設定するため、ここではスキップ

### 3. User ID取得
```bash
# LINE公式アカウントを友だち追加後、
# 以下のツールでUser IDを確認
# https://developers.line.biz/console/
```

## インフラ構築

### 1. Terraform変数設定
```bash
cd terraform

# terraform.tfvarsファイルを作成
cat > terraform.tfvars <<EOF
project_id = "$PROJECT_ID"
region     = "asia-northeast1"
EOF
```

### 2. Terraform実行
```bash
# 初期化
terraform init

# プラン確認
terraform plan

# 適用（確認後yes）
terraform apply
```

### 3. サービスアカウント確認
```bash
# 作成されたサービスアカウントを確認
gcloud iam service-accounts list | grep space-guardian
```

## アプリケーションデプロイ

### 1. Artifact Registryへのログイン
```bash
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

### 2. デプロイスクリプト実行
```bash
cd ..  # プロジェクトルートへ
chmod +x deploy.sh
./deploy.sh $PROJECT_ID asia-northeast1
```

### 3. 環境変数設定

#### LINE Bot
```bash
export LINE_TOKEN="YOUR_CHANNEL_ACCESS_TOKEN"
export LINE_USER_ID="YOUR_USER_ID"

gcloud run services update line-bot \
  --region asia-northeast1 \
  --set-env-vars LINE_CHANNEL_ACCESS_TOKEN=$LINE_TOKEN,LINE_USER_ID=$LINE_USER_ID
```

#### Detection Job
```bash
LINE_BOT_URL=$(gcloud run services describe line-bot \
  --region asia-northeast1 \
  --format='value(status.url)')

gcloud run jobs update detection-job \
  --region asia-northeast1 \
  --set-env-vars LINE_NOTIFY_URL=${LINE_BOT_URL}/notify,PROJECT_ID=$PROJECT_ID
```

#### Data Ingest Job
```bash
gcloud run jobs update data-ingest-job \
  --region asia-northeast1 \
  --set-env-vars PROJECT_ID=$PROJECT_ID
```

## 動作確認

### 1. 手動ジョブ実行
```bash
# データ取得
gcloud run jobs execute data-ingest-job --region asia-northeast1 --wait

# 検知実行
gcloud run jobs execute detection-job --region asia-northeast1 --wait
```

### 2. ログ確認
```bash
# Data Ingestログ
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=data-ingest-job" \
  --limit 20 --format json

# Detectionログ
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=detection-job" \
  --limit 20 --format json
```

### 3. Firestore確認
```bash
# GCPコンソールでFirestoreを開く
echo "https://console.cloud.google.com/firestore/data?project=$PROJECT_ID"
```

### 4. ダッシュボードアクセス
```bash
# URLを取得
DASHBOARD_URL=$(gcloud run services describe dashboard \
  --region asia-northeast1 \
  --format='value(status.url)')

echo "Dashboard: $DASHBOARD_URL"
```

## トラブルシューティング

### ジョブが権限エラーで失敗
```bash
# サービスアカウントに権限を追加
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:space-guardian-runner@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

### LINE通知が届かない
1. Channel Access Tokenが正しいか確認
2. User IDが正しいか確認（`U`で始まる文字列）
3. LINE Botのログを確認

### Cloud Schedulerが動かない
```bash
# Schedulerの状態確認
gcloud scheduler jobs describe data-ingest-trigger --location asia-northeast1

# 手動実行
gcloud scheduler jobs run data-ingest-trigger --location asia-northeast1
```

## 次のステップ
- `verification_plan.md` の手動確認項目を実施
- 定期実行の動作を24時間監視
- フェーズ1への移行を検討
