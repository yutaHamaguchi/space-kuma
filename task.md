# Space Guardian タスクリスト

*フェーズ0: 無料枠でのプロトタイプ構築*

## フェーズ0: 無料プロトタイプ (実装完了)

### 初期化
- [x] 要件定義書の作成 (フェーズ0追加)
- [x] 実装計画書の作成
- [x] プロジェクトディレクトリ構成の作成

### インフラストラクチャ (Terraform)
- [x] [main.tf](file:///c:/Users/yutah/github/space-kuma/terraform/main.tf) の修正 (Google Batch削除, Cloud Run Jobsへ変更)
- [ ] `terraform init` & `apply` (開発環境) (無料枠内想定)
- [ ] Firestore インデックス設定

### データ取得 (Data Ingest - Mock)
- [x] モックデータローダー実装 (`cloud_run/data_ingest_job`) (無料)
    - Tellus APIの代わりにローカル/GCSのサンプル画像を読み込む
- [x] GeoTIFF 保存ロジック実装 (GCS) (無料枠内)
- [x] Cloud Scheduler 設定 (10分間隔) (無料枠内)

### 一次検知 (Detection - Mock/CPU)
- [x] 簡易検知ロジック実装 (Cloud Run Jobs) (無料枠内)
    - GPU/AIモデルは使用せず、画像プロパティ比較やランダム判定で代用
- [x] 結果保存ロジック実装 (Firestore) (無料枠内)
- [x] Dockerコンテナビルド & Artifact Registry プッシュ (無料枠内)

### 通知機能 (Notification - LINE Bot)
- [x] LINE Messaging API 連携実装
- [x] 通知メッセージフォーマット作成 (位置情報, Google Mapsリンク)
- [x] Cloud Run Service デプロイ (無料枠内)

### 簡易ダッシュボード (Simple UI)
- [x] Firestore データ取得ロジック実装 (無料枠内)
- [x] Streamlit UI 実装 (検知リスト表示)
- [x] Cloud Run Service デプロイ (無料枠内)

### ドキュメント
- [x] README.md 更新
- [x] SETUP.md 作成（詳細セットアップガイド）
- [x] .gitignore 作成
- [x] deploy.sh 作成

### 統合テスト (Phase 0)
- [ ] エンドツーエンドテスト (モックデータ -> 簡易検知 -> 通知)
- [ ] verification_plan.md の手動確認項目を実施

-----

## フェーズ1: MVP開発 (将来: 課金あり)
*※以下はプロトタイプ検証後に実施*

- [ ] Tellus API 本実装 (データ取得)
- [ ] Google Batch (GPU) 環境構築
- [ ] SAR-ChangeNet v2 モデル実装
- [ ] 本番用インフラデプロイ

## フェーズ2: 本番運用拡張 (将来: 高額)
- [ ] 高解像度画像発注ロジック
- [ ] 詳細解析モデル実装
