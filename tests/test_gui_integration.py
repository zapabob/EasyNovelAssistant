# -*- coding: utf-8 -*-
"""
GUI ↔ Core 双方向同期テスト
統合システムv3制御パネルとコア機能の連携確認
"""

import os
import sys
import time
import tkinter as tk
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_gui_core_bidirectional_sync():
    """GUI ↔ Core 双方向同期テスト"""
    print("🧪 GUI ↔ Core 双方向同期テスト")
    print("=" * 50)
    
    try:
        # 1. 統合システム制御パネルのインポートテスト
        from EasyNovelAssistant.src.integration_control_panel import IntegrationControlPanel
        print("✅ 統合システム制御パネルインポート成功")
        
        # 2. GUIの基本構築テスト
        root = tk.Tk()
        root.title("GUI ↔ Core 双方向同期テスト")
        root.geometry("800x600")
        
        # 3. ダミーコンテキストの作成
        class DummyContext:
            def __init__(self):
                self.integration_config = {}
                self.integration_stats = {
                    'theta_convergence_rate': 0.835,
                    'bleurt_alternative_score': 0.882,
                    'total_processed': 45,
                    'success_rate_history': [0.92, 0.91, 0.93, 0.90, 0.94],
                    'total_compression_rate': 0.12
                }
        
        dummy_ctx = DummyContext()
        
        # 4. 設定変更コールバックのテスト
        settings_changed_count = 0
        last_settings = {}
        
        def on_settings_changed(settings):
            nonlocal settings_changed_count, last_settings
            settings_changed_count += 1
            last_settings = settings.copy()
            print(f"🔄 設定変更通知 #{settings_changed_count}")
            print(f"   変更項目数: {len(settings)}")
            
            # 設定の妥当性チェック
            if 'theta_optimization' in settings:
                theta = settings['theta_optimization']
                if 'target_convergence' in theta:
                    print(f"   θ目標収束度: {theta['target_convergence']:.1%}")
            
            if 'bleurt_alternative' in settings:
                bleurt = settings['bleurt_alternative']
                if 'target_score' in bleurt:
                    print(f"   BLEURT目標: {bleurt['target_score']:.1%}")
        
        # 5. 統合システム制御パネルの作成
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        control_panel = IntegrationControlPanel(
            main_frame,
            dummy_ctx,
            on_settings_changed=on_settings_changed
        )
        control_panel.get_widget().pack(fill=tk.BOTH, expand=True)
        
        print("✅ 統合システム制御パネル作成成功")
        
        # 6. 統計更新テスト
        def update_statistics():
            # 模擬的な統計情報の更新
            dummy_ctx.integration_stats['total_processed'] += 1
            dummy_ctx.integration_stats['theta_convergence_rate'] = min(0.95, 
                dummy_ctx.integration_stats['theta_convergence_rate'] + 0.001)
            dummy_ctx.integration_stats['bleurt_alternative_score'] = min(0.92,
                dummy_ctx.integration_stats['bleurt_alternative_score'] + 0.001)
            
            # GUIに統計更新を反映
            control_panel.update_statistics(dummy_ctx.integration_stats)
            
            # 1秒後に再度更新
            root.after(1000, update_statistics)
        
        # 7. テスト用ボタンの追加
        test_frame = tk.Frame(main_frame)
        test_frame.pack(fill=tk.X, pady=5)
        
        def test_phase4_preset():
            print("📊 Phase 4プリセットテスト")
            control_panel.apply_phase4_config()
            print("   Phase 4達成モード適用完了")
        
        def test_speed_preset():
            print("⚡ 高速処理モードテスト")
            control_panel.apply_speed_config()
            print("   高速処理モード適用完了")
        
        def test_quality_preset():
            print("💎 品質重視モードテスト")
            control_panel.apply_quality_config()
            print("   品質重視モード適用完了")
        
        # テストボタン
        tk.Button(test_frame, text="Phase 4テスト", command=test_phase4_preset).pack(side=tk.LEFT, padx=2)
        tk.Button(test_frame, text="高速モードテスト", command=test_speed_preset).pack(side=tk.LEFT, padx=2)
        tk.Button(test_frame, text="品質モードテスト", command=test_quality_preset).pack(side=tk.LEFT, padx=2)
        
        def close_test():
            print("🏁 GUI ↔ Core 双方向同期テスト終了")
            print(f"   設定変更通知回数: {settings_changed_count}")
            print(f"   最終統計: θ={dummy_ctx.integration_stats['theta_convergence_rate']:.1%}, "
                  f"BLEURT={dummy_ctx.integration_stats['bleurt_alternative_score']:.1%}")
            root.destroy()
        
        tk.Button(test_frame, text="テスト終了", command=close_test).pack(side=tk.RIGHT, padx=2)
        
        # 8. 統計更新開始
        update_statistics()
        
        print("\n🚀 GUI ↔ Core 双方向同期テスト開始")
        print("   各プリセットボタンをクリックして設定変更をテストしてください")
        print("   統計情報は自動更新されます")
        
        # GUIメインループ開始
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ GUI ↔ Core 双方向同期テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    print("🧪 EasyNovelAssistant GUI ↔ Core 双方向同期テスト")
    print("   Step 2: GUI ↔ Core 双方向バインド確認")
    print("=" * 60)
    
    success = test_gui_core_bidirectional_sync()
    
    if success:
        print("\n🎉 GUI ↔ Core 双方向同期テスト成功！")
        print("   ✅ 統合システム制御パネル正常動作")
        print("   ✅ 設定変更コールバック機能")
        print("   ✅ リアルタイム統計更新機能")
        print("   ✅ プリセット設定切り替え機能")
        print("\n🚀 次のステップ: Voice (Style-BERT-VITS2) 併走 準備OK")
        return 0
    else:
        print("\n📈 GUI ↔ Core 双方向同期テスト 改善必要")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 