# Space Guardian 要件定義書（GCP版・改訂v2）

**衛星画像AI解析による緊急事態検知システム（GEE不使用・フェーズ分割対応）**

-----

## 1. プロジェクト概要

### 1.1 プロジェクト名

Space Guardian – 北摂・丹波篠山エリア広域監視システム

### 1.2 プロジェクト目的

広域エリアの衛星画像（SAR）を定期取得し、AIによる変化検知で「倒れている人」等の異常候補を特定。LINEを通じて即座に管理者へ通知し、現場確認を促すことで救助活動を支援する。

### 1.3 対象エリア（変更）

  * **大阪府 北摂エリア**（豊中市、吹田市、高槻市、茨木市、箕面市 等）
  * **兵庫県 丹波篠山市**
  * *合計面積：約 1,000 km² 規模（山間部・都市部混合）*

### 1.4 開発フェーズ定義

  * **フェーズ0（無料プロトタイプ・モックアップ）**
      * **目的**: 完全無料（GCP無料枠内）でシステム全体の動作フローを確認する。
      * **データ**: 衛星データAPIは使用せず、事前に用意したサンプル画像（GeoTIFF）を使用。
      * **検知**: GPU/AIは使用せず、Cloud Run (CPU) 上で簡易的な画像差分またはランダム検知を行う。
      * **通知**: LINE通知の疎通確認を行う。
  * **フェーズ1（実証実験・MVP）**
      * 衛星データ取得と一次検知（SAR）のみ実装。
      * 検知結果をLINE公式アカウントへ即時通知。
      * 現場確認は人間が行う（高解像度撮影・詳細解析はなし）。
      * UIはログ確認用の簡易リストのみ。
  * **フェーズ2（機能拡張・本稼働）**
      * 検知地点の高解像度画像（Maxar/Capella）自動発注機能を追加。
      * 詳細AI解析（姿勢推定）による誤検知フィルタリング。
      * リアルタイムマップを備えた統合ダッシュボードの実装。

### 1.5 前提条件・制約

  * **クラウド**: Google Cloud Platform (GCP) 東京リージョン
  * **予算**: インフラ費用 月額約5万円以内（※フェーズ2の画像購入費は別枠）
  * **衛星データ**: Tellus API（無料枠/定額枠活用）
  * **最適化**: Google Batch, Spot VM, Cloud Run Jobs を積極活用

-----

## 2. システムアーキテクチャ（GCP最適化版）

### 2.1 全体構成図（フェーズ1）

```mermaid
graph TD
    Scheduler((Cloud Scheduler)) -->|10分毎| Ingest[Cloud Run Jobs: Data Ingest]
    Ingest -->|Tellus API| SatData(衛星データ取得)
    Ingest -->|GeoTIFF| GCS_Raw[(GCS: Raw Data)]
    Ingest -->|Trigger| Batch[Google Batch]
    
    subgraph Compute Resources (Spot VMs)
    Batch -->|Pull Container| AR[Artifact Registry]
    Batch -->|Execute| GPU_Node[Compute Engine T4 GPU]
    GPU_Node -->|Preprocessing| Pre[前処理: GDAL/CuPy]
    Pre -->|Inference| Model[一次検知: SAR-ChangeNet v2]
    end
    
    Model -->|Result JSON| Firestore[(Firestore)]
    Model -->|Detection > 0.8| Notifier[Cloud Run: LINE Bot]
    Notifier -->|Message| LINE_API((LINE Messaging API))
    
    User((管理者)) <-- LINE通知 --- LINE_API
    User -->|閲覧| Web[Cloud Run: 簡易管理画面]
```

-----

## 3. 機能要件：フェーズ1（MVP）

### 3.1 データ取得・管理（Ingest & Storage）

  * **FR-101: 衛星データ定期取得**
      * **基盤**: Cloud Run Jobs（タイムアウト耐性とリトライ管理のため採用）
      * **トリガー**: Cloud Scheduler（10分間隔）
      * **対象**: QPS-SAR / ALOS-4（Tellus API経由）
      * **範囲**: 指定エリアの最新タイルのみ取得
  * **FR-102: コスト最適化ストレージ**
      * **保存先**: Cloud Storage (GCS)
      * **ライフサイクル**: `raw`データは7日後に自動削除、`result`（検知あり）は90日保存。

### 3.2 一次検知（Detection Phase 1）

  * **FR-103: バッチ推論実行**
      * **基盤**: **Google Batch**
      * **構成**: Spot VM (n1-standard-4 + NVIDIA T4) を自動プロビジョニング。
      * **動作**: ジョブ投入時のみVMを確保し、処理完了後即座に破棄（課金停止）。
  * **FR-104: SAR変化検知**
      * **前処理**: GDALによる地形補正、位置合わせ。
      * **モデル**: SAR-ChangeNet v2（軽量版）。
      * **判定**: 変化スコア 0.8 以上を「異常」として検出。

### 3.3 通知機能（Notification）

  * **FR-105: LINE通知**
      * **基盤**: Cloud Run Service (Webhook型)
      * **宛先**: 指定されたLINE公式アカウント（管理者グループ）。
      * **内容**:
          * 検知日時
          * 検知場所（住所逆ジオコーディング結果 ＋ Google Mapsリンク）
          * スコア（確度）
          * *「現場確認をお願いします」* のメッセージ
      * **API**: LINE Messaging API (Push Message)

### 3.4 簡易インターフェース（Simple UI）

  * **FR-106: 検知ログリスト**
      * **基盤**: Cloud Run + Streamlit（または単純なHTML）
      * **機能**: 直近24時間の検知履歴をリスト表示するのみ。
      * **認証**: Basic認証 または IAP (Identity-Aware Proxy)

-----

## 4. 機能要件：フェーズ2（本番運用拡張）

*※フェーズ1完了後に実装*

### 4.1 詳細解析連携（Tasking & Phase 2）

  * **FR-201: 高解像度画像自動発注**
      * 検知スコアが高い地点に対し、Maxar/CapellaのAPIを叩き撮影予約（Tasking）を行う。
      * *注: 別途画像購入予算が必要。*
  * **FR-202: 二次判定（詳細解析）**
      * 高解像度画像に対し、姿勢推定モデル（HRNet等）を適用。
      * 「人（臥位）」か「誤検知（看板、車両等）」かを分類。

### 4.2 統合ダッシュボード

  * **FR-203: リアルタイムマップUI**
      * Firebase Hosting + React + Mapbox GL。
      * 検知地点のヒートマップ表示、ステータス管理（未確認→確認中→完了）。

-----

## 5. 非機能要件（共通）

### 5.1 性能・拡張性

  * **処理時間**: 画像取得から通知まで **30分以内**（Spot VMの起動待ち時間を含む）。
  * **エリア拡張**: 設定ファイル（GeoJSON）の更新のみで北摂・丹波篠山以外の追加も可能にする。

### 5.2 コスト最適化・可用性

  * **Spot VM利用率**: 100%を目指す。確保失敗時のみStandard VMにフォールバックする設定をGoogle Batchに入れる。
  * **予算管理**: GCP予算アラートを設定し、月額4万円を超えた時点でLINEに警告を飛ばす。

-----

## 6. GCPインフラ構成とコスト試算（フェーズ1）

**前提**: 月間720時間稼働ではなく、バッチ処理の実働時間のみ課金。

| コンポーネント | スペック / 設定 | 概算コスト (月額) | 備考 |
| :--- | :--- | :--- | :--- |
| **Compute Engine** | **Google Batch管理**<br>n1-standard-4 + T4 GPU<br>**Spot VM適用** | **約 ¥15,000** | 1回10分処理×1日144回<br>Spot価格($0.11/h)で試算 |
| **Cloud Run** | Jobs (Ingest) + Service (LINE/UI)<br>CPU 1, Memory 512MB | **約 ¥2,000** | リクエスト数ベース。<br>無料枠適用範囲内が多い。 |
| **Cloud Storage** | Standardクラス<br>保存量 200GB想定 | **約 ¥500** | ライフサイクル設定で<br>古いデータを削除し節約。 |
| **Firestore** | ドキュメント読み書き | **約 ¥1,000** | 簡易UIのためアクセス頻度低。 |
| **Network** | 外向き通信 (Egress) | **約 ¥2,000** | 画像データ転送量による。 |
| **その他** | Container Registry, Logging | **¥1,000** | |
| **合計** | | **約 ¥21,500** | **予算(5万円)に対し余裕あり** |

  * *注: Tellus等の衛星データAPI利用料は別途（無料枠または定額契約）。*
  * *注: フェーズ2で高解像度画像を購入する場合は、1枚あたり数万円〜が別途加算されます。*

-----

## 7. ディレクトリ構成案

```text
/space-guardian-v2/
│
├ .github/workflows/     # CI/CD: Cloud Build連携
│
├ batch_jobs/            # Google Batch用コード
│   ├ detection_job/
│   │   ├ Dockerfile
│   │   ├ main.py        # 前処理〜推論ロジック
│   │   └ requirements.txt
│
├ cloud_run/
│   ├ data_ingest_job/   # データ取得 (Cloud Run Jobs)
│   ├ line_bot/          # 通知機能 (FastAPI)
│   └ simple_dashboard/  # 簡易UI (Streamlit)
│
├ terraform/             # インフラコード化 (IaC)
│   ├ main.tf
│   └ variables.tf
│
└ configs/
    └ target_areas.json  # 北摂・丹波篠山の座標定義
```

-----

## 8. リスクと対策

| リスク | 影響度 | 対策 |
| :--- | :--- | :--- |
| **Spot VMが確保できない** | 中 | Google Batchのフォールバック機能で通常VMを使用（一時的コスト増を許容）。 |
| **山間部の誤検知** | 高 | 丹波篠山エリアは植生変化が多いため、季節ごとのマスク処理を強化。フェーズ1では「人が確認する」ことでカバー。 |
| **LINE通知の到達率** | 低 | 公式アカウントのプッシュメッセージ枠（無料/有料）に注意。通知過多の場合は重要度フィルタを導入。 |

-----

## 9. 承認

  * **プロジェクトオーナー**: ____________________
  * **開発責任者**: ____________________
  * **日付**: 2025年12月3日
