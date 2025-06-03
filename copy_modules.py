#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyNovelAssistant モジュールコピースクリプト
必要なモジュールをプロジェクトルートにコピーしてEXE実行時の依存関係エラーを解決
"""

import shutil
import os
from pathlib import Path

def copy_module(source_path, target_name=None):
    """モジュールをプロジェクトルートにコピー"""
    source = Path(source_path)
    if not source.exists():
        print(f"❌ {source} が見つかりません")
        return False
    
    target_name = target_name or source.name
    target = Path(target_name)
    
    try:
        if target.exists():
            print(f"⚠️ {target_name} は既に存在します（スキップ）")
            return True
        
        shutil.copy2(source, target)
        print(f"✅ {source} → {target_name}")
        return True
    except Exception as e:
        print(f"❌ {source} のコピーに失敗: {e}")
        return False

def main():
    print("📁 EasyNovelAssistant モジュールコピー開始")
    print("=" * 50)
    
    # 必要なモジュールのマッピング
    modules_to_copy = [
        ("EasyNovelAssistant/src/path.py", "path.py"),
        ("EasyNovelAssistant/src/form.py", "form.py"),
        ("EasyNovelAssistant/src/generator.py", "generator.py"),
        ("EasyNovelAssistant/src/kobold_cpp.py", "kobold_cpp.py"),
        ("EasyNovelAssistant/src/movie_maker.py", "movie_maker.py"),
        ("EasyNovelAssistant/src/style_bert_vits2.py", "style_bert_vits2.py"),
    ]
    
    success_count = 0
    total_count = len(modules_to_copy)
    
    for source_path, target_name in modules_to_copy:
        if copy_module(source_path, target_name):
            success_count += 1
    
    print("=" * 50)
    print(f"📊 コピー結果: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        print("✅ すべてのモジュールが正常にコピーされました")
        print("💡 これでEXE実行時の依存関係エラーが解決されるはずです")
    else:
        print("⚠️ 一部のモジュールコピーが失敗しました")
        print("💡 エラーが発生したモジュールを手動で確認してください")

if __name__ == "__main__":
    main() 