# EasyNovelAssistant

小説生成支援ツール

## 機能

- LLMを使用した文章生成
- BERT-VITS2を使用した音声生成
- 動画生成

## 必要要件

- Python 3.10以上
- KoboldCpp
- BERT-VITS2（オプション）
- FFmpeg（オプション）

## セットアップ

1. リポジトリをクローン
```bash
git clone https://github.com/zapabob/EasyNovelAssistant.git
cd EasyNovelAssistant
```

2. 仮想環境を作成してアクティベート
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

4. KoboldCppをセットアップ
- [KoboldCpp](https://github.com/LostRuins/koboldcpp)をダウンロード
- `setup/koboldcpp`ディレクトリに配置

5. BERT-VITS2をセットアップ（オプション）
- [BERT-VITS2](https://github.com/fishaudio/Bert-VITS2)をダウンロード
- `setup/bert-vits2`ディレクトリに配置

## 使用方法

1. アプリケーションを起動
```bash
python src/easy_novel_assistant.py
```

2. モデルメニューからLLMを選択してダウンロード

3. 入力エリアにプロンプトを入力して生成開始

## ライセンス

MIT License 