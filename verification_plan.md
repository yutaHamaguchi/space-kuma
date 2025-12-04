# Space Guardian 検証計画書 (フェーズ0: 無料プロトタイプ)

## 1. 自動テスト計画

### 1.1 ユニットテスト (Unit Tests)
- **Data Ingest (Mock)**:
    - サンプル画像ファイルが正しく読み込まれ、GCSに配置されるか。
- **Detection (Simple)**:
    - 簡易ロジック（例: ファイルサイズや特定ピクセル値のチェック）が、意図した「検知/非検知」判定を返すか。
- **Notification**:
    - LINE API へのリクエスト形式が正しいか。

### 1.2 統合テスト (Integration Tests)
- **Mock Flow**:
    - Scheduler起動 -> モックデータ配置 -> 検知ジョブ起動 -> (検知時) LINE通知
    - この一連の流れがエラーなく完走することを確認。

-----

## 2. 手動確認項目 (Manual Verification Checklist)

### 2.1 インフラ構築確認 (無料枠構成)
- [ ] **GCPコンソール**: Cloud Run Jobs (Ingest, Detection), Firestore, GCS が作成されていること。
- [ ] **Google Batch**: *フェーズ0では作成されていないこと*（コスト回避）。

### 2.2 データ取得機能 (Mock Ingest)
- [ ] **動作確認**: ジョブを実行すると、GCSの `raw-data` バケットにサンプル画像が保存されること。

### 2.3 検知機能 (Simple Detection)
- [ ] **動作確認**: Cloud Run Jobs (Detection) が起動し、正常終了すること。
- [ ] **Firestore**: `detections` コレクションにテストデータが記録されること。

### 2.4 通知機能 (Notification)
- [ ] **LINE**: 管理者のLINEアプリに「テスト検知」の通知が届くこと。
- [ ] **リンク確認**: 通知内のGoogle Mapsリンクが正しく開くこと。

### 2.5 ダッシュボード (Dashboard)
- [ ] **表示確認**: ダッシュボードにアクセスし、Firestoreに記録されたテスト検知データが表示されること。

-----

## 3. 制限事項確認
- [ ] **課金回避**: 高価なリソース（GPU, Batch, External APIs）が使用されていないことをコードレベルで確認。
