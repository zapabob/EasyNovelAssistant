# -*- coding: utf-8 -*-
"""
簡易動作確認テスト v3.0
Phase 2完成システムの基本動作確認
"""

import asyncio
import time
import sys
import os

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, "src")
sys.path.insert(0, src_dir)

def test_system_imports():
    """システムインポートテスト"""
    print("🧪 システムインポートテスト開始")
    
    try:
        from optimization.memory_efficiency_system_v3 import create_memory_efficiency_system
        print("✅ メモリ効率化システム v3.0 インポート成功")
        memory_success = True
    except Exception as e:
        print(f"❌ メモリ効率化システム インポートエラー: {e}")
        memory_success = False
    
    try:
        from integration.realtime_coordination_controller_v3 import create_realtime_coordination_controller
        print("✅ リアルタイム協調制御システム v3.0 インポート成功")
        coordination_success = True
    except Exception as e:
        print(f"❌ 協調制御システム インポートエラー: {e}")
        coordination_success = False
    
    try:
        from nkat.nkat_integration_preparation_v3 import create_nkat_integration_system
        print("✅ NKAT理論統合準備システム v3.0 インポート成功")
        nkat_success = True
    except Exception as e:
        print(f"❌ NKAT統合システム インポートエラー: {e}")
        nkat_success = False
    
    try:
        from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
        print("✅ 反復抑制システム v3.0 インポート成功")
        repetition_success = True
    except Exception as e:
        print(f"❌ 反復抑制システム インポートエラー: {e}")
        repetition_success = False
    
    total_systems = 4
    successful_systems = sum([memory_success, coordination_success, nkat_success, repetition_success])
    success_rate = successful_systems / total_systems
    
    print(f"\n📊 インポート結果: {successful_systems}/{total_systems} システム成功 ({success_rate:.1%})")
    
    return {
        'memory_system': memory_success,
        'coordination_system': coordination_success,
        'nkat_system': nkat_success,
        'repetition_system': repetition_success,
        'success_rate': success_rate
    }

def test_memory_system_basic():
    """メモリシステム基本テスト"""
    print("\n💾 メモリシステム基本テスト")
    
    try:
        from optimization.memory_efficiency_system_v3 import create_memory_efficiency_system
        
        # システム作成
        memory_system = create_memory_efficiency_system({
            'monitoring_interval': 1.0,
            'warning_threshold_percent': 90.0
        })
        
        # 監視開始
        memory_system.start_monitoring()
        time.sleep(2.0)  # 2秒監視
        
        # メモリ情報取得
        memory_info = memory_system.get_current_memory_info()
        print(f"  プロセスメモリ: {memory_info.get('process_memory_mb', 0):.1f}MB")
        print(f"  システム使用率: {memory_info.get('system_usage_percent', 0):.1f}%")
        
        # クリーンアップテスト
        cleanup_result = memory_system.force_memory_cleanup()
        print(f"  クリーンアップ: {cleanup_result.get('recovered_mb', 0):.1f}MB回復")
        
        # 効率レポート
        efficiency_report = memory_system.get_efficiency_report()
        print(f"  GC実行回数: {efficiency_report.get('performance', {}).get('gc_triggers', 0)}")
        
        # システム停止
        memory_system.shutdown()
        
        print("✅ メモリシステム基本テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ メモリシステムテストエラー: {e}")
        return False

async def test_coordination_system_basic():
    """協調制御システム基本テスト"""
    print("\n🎯 協調制御システム基本テスト")
    
    try:
        from integration.realtime_coordination_controller_v3 import create_realtime_coordination_controller, TaskPriority
        
        # システム作成
        controller = create_realtime_coordination_controller({
            'max_workers': 4,
            'monitoring_interval': 0.1
        })
        
        # システム開始
        await controller.start()
        
        # テストタスク定義
        async def simple_task(message: str):
            await asyncio.sleep(0.1)
            return f"処理完了: {message}"
        
        # タスク投入
        task_id = await controller.submit_task(
            task_id="test_task_1",
            func=simple_task,
            args=("基本テスト",),
            priority=TaskPriority.HIGH
        )
        
        # 実行待機
        await asyncio.sleep(0.5)
        
        # 状態確認
        task_status = await controller.get_task_status(task_id)
        system_status = controller.get_system_status()
        
        print(f"  タスク状態: {task_status.get('status', '不明') if task_status else '不明'}")
        print(f"  アクティブタスク: {system_status.get('active_tasks', 0)}")
        print(f"  完了タスク: {system_status.get('completed_tasks', 0)}")
        
        # 性能レポート
        performance_report = controller.get_performance_report()
        if 'error' not in performance_report:
            print(f"  平均スループット: {performance_report.get('summary', {}).get('average_throughput', 0):.2f}タスク/秒")
        
        # システム停止
        await controller.stop()
        
        print("✅ 協調制御システム基本テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 協調制御システムテストエラー: {e}")
        return False

async def test_nkat_system_basic():
    """NKATシステム基本テスト"""
    print("\n🧠 NKATシステム基本テスト")
    
    try:
        from nkat.nkat_integration_preparation_v3 import create_nkat_integration_system, NKATCharacterArchetype
        
        # システム作成
        nkat_system = create_nkat_integration_system({
            'emotion_update_interval': 0.5,
            'pattern_recognition_threshold': 0.7
        })
        
        # キャラクター作成
        profile = nkat_system.create_character_profile(
            character_id="test_char",
            archetype=NKATCharacterArchetype.INNOCENT
        )
        
        print(f"  キャラクター作成: {profile.character_id} ({profile.archetype.name})")
        
        # テキスト処理テスト
        test_text = "おはようございます！今日もええ天気やなあ♪"
        processed_text, result_info = await nkat_system.process_text_with_nkat(
            test_text, "test_char"
        )
        
        print(f"  入力テキスト: {test_text}")
        print(f"  処理結果: {processed_text}")
        print(f"  一貫性スコア: {result_info.get('coherence_score', 0):.3f}")
        print(f"  処理時間: {result_info.get('processing_time', 0):.3f}秒")
        
        # 性能レポート
        performance_report = nkat_system.get_performance_report()
        if 'error' not in performance_report:
            summary = performance_report.get('summary', {})
            print(f"  総キャラクター数: {summary.get('total_characters', 0)}")
            print(f"  平均処理時間: {summary.get('average_processing_time', 0):.3f}秒")
        
        # システム終了
        await nkat_system.shutdown()
        
        print("✅ NKATシステム基本テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ NKATシステムテストエラー: {e}")
        return False

def test_repetition_system_basic():
    """反復抑制システム基本テスト"""
    print("\n🔄 反復抑制システム基本テスト")
    
    try:
        from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
        
        # システム作成
        suppressor = AdvancedRepetitionSuppressorV3({
            'kansai_mode': True,
            'learning_enabled': True
        })
        
        # テストテキスト（反復含む）
        test_text = "今日は今日は、ええ天気やなあ、ええ天気やなあ。"
        
        # 反復抑制処理
        processed_text, metrics = suppressor.suppress_repetitions_with_debug_v3(
            test_text, "test_character"
        )
        
        print(f"  入力テキスト: {test_text}")
        print(f"  処理結果: {processed_text}")
        compression_rate = (metrics.input_length - metrics.output_length) / metrics.input_length if metrics.input_length > 0 else 0
        print(f"  圧縮率: {compression_rate:.1%}")
        print(f"  処理時間: {metrics.processing_time_ms:.1f}ms")
        print(f"  成功率: {metrics.success_rate:.1%}")
        
        # 統計取得
        stats = suppressor.get_statistics()
        print(f"  処理件数: {stats.get('total_attempts', 0)}")
        print(f"  累積成功率: {stats.get('success_rate', 0):.1%}")
        
        print("✅ 反復抑制システム基本テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 反復抑制システムテストエラー: {e}")
        return False

async def run_quick_tests():
    """簡易テスト実行"""
    print("🚀 Phase 2完成システム 簡易動作確認テスト開始")
    print("=" * 60)
    
    # システムインポートテスト
    import_results = test_system_imports()
    
    test_results = []
    
    # 各システムの基本テスト
    if import_results['memory_system']:
        memory_result = test_memory_system_basic()
        test_results.append(('メモリ効率化', memory_result))
    
    if import_results['coordination_system']:
        coordination_result = await test_coordination_system_basic()
        test_results.append(('協調制御', coordination_result))
    
    if import_results['nkat_system']:
        nkat_result = await test_nkat_system_basic()
        test_results.append(('NKAT統合', nkat_result))
    
    if import_results['repetition_system']:
        repetition_result = test_repetition_system_basic()
        test_results.append(('反復抑制', repetition_result))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    successful_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    for system_name, result in test_results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"  {system_name}: {status}")
    
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    print(f"\n総合成功率: {successful_tests}/{total_tests} ({success_rate:.1%})")
    
    if success_rate >= 0.75:
        print("🎉 Phase 2システム開発 - 高い成功率で完了！")
    elif success_rate >= 0.5:
        print("⚠️ Phase 2システム開発 - 部分的に成功")
    else:
        print("❌ Phase 2システム開発 - 修正が必要")
    
    return success_rate

if __name__ == "__main__":
    try:
        success_rate = asyncio.run(run_quick_tests())
        sys.exit(0 if success_rate >= 0.75 else 1)
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        sys.exit(1) 