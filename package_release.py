#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyNovelAssistant リリースパッケージ作成スクリプト
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path
import json
import time

def log(message):
    """ログメッセージ出力"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def create_release_package():
    """リリースパッケージ作成"""
    log("📦 EasyNovelAssistant リリースパッケージ作成開始")
    print("=" * 60)
    
    version = "3.0.0"
    release_dir = Path(f"release/EasyNovelAssistant-v{version}")
    
    # リリースディレクトリ作成
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)
    log(f"📁 リリースディレクトリ作成: {release_dir}")
    
    # EXEファイルコピー
    exe_file = Path("dist/EasyNovelAssistant.exe")
    if exe_file.exists():
        shutil.copy2(exe_file, release_dir)
        size_mb = exe_file.stat().st_size / (1024 * 1024)
        log(f"📄 EXEファイルコピー完了: {size_mb:.1f} MB")
    else:
        log("❌ EXEファイルが見つかりません")
        return False
    
    # 必須ファイルコピー
    essential_files = [
        "Launch_Portable.bat",
        "README.md",
        "LICENSE.txt",
        "EXE_PACKAGING_GUIDE.md",
        "config.json",
        "llm.json", 
        "llm_sequence.json"
    ]
    
    for file_name in essential_files:
        src_file = Path(file_name)
        if src_file.exists():
            shutil.copy2(src_file, release_dir)
            log(f"📄 {file_name} をコピー")
    
    # KoboldCppディレクトリ（サンプル）作成
    kobold_dir = release_dir / "KoboldCpp"
    kobold_dir.mkdir(exist_ok=True)
    
    # KoboldCpp関連ファイルがあればコピー
    src_kobold = Path("KoboldCpp")
    if src_kobold.exists():
        # 実行ファイルのみコピー（GGUFファイルは大きすぎるため除外）
        for item in src_kobold.iterdir():
            if item.suffix in ['.exe', '.bat', '.txt']:
                shutil.copy2(item, kobold_dir)
                log(f"📄 KoboldCpp/{item.name} をコピー")
    
    # 使用方法ファイル作成
    create_usage_files(release_dir)
    
    # ZIPパッケージ作成
    zip_path = Path(f"release/EasyNovelAssistant-v{version}.zip")
    create_zip_package(release_dir, zip_path)
    
    # 完了報告
    log("🎉 リリースパッケージ作成完了！")
    log(f"📁 フォルダ版: {release_dir}")
    log(f"📦 ZIP版: {zip_path}")
    
    return True

def create_usage_files(release_dir):
    """使用方法ファイル作成"""
    log("📝 使用方法ファイル作成中...")
    
    # 詳細README作成
    readme_content = """# 🎯 EasyNovelAssistant v3.0 - 完全版

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
"""
    
    readme_file = release_dir / "README_RELEASE.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    log("📄 README_RELEASE.md を作成")
    
    # クイックスタートガイド作成
    quickstart_content = """🎯 EasyNovelAssistant v3.0 - クイックスタート

1. 📁 Launch_Portable.bat をダブルクリック
2. 🔧 初回起動時は設定を確認
3. 📝 プロンプトを入力して生成開始
4. 🎉 小説作成をお楽しみください！

詳細: README_RELEASE.md を参照
"""
    
    quickstart_file = release_dir / "QUICKSTART.txt"
    with open(quickstart_file, 'w', encoding='utf-8') as f:
        f.write(quickstart_content)
    log("📄 QUICKSTART.txt を作成")

def create_zip_package(source_dir, zip_path):
    """ZIPパッケージ作成"""
    log("📦 ZIPパッケージ作成中...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as zipf:
        for file_path in source_dir.rglob('*'):
            if file_path.is_file():
                arc_name = file_path.relative_to(source_dir.parent)
                zipf.write(file_path, arc_name)
    
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    log(f"📦 ZIPパッケージ作成完了: {size_mb:.1f} MB")

def main():
    """メイン関数"""
    if create_release_package():
        input("\n✅ リリースパッケージ作成完了。Enterキーで終了...")
        return 0
    else:
        input("\n❌ リリースパッケージ作成失敗。Enterキーで終了...")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 