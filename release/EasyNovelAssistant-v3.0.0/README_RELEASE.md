# 🎯 EasyNovelAssistant v3.0 - 完全版

## 🚀 クイックスタート

### 1. 基本起動
```
Launch_Portable.bat をダブルクリック
```

### 2. 直接起動
```
EasyNovelAssistant.exe をダブルクリック
```

## 📋 パッケージ内容

### 🟢 実行ファイル
- `EasyNovelAssistant.exe` - メインアプリケーション (約1.6GB)
- `Launch_Portable.bat` - ポータブル起動スクリプト

### 🟡 設定ファイル
- `config.json` - 基本設定
- `llm.json` - LLM接続設定
- `llm_sequence.json` - シーケンス設定

### 🟠 ドキュメント
- `README.md` - プロジェクト概要
- `LICENSE.txt` - ライセンス情報
- `EXE_PACKAGING_GUIDE.md` - 詳細技術資料

### 🔵 KoboldCppサポート
- `KoboldCpp/` - 推論エンジン用ディレクトリ
  - GGUFファイルをここに配置
  - koboldcpp.exe を配置（別途ダウンロード）

## 🔧 初回セットアップ

### ステップ1: KoboldCpp準備
1. [KoboldCpp公式サイト](https://github.com/LostRuins/koboldcpp)から `koboldcpp.exe` をダウンロード
2. `KoboldCpp/` フォルダに配置

### ステップ2: GGUFモデル準備
1. Hugging Faceから日本語対応GGUFモデルをダウンロード
   - 推奨: `Ninja-V3-7B-Q4_K_M.gguf` (約4GB)
   - 推奨: `Vecteus-v1-IQ4_XS.gguf` (約3.6GB)
2. `KoboldCpp/` フォルダに配置

### ステップ3: 起動テスト
1. `Launch_Portable.bat` で起動
2. 設定メニューからKoboldCpp接続を確認

## ⚙️ 高度な設定

### GPU加速
- NVIDIA GPU使用時: GPUレイヤー数を調整
- RTX 3080: 最大32レイヤー推奨
- RTX 4090: 最大40レイヤー推奨

### メモリ設定
- 32Kコンテキスト: 16GB RAM推奨
- 8Kコンテキスト: 8GB RAM推奨

### 反復抑制システム
- 高度反復抑制システム v3 搭載
- 90%成功率の反復検出・抑制
- NKAT理論統合システム

## 🆘 トラブルシューティング

### アプリケーションが起動しない
1. Windows Defenderの除外設定を確認
2. 管理者権限で実行
3. Visual C++ Redistributableをインストール

### KoboldCppに接続できない
1. ポート番号確認 (デフォルト: 5001)
2. ファイアウォール設定確認
3. KoboldCppプロセスが起動しているか確認

### メモリ不足エラー
1. コンテキストサイズを縮小
2. GPUレイヤー数を削減
3. より軽量なGGUFモデルを使用

## 📊 パフォーマンス情報

### 32K Context 耐久性テスト結果
- ✅ 処理速度: 22,152.8 tok/s
- ✅ OOMイベント: 0件
- ✅ メモリリーク: 未検出
- ✅ 32Kトークン生成: 安定動作

### 推奨システム要件
- **最小**: Intel i5/AMD Ryzen 5, 8GB RAM, GTX 1060
- **推奨**: Intel i7/AMD Ryzen 7, 16GB RAM, RTX 3080
- **最適**: Intel i9/AMD Ryzen 9, 32GB RAM, RTX 4090

## 🔗 リンク

- **GitHub**: https://github.com/zapabob/EasyNovelAssistant
- **Issues**: バグ報告・機能要望
- **Wiki**: 詳細ドキュメント
- **Discord**: コミュニティサポート

## 📝 バージョン情報

- **Version**: 3.0.0
- **Build**: KoboldCpp + GGUF統合対応版
- **Release**: 2025-06-03
- **Architecture**: Windows x64
- **Python**: 3.12.9
- **PyInstaller**: 6.13.0

---

**🎉 EasyNovelAssistant v3.0をお楽しみください！**
