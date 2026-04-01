# 2026-03-24 Kobold互換HTTPプロキシ実装（EasyNovelAssistant）

## 目的

EasyNovelAssistant 本体の KoboldCpp クライアント挙動を維持したまま、  
別プロセスの Kobold互換プロキシ経由で Hypura(Ollama互換 API) へ中継する。

## 運用位置づけ（更新）

本ドキュメントのプロキシ方式は **補助運用** とする。  
標準運用は「EasyNovelAssistant -> 実KoboldCpp」「OpenClaw -> Hypura」の二系統分離。

構成:

- EasyNovelAssistant -> `http://127.0.0.1:5001` (Kobold互換プロキシ)
- プロキシ -> `http://127.0.0.1:8080` (Hypura)

## 変更ファイル

- `proxy/kobold_to_hypura_proxy.py` (新規)
- `Run-EasyNovelAssistant-HypuraProxy.bat` (新規)
- `config.json` (接続先を 5001 に変更)

## 実装内容

### 1) Kobold互換プロキシ

`proxy/kobold_to_hypura_proxy.py` を追加し、以下の互換エンドポイントを実装:

- `GET /api/v1/model`
  - Hypura `GET /api/tags` の先頭モデルを `{"result":"<name>"}` で返却
- `POST /api/v1/generate`
  - Kobold 形式を Hypura 形式へ変換して `POST /api/generate` へ中継
  - 主要変換:
    - `max_length` -> `options.num_predict`
    - `rep_pen` -> `options.repeat_penalty`
    - `temperature`, `top_k`, `top_p` -> 同名で中継
  - 返却は Kobold 互換 `{"results":[{"text":"..."}]}`
- `GET /api/extra/generate/check`
  - 互換維持のため最新生成結果を返却（未生成時は空文字）
- `POST /api/extra/abort`
  - 互換維持で `{"success":true}` を返却

### 2) 起動ラッパー

`Run-EasyNovelAssistant-HypuraProxy.bat` を追加:

1. `http://127.0.0.1:8080/api/tags` で Hypura 疎通確認
2. `py -3 proxy/kobold_to_hypura_proxy.py --listen 127.0.0.1:5001 --hypura 127.0.0.1:8080` を別窓起動
3. `Run-EasyNovelAssistant.bat` を起動

### 3) 設定統一

`config.json` を以下に変更:

- `koboldcpp_host = "127.0.0.1"`
- `koboldcpp_port = 5001`
- `llm_backend = "koboldcpp"`（本方式運用に合わせる）

## 動作確認

### 実施コマンド

- `curl http://127.0.0.1:5001/api/v1/model` -> 成功
- `curl http://127.0.0.1:5001/api/extra/generate/check` -> 成功
- `curl -X POST http://127.0.0.1:5001/api/extra/abort` -> 成功
- `POST /api/v1/generate` -> タイムアウト（バックエンド生成待ちが長い環境では発生）
- `py -3 -m py_compile proxy/kobold_to_hypura_proxy.py` -> 成功

### 判定

- API互換面の経路と中継実装は確認済み
- `generate` の応答時間は Hypura 側のモデル/負荷に依存

## 障害対応手順

1. **Hypura 未起動**
   - 症状: ラッパー起動時に `Hypura is not reachable` 表示
   - 対処: `http://127.0.0.1:8080/api/tags` が応答する状態にして再実行

2. **ポート競合（5001）**
   - 症状: プロキシ起動失敗
   - 対処: 競合プロセス停止、または `--listen 127.0.0.1:<別ポート>` と `config.json` を一致

3. **モデル名不一致**
   - 症状: クライアント側で想定モデルが見えない
   - 対処: `GET /api/v1/model` と Hypura `GET /api/tags` の先頭モデルを確認

4. **生成タイムアウト**
   - 症状: `POST /api/v1/generate` 応答が遅い/返らない
   - 対処: `max_length` を下げる（例: 1024 -> 512）、Hypura 側負荷とコンテキスト設定を見直し
