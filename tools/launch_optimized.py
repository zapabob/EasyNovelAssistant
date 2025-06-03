# -*- coding: utf-8 -*-
"""
EasyNovelAssistant 最適化起動スクリプト
RTX 3080環境での性能最適化とNKAT文章一貫性向上機能を統合
"""

import os
import sys
import json

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_nkat_availability():
    """NKAT統合モジュールの可用性チェック"""
    try:
        from nkat.nkat_integration import NKATIntegration
        return True
    except ImportError:
        return False

def setup_nkat_config():
    """NKAT設定の確認と初期化"""
    config_path = "config.json"
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
        
        # NKAT設定が不足している場合の追加
        nkat_defaults = {
            "nkat_enabled": True,
            "nkat_consistency_mode": True,
            "nkat_stability_factor": 0.8,
            "nkat_context_memory": 3,
            "nkat_smoothing_enabled": True,
            "nkat_cache_size": 500,
            "nkat_async_processing": True
        }
        
        updated = False
        for key, value in nkat_defaults.items():
            if key not in config:
                config[key] = value
                updated = True
        
        if updated:
            with open(config_path, 'w', encoding='utf-8-sig') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print("NKAT設定を追加しました")
        
        return config.get("nkat_enabled", False)
        
    except Exception as e:
        print(f"設定ファイル処理エラー: {e}")
        return False

# メイン実行
if __name__ == "__main__":
    try:
        print("EasyNovelAssistant起動中（最適化版）...")
        
        # NKAT可用性チェック
        nkat_available = check_nkat_availability()
        nkat_enabled = setup_nkat_config()
        
        if nkat_available and nkat_enabled:
            print("NKAT文章一貫性向上機能: 有効")
        else:
            print("NKAT文章一貫性向上機能: 無効（設定またはモジュール不可）")
        
        # 最適化モジュール読み込み
        try:
            from nkat.optimize_config import RTX3080Optimizer
            
            # RTX 3080最適化適用
            optimizer = RTX3080Optimizer()
            optimization_result = optimizer.optimize_for_rtx3080()
            print(f"RTX 3080最適化完了: {optimization_result['expected_performance']['estimated_tokens_per_sec']} tokens/sec 予想")
            
        except ImportError:
            print("RTX 3080最適化モジュールが見つかりません。標準設定で継続します。")
        
        # 従来のメイン処理
        from easy_novel_assistant import EasyNovelAssistant
        
        print("アプリケーション初期化中...")
        app = EasyNovelAssistant()
        
        # NKAT統合状況の確認
        if nkat_available and nkat_enabled:
            if hasattr(app.ctx, 'nkat'):
                stats = app.get_nkat_stats()
                print(f"NKAT統合状況: {stats['nkat_enabled']}")
                if stats.get('consistency_mode'):
                    print("一貫性モード: 有効")
        
        print("EasyNovelAssistant起動完了")
        app.run()
        
    except Exception as e:
        print(f"起動エラー: {e}")
        print("従来の起動方法にフォールバック...")
        
        # フォールバック起動
        try:
            from easy_novel_assistant import EasyNovelAssistant
            app = EasyNovelAssistant()
            app.run()
        except Exception as fallback_error:
            print(f"フォールバック起動もエラー: {fallback_error}")
            input("Enterキーで終了...")
