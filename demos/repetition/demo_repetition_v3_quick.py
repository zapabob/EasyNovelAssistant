# -*- coding: utf-8 -*-
"""
反復抑制システム v3 クイックデモ
成功率80%達成のための「ラスト21.7pt」改善版

コマンドライン実行例:
python demo_repetition_v3_quick.py --sim 0.50 --max_dist 50 --ngram 4 --min_compress 0.05 --drp-base 1.05 --drp-alpha 0.4
"""

import argparse
import json
import os
import sys
import time
from typing import Dict, List

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

try:
    from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3, SuppressionMetricsV3
    print("✅ v3システム読み込み成功")
except ImportError as e:
    print(f"❌ v3システム読み込み失敗: {e}")
    print("   v2システムでフォールバックします")
    from utils.repetition_suppressor import AdvancedRepetitionSuppressor, SuppressionMetrics
    
    # v3互換レイヤー
    class AdvancedRepetitionSuppressorV3(AdvancedRepetitionSuppressor):
        def suppress_repetitions_with_debug_v3(self, text, character_name=None):
            result, metrics = self.suppress_repetitions_with_debug(text, character_name)
            # v3メトリクスへの変換
            v3_metrics = type('SuppressionMetricsV3', (), {
                'input_length': metrics.input_length,
                'output_length': metrics.output_length,
                'patterns_detected': metrics.patterns_detected,
                'patterns_suppressed': metrics.patterns_suppressed,
                'detection_misses': metrics.detection_misses,
                'over_compressions': metrics.over_compressions,
                'processing_time_ms': metrics.processing_time_ms,
                'success_rate': metrics.success_rate,
                'ngram_blocks_applied': 0,
                'mecab_normalizations': 0,
                'rhetorical_exceptions': 0,
                'latin_number_blocks': 0,
                'min_compress_rate': 0.05
            })()
            return result, v3_metrics
    
    SuppressionMetricsV3 = SuppressionMetrics


def create_v3_test_cases() -> List[Dict]:
    """v3強化版テストケース（80%達成用）"""
    return [
        # === 基本同語反復（v3重点対象） ===
        {
            "name": "基本同語反復",
            "input": "お兄ちゃんお兄ちゃん、どこに行くのですかお兄ちゃん？",
            "character": "妹",
            "expected_patterns": ["お兄ちゃん"],
            "category": "same_word",
            "target_compression": 0.15
        },
        {
            "name": "関西弁同語反復",
            "input": "そやそやそや、あかんあかんあかん、やなやなそれは。",
            "character": "関西弁キャラ",
            "expected_patterns": ["そや", "あかん", "やな"],
            "category": "dialect",
            "target_compression": 0.20
        },
        {
            "name": "語尾反復複合",
            "input": "ですですね、ますますよ、でしょでしょう。",
            "character": "丁寧語キャラ",
            "expected_patterns": ["です", "ます", "でしょ"],
            "category": "ending",
            "target_compression": 0.10
        },
        
        # === 4-gramブロック対象 ===
        {
            "name": "4-gram反復",
            "input": "今日は良い天気ですね。今日は良い天気だから散歩しましょう。",
            "character": "普通の人",
            "expected_patterns": ["今日は良い"],
            "category": "ngram",
            "target_compression": 0.08
        },
        
        # === ラテン文字・数字連番 ===
        {
            "name": "連番反復",
            "input": "wwwwww、そうですね。777777って数字ですか？",
            "character": "ネットユーザー",
            "expected_patterns": ["wwwwww", "777777"],
            "category": "latin_number",
            "target_compression": 0.12
        },
        
        # === 修辞的例外保護テスト ===
        {
            "name": "修辞的反復保護",
            "input": "ねえ、ねえ、ねえ！聞いてよ。",
            "character": "感情的キャラ",
            "expected_patterns": [],  # 保護されるべき
            "category": "rhetorical",
            "target_compression": 0.0  # 圧縮されない
        },
        {
            "name": "音象徴語保護",
            "input": "ドキドキしちゃう。ワクワクするね！",
            "character": "元気キャラ",
            "expected_patterns": [],  # 保護されるべき
            "category": "onomatopoeia",
            "target_compression": 0.0
        },
        
        # === 複雑ケース ===
        {
            "name": "複合反復",
            "input": "嬉しい嬉しい、楽しい楽しい、幸せ幸せという感じですです。",
            "character": "ポジティブキャラ",
            "expected_patterns": ["嬉しい", "楽しい", "幸せ", "です"],
            "category": "complex",
            "target_compression": 0.15
        },
        {
            "name": "感嘆詞過多",
            "input": "あああああああ！うわああああああ！きゃああああああ！",
            "character": "感情豊かキャラ",
            "expected_patterns": ["あああああああ", "うわああああああ", "きゃああああああ"],
            "category": "interjection",
            "target_compression": 0.25
        },
        
        # === 境界ケース ===
        {
            "name": "短文反復",
            "input": "はい、はい、はい。",
            "character": "相槌キャラ",
            "expected_patterns": ["はい"],
            "category": "short",
            "target_compression": 0.20
        }
    ]


def parse_args():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description='反復抑制システム v3 クイックデモ')
    
    # 基本パラメータ
    parser.add_argument('--sim', type=float, default=0.50, help='類似度閾値 (default: 0.50)')
    parser.add_argument('--max_dist', type=int, default=50, help='最大検出距離 (default: 50)')
    parser.add_argument('--min_compress', type=float, default=0.05, help='最小圧縮率 (default: 0.05)')
    
    # v3新機能
    parser.add_argument('--ngram', type=int, default=4, help='n-gramブロックサイズ (default: 4)')
    parser.add_argument('--drp-base', type=float, default=1.05, help='DRP基準値 (default: 1.05)')
    parser.add_argument('--drp-alpha', type=float, default=0.4, help='DRPアルファ値 (default: 0.4)')
    parser.add_argument('--enable-mecab', action='store_true', help='MeCab正規化を有効化')
    parser.add_argument('--disable-rhetorical', action='store_true', help='修辞的保護を無効化')
    
    # 実行オプション
    parser.add_argument('--target-rate', type=float, default=0.80, help='目標成功率 (default: 0.80)')
    parser.add_argument('--verbose', action='store_true', help='詳細出力')
    parser.add_argument('--save-report', type=str, help='レポート保存ファイル名')
    
    return parser.parse_args()


def create_v3_config(args) -> Dict:
    """引数からv3設定を構築"""
    return {
        'similarity_threshold': args.sim,
        'max_distance': args.max_dist,
        'min_compress_rate': args.min_compress,
        'enable_4gram_blocking': args.ngram > 0,
        'ngram_block_size': args.ngram,
        'enable_drp': True,
        'drp_base': args.drp_base,
        'drp_alpha': args.drp_alpha,
        'enable_mecab_normalization': args.enable_mecab,
        'enable_rhetorical_protection': not args.disable_rhetorical,
        'enable_aggressive_mode': True,
        'debug_mode': args.verbose,
        'min_repeat_threshold': 1,
        'enable_latin_number_detection': True
    }


def run_v3_quick_test(config: Dict, test_cases: List[Dict], target_success_rate: float = 0.8) -> Dict:
    """v3クイックテスト実行"""
    print(f"🚀 反復抑制システム v3 クイックテスト開始")
    print(f"   目標成功率: {target_success_rate:.1%}")
    print(f"   テストケース: {len(test_cases)}件")
    print("=" * 60)
    
    # システム初期化
    suppressor = AdvancedRepetitionSuppressorV3(config)
    
    results = []
    category_stats = {}
    
    start_time = time.time()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 テスト {i}/{len(test_cases)}: {test_case['name']}")
        
        # 処理実行
        result_text, metrics = suppressor.suppress_repetitions_with_debug_v3(
            test_case['input'], 
            test_case['character']
        )
        
        # 成功判定（v3基準）
        compression_rate = (metrics.input_length - metrics.output_length) / metrics.input_length
        meets_compression_target = compression_rate >= test_case.get('target_compression', config['min_compress_rate'])
        success = metrics.success_rate >= 0.7 and meets_compression_target  # v3では70%+圧縮達成を成功とする
        
        # 結果記録
        test_result = {
            'test_case': test_case['name'],
            'category': test_case['category'],
            'success': success,
            'success_rate': metrics.success_rate,
            'compression_rate': compression_rate,
            'target_compression': test_case.get('target_compression', config['min_compress_rate']),
            'input_length': metrics.input_length,
            'output_length': metrics.output_length,
            'patterns_detected': metrics.patterns_detected,
            'patterns_suppressed': metrics.patterns_suppressed,
            'processing_time_ms': metrics.processing_time_ms,
            'input_text': test_case['input'][:50] + "..." if len(test_case['input']) > 50 else test_case['input'],
            'output_text': result_text[:50] + "..." if len(result_text) > 50 else result_text,
            'v3_features': {
                'ngram_blocks': getattr(metrics, 'ngram_blocks_applied', 0),
                'mecab_normalizations': getattr(metrics, 'mecab_normalizations', 0),
                'rhetorical_exceptions': getattr(metrics, 'rhetorical_exceptions', 0),
                'latin_blocks': getattr(metrics, 'latin_number_blocks', 0)
            }
        }
        
        results.append(test_result)
        
        # カテゴリ別統計
        category = test_case['category']
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'success': 0}
        category_stats[category]['total'] += 1
        if success:
            category_stats[category]['success'] += 1
        
        # 結果表示
        status_icon = "✅" if success else "❌"
        print(f"   {status_icon} 成功率: {metrics.success_rate:.1%}, 圧縮率: {compression_rate:.1%}")
        
        if config.get('debug_mode', False):
            print(f"      入力: {test_case['input'][:40]}...")
            print(f"      出力: {result_text[:40]}...")
            print(f"      処理時間: {metrics.processing_time_ms:.1f}ms")
            
            # v3機能の使用状況
            v3_features = test_result['v3_features']
            if any(v3_features.values()):
                print(f"      v3機能: 4-gram={v3_features['ngram_blocks']}, MeCab={v3_features['mecab_normalizations']}, 修辞={v3_features['rhetorical_exceptions']}, 連番={v3_features['latin_blocks']}")
    
    total_time = time.time() - start_time
    
    # 総合統計
    total_tests = len(results)
    total_success = sum(1 for r in results if r['success'])
    overall_success_rate = total_success / total_tests if total_tests > 0 else 0
    
    avg_compression = sum(r['compression_rate'] for r in results) / total_tests if total_tests > 0 else 0
    avg_processing_time = sum(r['processing_time_ms'] for r in results) / total_tests if total_tests > 0 else 0
    
    # v3機能統計
    total_ngram_blocks = sum(r['v3_features']['ngram_blocks'] for r in results)
    total_mecab_normalizations = sum(r['v3_features']['mecab_normalizations'] for r in results)
    total_rhetorical_exceptions = sum(r['v3_features']['rhetorical_exceptions'] for r in results)
    total_latin_blocks = sum(r['v3_features']['latin_blocks'] for r in results)
    
    print("\n" + "=" * 60)
    print(f"📊 v3システム総合結果")
    print(f"   成功率: {overall_success_rate:.1%} ({total_success}/{total_tests})")
    print(f"   目標達成: {'🎉 達成！' if overall_success_rate >= target_success_rate else '❌ 未達'}")
    print(f"   平均圧縮率: {avg_compression:.1%}")
    print(f"   平均処理時間: {avg_processing_time:.1f}ms")
    print(f"   総処理時間: {total_time:.2f}秒")
    
    print(f"\n🔧 v3機能使用状況:")
    print(f"   4-gramブロック: {total_ngram_blocks}回")
    print(f"   MeCab正規化: {total_mecab_normalizations}回")
    print(f"   修辞的例外: {total_rhetorical_exceptions}回")
    print(f"   連番除去: {total_latin_blocks}回")
    
    print(f"\n📈 カテゴリ別成功率:")
    for category, stats in category_stats.items():
        success_rate = stats['success'] / stats['total']
        print(f"   {category}: {success_rate:.1%} ({stats['success']}/{stats['total']})")
    
    # 失敗ケースの分析
    failed_cases = [r for r in results if not r['success']]
    if failed_cases:
        print(f"\n❌ 失敗ケース分析 ({len(failed_cases)}件):")
        for case in failed_cases:
            print(f"   - {case['test_case']}: 成功率{case['success_rate']:.1%}, 圧縮率{case['compression_rate']:.1%}")
    
    # 改善提案
    if overall_success_rate < target_success_rate:
        gap = target_success_rate - overall_success_rate
        print(f"\n🔍 改善提案（残り{gap:.1%}pt）:")
        
        if avg_compression < config['min_compress_rate']:
            print(f"   - 圧縮率向上: 現在{avg_compression:.1%} → 目標{config['min_compress_rate']:.1%}")
            print(f"     → similarity_threshold を {config['similarity_threshold']:.2f} → {max(0.3, config['similarity_threshold'] - 0.1):.2f} に下げる")
        
        worst_category = min(category_stats.items(), key=lambda x: x[1]['success'] / x[1]['total'])
        print(f"   - 最弱カテゴリ: {worst_category[0]} ({worst_category[1]['success']}/{worst_category[1]['total']})")
        
        if total_ngram_blocks == 0:
            print(f"   - 4-gramブロック未使用 → ngram_block_size を3に下げる")
        
        if total_rhetorical_exceptions > total_success // 2:
            print(f"   - 修辞的例外が多すぎ → enable_rhetorical_protection=False を検討")
    
    # 設定最適化提案
    print(f"\n⚙️ 次回推奨設定:")
    optimized_config = dict(config)
    if overall_success_rate < target_success_rate:
        optimized_config['similarity_threshold'] = max(0.3, config['similarity_threshold'] - 0.05)
        if avg_compression < config['min_compress_rate']:
            optimized_config['min_compress_rate'] = max(0.03, config['min_compress_rate'] - 0.01)
    
    print(f"   --sim {optimized_config['similarity_threshold']:.2f} --max_dist {optimized_config['max_distance']} --ngram {optimized_config.get('ngram_block_size', 4)} --min_compress {optimized_config['min_compress_rate']:.2f} --drp-base {optimized_config['drp_base']:.2f} --drp-alpha {optimized_config['drp_alpha']:.1f}")
    
    return {
        'overall_success_rate': overall_success_rate,
        'target_achievement': overall_success_rate >= target_success_rate,
        'total_tests': total_tests,
        'total_success': total_success,
        'average_compression_rate': avg_compression,
        'average_processing_time_ms': avg_processing_time,
        'total_processing_time_s': total_time,
        'v3_feature_usage': {
            'ngram_blocks': total_ngram_blocks,
            'mecab_normalizations': total_mecab_normalizations,
            'rhetorical_exceptions': total_rhetorical_exceptions,
            'latin_blocks': total_latin_blocks
        },
        'category_stats': category_stats,
        'failed_cases': failed_cases,
        'optimized_config': optimized_config,
        'config_used': config,
        'detailed_results': results
    }


def save_report(report: Dict, filename: str):
    """レポートをJSONファイルに保存"""
    try:
        os.makedirs('logs/v3_tests', exist_ok=True)
        filepath = f'logs/v3_tests/{filename}'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 レポート保存: {filepath}")
    except Exception as e:
        print(f"\n❌ レポート保存失敗: {e}")


def main():
    """メイン実行関数"""
    args = parse_args()
    
    print("🔥 反復抑制システム v3 - 「ラスト21.7pt」強化版")
    print("   58.3% → 80% 達成を目指します！")
    print("=" * 60)
    
    # 設定構築
    config = create_v3_config(args)
    
    print("⚙️ v3設定:")
    print(f"   類似度閾値: {config['similarity_threshold']}")
    print(f"   最大距離: {config['max_distance']}")
    print(f"   最小圧縮率: {config['min_compress_rate']:.1%}")
    print(f"   4-gramブロック: {config['enable_4gram_blocking']} (サイズ: {config.get('ngram_block_size', 0)})")
    print(f"   DRP: base={config['drp_base']}, alpha={config['drp_alpha']}")
    print(f"   MeCab: {config['enable_mecab_normalization']}")
    print(f"   修辞的保護: {config['enable_rhetorical_protection']}")
    
    # テストケース準備
    test_cases = create_v3_test_cases()
    
    # テスト実行
    report = run_v3_quick_test(config, test_cases, args.target_rate)
    
    # レポート保存
    if args.save_report:
        save_report(report, args.save_report)
    
    # 最終判定
    if report['target_achievement']:
        print(f"\n🎉 目標達成！ 成功率 {report['overall_success_rate']:.1%} ≥ {args.target_rate:.1%}")
        print("   80%ラインに到達しました！🔥")
    else:
        gap = args.target_rate - report['overall_success_rate']
        print(f"\n📈 あと{gap:.1%}pt で目標達成です")
        print("   次回推奨設定で再チャレンジしてください")
    
    return 0 if report['target_achievement'] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 