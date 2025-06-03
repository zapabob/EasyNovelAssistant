# EasyNovelAssistant v3.0.4 リリースノート

## 📌 リリース概要
- **バージョン**: v3.0.4
- **リリース日**: 2025年06月03日
- **ビルドタイプ**: 安定版 (Stable)

## 🔧 主要な修正内容

### PyInstaller EXE化の改善
- **scipy依存関係の問題を解決**: EXE実行時の `ModuleNotFoundError: No module named 'scipy'` エラーを修正
- **dependencyの完全収集**: PyInstallerの`collect_data_files`と`collect_submodules`を使用してscipyの完全な依存関係を収集
- **hiddenimportsの強化**: scipy関連のすべてのサブモジュールを明示的に指定

### ビルド仕様の最適化
- **.specファイルの改良**: `easy_novel_assistant.spec`を更新してより包括的な依存関係管理を実装
- **エンコーディング対応の強化**: 日本語環境での安定動作を確保
- **不要なモジュールの除外**: matplotlib、PyQtなどの不要な大容量モジュールを除外してサイズ最適化

## 🎯 技術仕様

### ファイルサイズ
- **EXEファイルサイズ**: 約2.2GB
- **含まれる主要ライブラリ**: 
  - PyTorch + CUDA (1.5GB程度)
  - scipy + numpy 科学計算ライブラリ
  - 音声処理ライブラリ (librosa, soundfile)
  - 自然言語処理ライブラリ (transformers, fugashi)

### 動作環境
- **OS**: Windows 10/11 (64bit)
- **GPU**: CUDA対応 (RTX3080推奨)
- **メモリ**: 8GB以上推奨
- **ストレージ**: 3GB以上の空き容量

## 🚀 新機能・改善

### Style-Bert-VITS2統合
- **scipyなしでの動作**: scipyが利用できない環境でも音声処理をスキップして動作継続
- **エラーハンドリング強化**: 音声処理失敗時の適切なフォールバック処理

### 統合システムv3対応
- **高度な反復抑制**: PyTorch利用時の高性能テキスト処理
- **LoRA協調システム**: キャラクター別の文体調整
- **クロス抑制エンジン**: セッション間での品質一貫性

## 🔍 テスト状況

### EXE化テスト
- ✅ **ビルド成功**: PyInstaller 6.13.0でのクリーンビルド
- ✅ **起動テスト**: scipyエラーなしでの正常起動確認
- ✅ **プロセス動作**: バックグラウンドでの安定動作確認

### 依存関係テスト
- ✅ **scipy.io.wavfile**: 音声ファイル読み書き正常動作
- ✅ **numpy配列処理**: 科学計算ライブラリ正常動作
- ✅ **tkinter GUI**: ユーザーインターフェース正常表示

## 📁 配布ファイル構成

```
EasyNovelAssistant-v3.0.4/
├── EasyNovelAssistant.exe     (メインアプリケーション)
├── config.json                (基本設定ファイル)
├── llm.json                   (LLM設定ファイル)
├── llm_sequence.json          (シーケンス設定ファイル)
├── setup/                     (セットアップファイル群)
│   ├── res/                   (リソースファイル)
│   └── lib/                   (ライブラリファイル)
├── README.md                  (使用方法ドキュメント)
├── LICENSE.txt                (ライセンス情報)
└── RELEASE_NOTES_v3.0.4.md    (このファイル)
```

## 🛠️ 開発者向け情報

### ビルド手順
```bash
# 1. 依存関係の確認
pip list | findstr scipy

# 2. ビルド環境のクリーンアップ
Remove-Item -Path "build","dist" -Recurse -Force

# 3. PyInstallerでのEXE作成
pyinstaller --clean easy_novel_assistant.spec
```

### デバッグ情報
- **PyTorch CUDA**: v12.8対応
- **MKL最適化**: Intel MKL数学ライブラリ使用
- **メモリ使用量**: 起動時約7-8MB（プロセス監視結果）

## 🔄 前バージョンからの変更点

### v3.0.3 → v3.0.4
- scipyインポートエラーの完全解決
- PyInstallerビルド仕様の大幅改善
- 依存関係管理の自動化
- ファイルサイズの適正化（不要モジュール除外）

## ⚠️ 既知の制限事項

1. **ファイルサイズ**: 2.2GBと大容量（PyTorch+CUDA含有のため）
2. **初回起動**: PyTorchライブラリ読み込みで30-60秒程度の時間
3. **CUDA依存**: GPU処理にはCUDA環境が必要

## 📝 次期バージョン予定

### v3.0.5 (予定)
- EXEファイルサイズの更なる最適化
- 起動時間の短縮
- 設定ファイルの改良

---

**開発者**: EasyNovelAssistant Development Team  
**ビルド環境**: Windows 11 + Python 3.12.9 + PyInstaller 6.13.0  
**テスト完了日**: 2025年06月03日 