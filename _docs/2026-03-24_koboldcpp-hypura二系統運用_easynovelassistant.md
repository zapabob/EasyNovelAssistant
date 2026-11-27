# 2026-03-24 KoboldCpp/Hypura 二系統運用

## 方針

- EasyNovelAssistant は KoboldCpp 実サーバーへ接続
- OpenClaw は Hypura (Ollama互換 API) へ接続
- 推論経路を分離し、相互影響を減らす

## 反映内容

### 1) EasyNovelAssistant を KoboldCpp 直結へ固定

対象: `config.json`

- `llm_backend = "koboldcpp"`
- `koboldcpp_host = "127.0.0.1"`
- `koboldcpp_port = 5001`
- `llm_name = "[直接選択] Qwen3.5-27B-Uncensored-HauhauCS-Aggressive-Q4_K_M"`

### 2) KoboldCpp 先行起動ランチャーを追加

対象: `Run-EasyNovelAssistant-KoboldCpp.bat` (新規)

- `GET http://127.0.0.1:5001/api/v1/model` で KoboldCpp 疎通確認
- 到達可能なら `Run-EasyNovelAssistant.bat` を起動

### 3) Hypuraプロキシ導線は補助運用へ

対象: `Run-EasyNovelAssistant-HypuraProxy.bat`

- 先頭メッセージに「Optional launcher」を明記
- 標準運用が実KoboldCppであることを表示

## 検証結果

2026-03-24 実施:

- `GET http://127.0.0.1:5001/api/v1/model` -> 成功
  - 返却: `Qwen3.5-27B-Uncensored-HauhauCS-Aggressive`
- `POST http://127.0.0.1:5001/api/v1/generate` -> 成功
  - 短文生成を確認
- `GET http://127.0.0.1:8080/api/tags` -> 成功
- `POST http://127.0.0.1:8080/api/generate` -> 成功

## 通常手順

1. KoboldCpp を起動してモデルをロード
2. `Run-EasyNovelAssistant-KoboldCpp.bat` を起動
3. OpenClaw は従来どおり Hypura 8080 を参照

## 障害切り分け

1. EasyNovelAssistant が繋がらない
   - `http://127.0.0.1:5001/api/v1/model` を確認
2. OpenClaw が繋がらない
   - `http://127.0.0.1:8080/api/tags` を確認
3. モデル名が期待と違う
   - Kobold と Hypura で返却モデル名を個別確認
4. 生成が重い
   - `max_length` を下げてトークン予算を絞る
