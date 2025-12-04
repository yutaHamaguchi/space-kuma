# Space Guardian (GCP版) - フェーズ0: 無料プロトタイプ

衛星画像AI解析による緊急事態検知システム - 北摂・丹波篠山エリア広域監視

## 概要
広域エリアの衛星画像（SAR）を定期取得し、AIによる変化検知で異常候補を特定。LINEを通じて管理者に通知するシステムです。

**現在のフェーズ**: フェーズ0（無料プロトタイプ）
- モックデータを使用した動作確認
- GPU/AIモデルは使用せず、簡易ロジックで代用
- GCP無料枠内での動作を想定

## アーキテクチャ

```
Cloud Scheduler (10分毎)
    ↓
Data Ingest Job (Cloud Run Jobs)
    ↓ サンプル画像をGCSにコピー
GCS (raw-data bucket)
    ↓
Detection Job (Cloud Run Jobs)
    ↓ 簡易検知ロジック (30%確率でランダム検知)
Firestore (検知結果保存)
    ↓ (検知時)
LINE Bot (Cloud Run Service)
    ↓
LINE通知 → 管理者
```

## 構成
- **Data Ingest**: Cloud Run Jobs (モックデータローダー)
- **Detection**: Cloud Run Jobs (簡易CPU検知)
- **Notification**: Cloud Run Service (LINE Messaging API)
- **Dashboard**: Cloud Run Service (Streamlit)

## セットアップ

### 前提条件
- Google Cloud Platform アカウント
- gcloud CLI インストール済み
- Terraform インストール済み
- LINE Developers アカウント（Messaging API）

### 1. GCPプロジェクト作成

```bash
# プロジェクト作成
gcloud projects create YOUR_PROJECT_ID

# プロジェクト設定
gcloud config set project YOUR_PROJECT_ID

# 課金アカウント紐付け（必須）
gcloud beta billing accounts list
gcloud beta billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

### 2. Terraformでインフラ構築

```bash
cd terraform

# 初期化
terraform init

# 変数設定
export TF_VAR_project_id=YOUR_PROJECT_ID
export TF_VAR_region=asia-northeast1

# プラン確認
terraform plan

# 適用
terraform apply
```

### 3. LINE Bot設定

1. [LINE Developers Console](https://developers.line.biz/) でMessaging APIチャネルを作成
2. Channel Access Tokenを取得
3. 管理者のLINE User IDを取得（LINE公式アカウントを友だち追加）

### 4. デプロイ

```bash
# デプロイスクリプト実行
chmod +x deploy.sh
./deploy.sh YOUR_PROJECT_ID asia-northeast1
```

### 5. 環境変数設定

LINE Botサービスに環境変数を設定：

```bash
gcloud run services update line-bot \
  --region asia-northeast1 \
  --set-env-vars LINE_CHANNEL_ACCESS_TOKEN=YOUR_TOKEN,LINE_USER_ID=YOUR_USER_ID
```

Detection Jobに通知URLを設定：

```bash
# LINE BotのURLを取得
LINE_BOT_URL=$(gcloud run services describe line-bot --region asia-northeast1 --format='value(status.url)')

gcloud run jobs update detection-job \
  --region asia-northeast1 \
  --set-env-vars LINE_NOTIFY_URL=${LINE_BOT_URL}/notify
```

### 6. 動作確認

```bash
# Data Ingestジョブを手動実行
gcloud run jobs execute data-ingest-job --region asia-northeast1

# Detection Jobを手動実行
gcloud run jobs execute detection-job --region asia-northeast1

# ダッシュボードURLを取得
gcloud run services describe dashboard --region asia-northeast1 --format='value(status.url)'
```

## 使い方

### 自動実行
Cloud Schedulerにより10分ごとに自動実行されます。

### 手動実行
```bash
# データ取得
gcloud run jobs execute data-ingest-job --region asia-northeast1

# 検知実行
gcloud run jobs execute detection-job --region asia-northeast1
```

### ダッシュボード
ブラウザでダッシュボードURLにアクセスし、検知履歴を確認できます。

## コスト試算（フェーズ0）

無料枠内での運用を想定：
- Cloud Run Jobs: 無料枠内（月180,000 vCPU秒）
- Cloud Run Services: 無料枠内（月2,000,000リクエスト）
- Firestore: 無料枠内（1日50,000読み取り）
- Cloud Storage: 5GB以下（無料枠内）

**想定月額**: ¥0〜¥500程度

## 次のステップ（フェーズ1）

プロトタイプ検証後、以下を実装：
- 実際の衛星データAPI連携（Tellus）
- GPU環境でのAI推論（SAR-ChangeNet v2）
- 本番運用体制の構築

## トラブルシューティング

### ジョブが失敗する
```bash
# ログ確認
gcloud logging read "resource.type=cloud_run_job" --limit 50
```

### LINE通知が届かない
- Channel Access Tokenが正しいか確認
- User IDが正しいか確認
- LINE Botサービスのログを確認

## ライセンス
MIT License
