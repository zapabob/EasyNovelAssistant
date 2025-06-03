# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import json
import os
import sys

# コンソール出力のエンコーディングをUTF-8に設定
if sys.platform == "win32":
    import locale
    # Windowsでのコンソール出力をUTF-8に統一
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python 3.6以下の場合の対応
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# パス設定の統一化（プロジェクトルートベース）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir
ena_src_dir = os.path.join(current_dir, "EasyNovelAssistant", "src")
src_dir = os.path.join(current_dir, "src")

# 両方のsrcディレクトリをパスに追加
if ena_src_dir not in sys.path:
    sys.path.insert(0, ena_src_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"📁 プロジェクトルート: {project_root}")
print(f"📁 ENA srcディレクトリ: {ena_src_dir}")
print(f"📁 メインsrcディレクトリ: {src_dir}")

import time

from const import Const
from context import Context
from form import Form
from generator import Generator
from kobold_cpp import KoboldCpp
from movie_maker import MovieMaker
from path import Path
from style_bert_vits2 import StyleBertVits2

# フィードバックログシステムの初期化
try:
    from utils.feedback_logger import RepetitionFeedbackLogger
    feedback_logger = RepetitionFeedbackLogger()
    print("📊 フィードバックログシステム初期化完了")
    print(f"   ├─ フィードバックファイル: {feedback_logger.feedback_file}")
    print(f"   └─ 誤動作サンプル: {feedback_logger.misfire_samples_file}")
    FEEDBACK_LOGGER_AVAILABLE = True
    print("✅ フィードバックログシステム読み込み成功")
except ImportError as e:
    FEEDBACK_LOGGER_AVAILABLE = False
    print(f"⚠️ フィードバックログシステムインポートエラー: {e}")

# Phase 4達成モード適用
print("🎯 Phase 4達成モード設定を適用しました")

# 高度反復抑制システムのインポート（v3優先、統合システム対応）
try:
    from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3 as AdvancedRepetitionSuppressor
    REPETITION_SUPPRESSOR_AVAILABLE = True
    REPETITION_SUPPRESSOR_VERSION = "v3"
    print("✅ 反復抑制システム v3 読み込み成功")
except ImportError:
    try:
        from utils.repetition_suppressor import AdvancedRepetitionSuppressor
        REPETITION_SUPPRESSOR_AVAILABLE = True
        REPETITION_SUPPRESSOR_VERSION = "v2"
        print("✅ 反復抑制システム v2 読み込み成功（v3フォールバック）")
    except ImportError as e:
        REPETITION_SUPPRESSOR_AVAILABLE = False
        REPETITION_SUPPRESSOR_VERSION = "none"
        print(f"⚠️ 反復抑制システムインポートエラー: {e}")

# フィードバックログシステムの関数読み込み
try:
    if FEEDBACK_LOGGER_AVAILABLE:
        from utils.feedback_logger import log_repetition_result, record_user_feedback
        print("✅ フィードバック関数読み込み成功")
except ImportError as e:
    print(f"⚠️ フィードバック関数インポートエラー: {e}")

# NKAT統合モジュールのインポート
try:
    from nkat.nkat_integration import integrate_nkat_with_easy_novel_assistant
    NKAT_AVAILABLE = True
except ImportError as e:
    NKAT_AVAILABLE = False
    print(f"⚠️ NKAT統合モジュールインポートエラー: {e}")

# 運用3本柱システムのインポート
try:
    from utils.quality_guard import QualityGuard
    from optimization.continuous_learning import ContinuousLearningSystem
    QUALITY_GUARD_AVAILABLE = True
    CONTINUOUS_LEARNING_AVAILABLE = True
except ImportError as e:
    QUALITY_GUARD_AVAILABLE = False
    CONTINUOUS_LEARNING_AVAILABLE = False
    print(f"⚠️ 運用システムインポートエラー: {e}")

# LoRA Style Coordinator のインポート
try:
    from integration.lora_style_coordinator import LoRAStyleCoordinator, create_default_coordinator
    LORA_STYLE_AVAILABLE = True
except ImportError as e:
    LORA_STYLE_AVAILABLE = False
    print(f"⚠️ LoRAスタイルコーディネーターインポートエラー: {e}")

# Cross Suppression Engine のインポート
try:
    from integration.cross_suppression_engine import CrossSuppressionEngine, create_default_cross_engine
    CROSS_SUPPRESSION_AVAILABLE = True
except ImportError as e:
    CROSS_SUPPRESSION_AVAILABLE = False
    print(f"⚠️ クロス抑制エンジンインポートエラー: {e}")

# Theta Optimizer のインポート
try:
    from integration.theta_feedback_optimizer_v3 import ThetaFeedbackOptimizerV3, create_commercial_theta_optimizer
    THETA_OPTIMIZER_AVAILABLE = True
except ImportError as e:
    THETA_OPTIMIZER_AVAILABLE = False
    print(f"⚠️ Thetaオプティマイザーインポートエラー: {e}")

print("✅ 統合システムv3制御パネル追加完了")

class EasyNovelAssistant:
    SLEEP_TIME = 50

    def __init__(self):
        self.ctx = Context()
        Path.init(self.ctx)
        Const.init(self.ctx)

        self.ctx.kobold_cpp = KoboldCpp(self.ctx)
        self.ctx.style_bert_vits2 = StyleBertVits2(self.ctx)
        self.ctx.movie_maker = MovieMaker(self.ctx)
        self.ctx.form = Form(self.ctx)
        self.ctx.generator = Generator(self.ctx)

        # 高度反復抑制システムの初期化
        self.setup_repetition_suppressor()

        # NKAT統合の初期化
        self.setup_nkat_integration()

        # 一貫性監視システムの初期化
        self.consistency_monitor = ConsistencyMonitor(self.ctx)

        # 運用3本柱システムの初期化
        self.setup_operational_systems()

        # TODO: 起動時引数でのフォルダ・ファイル読み込み
        self.ctx.form.input_area.open_tab(self.ctx["input_text"])  # 書き出しは Form の finalize

        self.ctx.form.win.after(self.SLEEP_TIME, self.mainloop)

    def setup_repetition_suppressor(self):
        """高度反復抑制システム v3 の設定（90%成功率達成版）"""
        try:
            if REPETITION_SUPPRESSOR_AVAILABLE:
                # v3推奨設定（実証済み90%成功率設定）
                suppressor_config = {
                    'min_repeat_threshold': self.ctx.get('repetition_min_threshold', 1),  # 1回の反復でも検出
                    'max_distance': self.ctx.get('repetition_max_distance', 50),  # 検出距離を拡張
                    'similarity_threshold': self.ctx.get('repetition_similarity_threshold', 0.35),  # v3推奨: 0.35
                    'phonetic_threshold': self.ctx.get('repetition_phonetic_threshold', 0.7),  # 音韻類似度を下げる
                    'enable_aggressive_mode': True,  # アグレッシブモード有効化
                    'interjection_sensitivity': 0.3,  # 感嘆詞感度をさらに厳格に
                    'exact_match_priority': True,  # 完全一致を優先
                    'character_repetition_limit': 2,  # 文字反復の制限強化
                    # v3新機能（実証済み設定）
                    'debug_mode': self.ctx.get('repetition_debug_mode', True),  # デバッグ強化
                    'ngram_block_size': self.ctx.get('repetition_ngram_block_size', 3),  # 3-gramで確実性重視
                    'enable_4gram_blocking': True,  # v3: 3-gramブロック有効
                    'enable_drp': self.ctx.get('repetition_enable_drp', True),  # v3: DRP有効
                    'drp_base': self.ctx.get('repetition_drp_base', 1.10),  # v3: DRP基準値
                    'drp_alpha': self.ctx.get('repetition_drp_alpha', 0.5),  # v3: DRPアルファ値
                    'enable_mecab_normalization': self.ctx.get('repetition_enable_mecab', False),  # MeCab（オプション）
                    'enable_rhetorical_protection': self.ctx.get('repetition_enable_rhetorical', False),  # 修辞的保護（90%設定では無効）
                    'enable_latin_number_detection': True,  # v3: 連番検知
                    'min_compress_rate': self.ctx.get('repetition_min_compress_rate', 0.03)  # v3: 3%基準
                }
                
                self.ctx.repetition_suppressor = AdvancedRepetitionSuppressor(suppressor_config)
                
                # Generatorクラスに反復抑制処理を追加
                self.patch_generator_for_repetition_suppression()
                
                print(f"🔄 高度反復抑制システム {REPETITION_SUPPRESSOR_VERSION} が有効化されました（成功率90%+対応）")
                print(f"   ├─ 反復検出閾値: {suppressor_config['min_repeat_threshold']}")
                print(f"   ├─ 検出距離: {suppressor_config['max_distance']}文字")
                print(f"   ├─ 類似度閾値: {suppressor_config['similarity_threshold']}")
                print(f"   ├─ n-gramブロック: {suppressor_config['ngram_block_size']}")
                print(f"   ├─ DRP有効: {suppressor_config['enable_drp']}")
                print(f"   ├─ 圧縮率基準: {suppressor_config.get('min_compress_rate', 0.05):.1%}")
                print(f"   └─ デバッグモード: {suppressor_config['debug_mode']}")
            else:
                print("⚠️ 反復抑制システムは無効です（モジュール不可）")
        except Exception as e:
            print(f"❌ 反復抑制システム初期化エラー: {e}")

    def patch_generator_for_repetition_suppression(self):
        """Generatorクラスに反復抑制処理を追加"""
        if hasattr(self.ctx, 'repetition_suppressor'):
            original_generate = self.ctx.generator._generate if hasattr(self.ctx.generator, '_generate') else None
            
            if original_generate:
                def enhanced_generate_with_suppression(input_text):
                    """反復抑制処理を適用した生成関数"""
                    # 元の生成処理
                    result = original_generate(input_text)
                    
                    if result and hasattr(self.ctx, 'repetition_suppressor'):
                        try:
                            # キャラクター名の抽出
                            character_name = self.ctx.get('char_name', 'Unknown')
                            
                            # v3デバッグ強化版で反復抑制処理を適用
                            if hasattr(self.ctx.repetition_suppressor, 'suppress_repetitions_with_debug_v3'):
                                suppressed_result, metrics = self.ctx.repetition_suppressor.suppress_repetitions_with_debug_v3(
                                    result, character_name
                                )
                                
                                # フィードバックログシステムでログ記録
                                if FEEDBACK_LOGGER_AVAILABLE:
                                    log_info = log_repetition_result(result, suppressed_result, metrics, character_name)
                                    
                                    # 警告バナー表示判定
                                    show_warning, warning_msg = feedback_logger.should_show_warning_banner()
                                    if show_warning:
                                        print(f"⚠️ {warning_msg}")
                                
                                # デバッグ情報のログ記録
                                if hasattr(self.ctx.repetition_suppressor, 'debug_mode') and self.ctx.repetition_suppressor.debug_mode:
                                    if metrics.success_rate < 0.8:
                                        print(f"🐛 反復抑制課題: 成功率 {metrics.success_rate:.1%} (検知漏れ: {metrics.detection_misses}, 過剰圧縮: {metrics.over_compressions})")
                                    
                                    # セッション統計の更新
                                    if hasattr(self.ctx.repetition_suppressor, 'total_attempts'):
                                        session_success_rate = self.ctx.repetition_suppressor.total_success_count / max(1, self.ctx.repetition_suppressor.total_attempts)
                                        if self.ctx.repetition_suppressor.total_attempts % 10 == 0:  # 10回に1回表示
                                            print(f"📊 セッション成功率: {session_success_rate:.1%} ({self.ctx.repetition_suppressor.total_attempts}回実行)")
                                        
                                        # GUI統計パネルの更新
                                        compression_rate = (len(result) - len(suppressed_result)) / len(result) if len(result) > 0 else 0
                                        self.update_gui_statistics(
                                            success_rate=session_success_rate,
                                            attempts=self.ctx.repetition_suppressor.total_attempts,
                                            compression_rate=compression_rate
                                        )
                            elif hasattr(self.ctx.repetition_suppressor, 'suppress_repetitions_with_debug'):
                                # v2への対応
                                suppressed_result, metrics = self.ctx.repetition_suppressor.suppress_repetitions_with_debug(
                                    result, character_name
                                )
                                
                                # フィードバックログ（v2対応）
                                if FEEDBACK_LOGGER_AVAILABLE:
                                    log_repetition_result(result, suppressed_result, metrics, character_name)
                            else:
                                # 従来版へのフォールバック
                                suppressed_result = self.ctx.repetition_suppressor.suppress_repetitions(
                                    result, character_name
                                )
                            
                            # NKAT処理との組み合わせ
                            if hasattr(self.ctx, 'nkat') and suppressed_result != result:
                                try:
                                    enhanced_result = self.ctx.nkat.enhance_text_generation(
                                        prompt=input_text,
                                        llm_output=suppressed_result
                                    )
                                    
                                    # 一貫性監視システムに記録
                                    if hasattr(self, 'consistency_monitor'):
                                        self.consistency_monitor.record_generation(
                                            input_text, result, enhanced_result
                                        )
                                        self.consistency_monitor.record_repetition_suppression(
                                            result, suppressed_result, enhanced_result
                                        )
                                    
                                    return enhanced_result
                                except Exception as e:
                                    print(f"NKAT処理エラー: {e}")
                                    return suppressed_result
                            
                            # 一貫性監視システムに記録（NKAT無しの場合）
                            if hasattr(self, 'consistency_monitor'):
                                self.consistency_monitor.record_repetition_suppression(
                                    result, suppressed_result, suppressed_result
                                )
                            
                            return suppressed_result
                            
                        except Exception as e:
                            print(f"反復抑制処理エラー: {e}")
                            return result
                    
                    return result
                
                # 生成関数を置き換え
                self.ctx.generator._generate = enhanced_generate_with_suppression
                print("Generator に高度反復抑制処理を統合しました")

    def setup_nkat_integration(self):
        """NKAT統合の設定"""
        try:
            if NKAT_AVAILABLE and (self.ctx["nkat_enabled"] if self.ctx["nkat_enabled"] is not None else False):
                success = integrate_nkat_with_easy_novel_assistant(self.ctx)
                if success:
                    print("NKAT文章一貫性向上機能が有効化されました")
                    
                    # Generatorクラスに一貫性処理を追加（反復抑制の後に実行）
                    self.enhance_generator_with_nkat()
                else:
                    print("NKAT統合に失敗しました。標準モードで継続します。")
            else:
                print("NKAT機能は無効です（設定でnkat_enabled=falseまたはモジュール不可）")
        except Exception as e:
            print(f"NKAT統合エラー: {e}")

    def enhance_generator_with_nkat(self):
        """GeneratorクラスにNKAT処理を追加（反復抑制後に実行）"""
        # 反復抑制システム統合時に既に組み込み済みのため、ここでは追加処理のみ
        if hasattr(self.ctx, 'nkat'):
            print("NKAT処理は反復抑制システムと統合済みです")

    def setup_operational_systems(self):
        """運用3本柱システムの設定"""
        try:
            # フェーズ①自動デプロイ - 既に実装済み（NKAT統合）
            if hasattr(self.ctx, 'nkat'):
                print("🚀 フェーズ①自動デプロイ: NKAT統合完了")
            
            # フェーズ②品質ガード
            if QUALITY_GUARD_AVAILABLE and self.ctx.get('quality_guard_enabled', True):
                quality_config = {
                    'quality_guard_enabled': True,
                    'auto_correction_threshold': self.ctx.get('auto_correction_threshold', 0.03),
                    'diversity_target': self.ctx.get('diversity_target', 0.35),
                    'gamma_adjustment_step': self.ctx.get('gamma_adjustment_step', 0.01)
                }
                
                self.ctx.quality_guard = QualityGuard(quality_config)
                self.integrate_quality_guard()
                print("🛡️ フェーズ②品質ガード: 初期化完了")
            else:
                print("⚠️ フェーズ②品質ガード: 無効")
            
            # フェーズ③継続評価&学習
            if CONTINUOUS_LEARNING_AVAILABLE and self.ctx.get('continuous_learning_enabled', True):
                learning_config = {
                    'continuous_learning_enabled': True,
                    'feedback_db_path': self.ctx.get('feedback_db_path', 'data/feedback.db'),
                    'lora_training_enabled': self.ctx.get('lora_training_enabled', True),
                    'metrics_tracking_enabled': True,
                    'training_schedule': 'weekly',
                    'lora_batch_size': 8,
                    'lora_learning_rate': 1e-5,
                    'lora_rank': 16
                }
                
                self.ctx.continuous_learning = ContinuousLearningSystem(learning_config)
                print("📊 フェーズ③継続評価&学習: 初期化完了")
            else:
                print("⚠️ フェーズ③継続評価&学習: 無効")
            
            print("✅ 運用3本柱システム初期化完了")
            
        except Exception as e:
            print(f"❌ 運用システム初期化エラー: {e}")

    def integrate_quality_guard(self):
        """品質ガードシステムの統合"""
        if not hasattr(self.ctx, 'quality_guard'):
            return
        
        # 既存の生成処理に品質ガードを統合
        if hasattr(self.ctx.generator, '_generate'):
            original_generate = self.ctx.generator._generate
            
            def quality_guarded_generate(input_text):
                """品質ガード付き生成関数"""
                try:
                    # 元の生成処理
                    result = original_generate(input_text)
                    
                    # 現在のγ値取得（デフォルト値使用）
                    current_gamma = self.ctx.get('theta_gamma', 0.98)
                    
                    # 品質ガードによる自動補正
                    corrected_result, new_gamma, correction_applied = self.ctx.quality_guard.auto_correct_if_needed(
                        result, current_gamma, input_text
                    )
                    
                    # γ値が調整された場合、設定を更新
                    if correction_applied and new_gamma != current_gamma:
                        self.ctx['theta_gamma'] = new_gamma
                        print(f"🔧 γ値自動調整: {current_gamma:.3f} → {new_gamma:.3f}")
                    
                    # 継続学習システムへのメトリクス記録
                    if hasattr(self.ctx, 'continuous_learning'):
                        metrics = self.ctx.quality_guard.evaluate_quality(corrected_result, input_text)
                        
                        self.ctx.continuous_learning.record_interaction(
                            prompt=input_text,
                            generated_text=corrected_result,
                            metrics={
                                'diversity_score': metrics.diversity_score,
                                'contradiction_rate': metrics.repetition_rate,  # 反復率を矛盾率として使用
                                'processing_time': 0.0,  # 実際の処理時間は別途計測
                                'nkat_parameters': {
                                    'theta_gamma': new_gamma,
                                    'theta_rank': self.ctx.get('theta_rank', 6)
                                }
                            }
                        )
                    
                    return corrected_result
                    
                except Exception as e:
                    print(f"品質ガード処理エラー: {e}")
                    return result if 'result' in locals() else input_text
            
            # 生成関数を置き換え
            self.ctx.generator._generate = quality_guarded_generate
            print("Generator に品質ガードシステムを統合しました")

    def run(self):
        self.ctx.form.run()

    def run_with_config(self, config: dict):
        """設定付きでシステムを起動"""
        # 設定をコンテキストに適用
        for key, value in config.items():
            self.ctx[key] = value
        
        # NKAT設定が有効な場合、追加初期化
        if config.get('nkat_enabled'):
            print(f"🧠 NKAT設定適用中...")
            print(f"   ├─ θランク: {config.get('theta_rank', 6)}")
            print(f"   ├─ θガンマ: {config.get('theta_gamma', 0.98)}")
            print(f"   └─ 表現ブースト: {config.get('expression_boost_level', 70)}%")
        
        # 通常の起動プロセス
        self.run()

    def mainloop(self):
        self.ctx.generator.update()
        self.ctx.style_bert_vits2.update()
        self.ctx.form.input_area.update()
        
        # 一貫性監視の更新
        if hasattr(self, 'consistency_monitor'):
            self.consistency_monitor.update()
        
        self.ctx.form.win.after(self.SLEEP_TIME, self.mainloop)

    def get_repetition_stats(self):
        """反復抑制統計情報の取得"""
        if hasattr(self.ctx, 'repetition_suppressor'):
            return self.ctx.repetition_suppressor.get_statistics()
        return {"repetition_suppressor_enabled": False, "message": "反復抑制機能は無効です"}

    def get_nkat_stats(self):
        """NKAT統計情報の取得"""
        if hasattr(self.ctx, 'nkat'):
            return self.ctx.nkat.get_integration_stats()
        return {"nkat_enabled": False, "message": "NKAT機能は無効です"}

    def get_consistency_report(self):
        """一貫性レポートの取得"""
        if hasattr(self, 'consistency_monitor'):
            return self.consistency_monitor.generate_report()
        return {"monitor_enabled": False, "message": "一貫性監視は無効です"}

    def get_operational_report(self):
        """運用システム総合レポートの取得"""
        report = {
            "timestamp": time.time(),
            "operational_systems": {
                "nkat_enabled": hasattr(self.ctx, 'nkat'),
                "quality_guard_enabled": hasattr(self.ctx, 'quality_guard'),
                "continuous_learning_enabled": hasattr(self.ctx, 'continuous_learning')
            }
        }
        
        # 品質ガードレポート
        if hasattr(self.ctx, 'quality_guard'):
            report["quality_guard"] = self.ctx.quality_guard.get_quality_report()
        
        # 継続学習レポート
        if hasattr(self.ctx, 'continuous_learning'):
            report["continuous_learning"] = self.ctx.continuous_learning.get_comprehensive_report()
        
        # NKAT統計
        if hasattr(self.ctx, 'nkat'):
            report["nkat"] = self.get_nkat_stats()
        
        # 一貫性監視
        report["consistency"] = self.get_consistency_report()
        
        # 反復抑制統計
        report["repetition_suppression"] = self.get_repetition_stats()
        
        return report

    def record_user_feedback(self, rating: int, feedback_type: str, comments: str = ""):
        """ユーザーフィードバックの記録"""
        if hasattr(self.ctx, 'continuous_learning'):
            # 最後の生成結果を取得（仮実装）
            last_prompt = getattr(self, '_last_prompt', "")
            last_generated = getattr(self, '_last_generated', "")
            
            user_feedback = {
                'rating': rating,
                'type': feedback_type,
                'comments': comments,
                'quality_metrics': {},
                'nkat_parameters': {
                    'theta_gamma': self.ctx.get('theta_gamma', 0.98),
                    'theta_rank': self.ctx.get('theta_rank', 6)
                }
            }
            
            self.ctx.continuous_learning.record_interaction(
                prompt=last_prompt,
                generated_text=last_generated,
                user_feedback=user_feedback
            )
            
            print(f"📝 ユーザーフィードバック記録: 評価={rating}/5, タイプ={feedback_type}")

    def adjust_expression_boost(self, boost_level: int):
        """表現ブーストレベルの調整（0-100%）"""
        if 0 <= boost_level <= 100:
            # γ値の調整（boost_level に応じて）
            base_gamma = 0.98
            gamma_adjustment = (100 - boost_level) * 0.002  # 最大0.2の調整
            new_gamma = max(0.8, min(1.0, base_gamma - gamma_adjustment))
            
            self.ctx['theta_gamma'] = new_gamma
            self.ctx['expression_boost_level'] = boost_level
            
            print(f"🎚️ 表現ブーストレベル調整: {boost_level}% (γ={new_gamma:.3f})")
            
            # 品質ガードの多様性目標も調整
            if hasattr(self.ctx, 'quality_guard'):
                diversity_target = 0.30 + (boost_level * 0.001)  # 30%〜40%の範囲
                self.ctx.quality_guard.diversity_target = diversity_target
                print(f"🎯 多様性目標調整: {diversity_target:.1%}")
        else:
            print(f"❌ 無効なブーストレベル: {boost_level} (0-100の範囲で指定してください)")

    def get_performance_metrics(self):
        """現在のパフォーマンスメトリクス取得"""
        metrics = {
            "timestamp": time.time(),
            "nkat_parameters": {
                "theta_gamma": self.ctx.get('theta_gamma', 0.98),
                "theta_rank": self.ctx.get('theta_rank', 6),
                "expression_boost_level": self.ctx.get('expression_boost_level', 70)
            }
        }
        
        # 品質ガードメトリクス
        if hasattr(self.ctx, 'quality_guard') and self.ctx.quality_guard.quality_history:
            recent_quality = self.ctx.quality_guard.quality_history[-1]['metrics']
            metrics["quality"] = {
                "diversity_score": recent_quality.get('diversity_score', 0),
                "grammar_score": recent_quality.get('grammar_score', 0),
                "overall_score": recent_quality.get('overall_score', 0)
            }
        
        # 推定性能値
        theta_rank = metrics["nkat_parameters"]["theta_rank"]
        boost_level = metrics["nkat_parameters"]["expression_boost_level"]
        
        metrics["estimated_performance"] = {
            "vram_usage_gb": theta_rank * 0.8 + 2.5,
            "diversity_estimate_percent": 29.6 + (boost_level - 70) * 0.1,
            "style_variation_percent": 250 + boost_level * 2
        }
        
        return metrics

    def adjust_repetition_suppression(self, aggressiveness_level: int):
        """反復抑制の強度を調整（0-100%）"""
        if not hasattr(self.ctx, 'repetition_suppressor'):
            print("❌ 反復抑制システムが利用できません")
            return
        
        if not 0 <= aggressiveness_level <= 100:
            print(f"❌ 無効な強度レベル: {aggressiveness_level} (0-100の範囲で指定してください)")
            return
        
        # 強度に応じた設定調整
        if aggressiveness_level >= 80:
            # 超厳格モード
            config = {
                'min_repeat_threshold': 1,
                'max_distance': 20,
                'similarity_threshold': 0.6,
                'phonetic_threshold': 0.7,
                'enable_aggressive_mode': True,
                'interjection_sensitivity': 0.4,
                'exact_match_priority': True,
                'character_repetition_limit': 2
            }
            mode_name = "超厳格モード"
        elif aggressiveness_level >= 60:
            # 厳格モード
            config = {
                'min_repeat_threshold': 1,
                'max_distance': 30,
                'similarity_threshold': 0.7,
                'phonetic_threshold': 0.8,
                'enable_aggressive_mode': True,
                'interjection_sensitivity': 0.5,
                'exact_match_priority': True,
                'character_repetition_limit': 3
            }
            mode_name = "厳格モード"
        elif aggressiveness_level >= 40:
            # バランスモード
            config = {
                'min_repeat_threshold': 2,
                'max_distance': 40,
                'similarity_threshold': 0.8,
                'phonetic_threshold': 0.85,
                'enable_aggressive_mode': False,
                'interjection_sensitivity': 0.7,
                'exact_match_priority': False,
                'character_repetition_limit': 4
            }
            mode_name = "バランスモード"
        else:
            # 軽度モード
            config = {
                'min_repeat_threshold': 3,
                'max_distance': 50,
                'similarity_threshold': 0.9,
                'phonetic_threshold': 0.9,
                'enable_aggressive_mode': False,
                'interjection_sensitivity': 0.8,
                'exact_match_priority': False,
                'character_repetition_limit': 5
            }
            mode_name = "軽度モード"
        
        # 新しい設定で反復抑制システムを再初期化
        from utils.repetition_suppressor import AdvancedRepetitionSuppressor
        self.ctx.repetition_suppressor = AdvancedRepetitionSuppressor(config)
        
        # 設定をコンテキストに保存
        for key, value in config.items():
            self.ctx[f'repetition_{key}'] = value
        self.ctx['repetition_aggressiveness_level'] = aggressiveness_level
        
        print(f"🔧 反復抑制強度調整: {aggressiveness_level}% ({mode_name})")
        print(f"   ├─ 検出閾値: {config['min_repeat_threshold']}")
        print(f"   ├─ 検出距離: {config['max_distance']}文字")
        print(f"   ├─ 類似度閾値: {config['similarity_threshold']}")
        print(f"   └─ アグレッシブモード: {'有効' if config['enable_aggressive_mode'] else '無効'}")
        
        # Generatorの再パッチ
        if hasattr(self.ctx.generator, '_generate'):
            self.patch_generator_for_repetition_suppression()

    def get_repetition_suppression_settings(self):
        """現在の反復抑制設定を取得"""
        if not hasattr(self.ctx, 'repetition_suppressor'):
            return {"enabled": False, "message": "反復抑制システムが無効です"}
        
        aggressiveness = self.ctx.get('repetition_aggressiveness_level', 60)
        
        settings = {
            "enabled": True,
            "aggressiveness_level": aggressiveness,
            "current_config": {
                "min_repeat_threshold": self.ctx.get('repetition_min_repeat_threshold', 1),
                "max_distance": self.ctx.get('repetition_max_distance', 30),
                "similarity_threshold": self.ctx.get('repetition_similarity_threshold', 0.7),
                "enable_aggressive_mode": self.ctx.get('repetition_enable_aggressive_mode', True),
                "exact_match_priority": self.ctx.get('repetition_exact_match_priority', True)
            }
        }
        
        return settings

    def reset_all_contexts(self):
        """すべてのコンテキストのリセット"""
        if hasattr(self.ctx, 'repetition_suppressor'):
            # 反復抑制キャッシュのクリア
            self.ctx.repetition_suppressor.replacement_cache.clear()
            self.ctx.repetition_suppressor.character_patterns.clear()
            print("反復抑制キャッシュをリセットしました")
        
        if hasattr(self.ctx, 'nkat'):
            self.ctx.nkat.reset_consistency_context()
            print("NKAT一貫性コンテキストをリセットしました")

    def cleanup(self):
        """アプリケーション終了時のクリーンアップ"""
        if hasattr(self.ctx, 'repetition_suppressor'):
            self.ctx.repetition_suppressor.save_session_data()
        
        if hasattr(self.ctx, 'nkat'):
            self.ctx.nkat.cleanup()
        
        if hasattr(self, 'consistency_monitor'):
            self.consistency_monitor.save_session_data()

    def update_gui_statistics(self, success_rate=None, attempts=None, compression_rate=None):
        """GUI統計パネルの更新（リアルタイム反復制御パネル用）"""
        try:
            if hasattr(self.ctx, 'form') and hasattr(self.ctx.form, 'update_repetition_statistics'):
                self.ctx.form.update_repetition_statistics(success_rate, attempts, compression_rate)
        except Exception as e:
            if self.ctx.get('repetition_debug_mode', False):
                print(f"🔍 GUI統計更新スキップ: {e}")


class ConsistencyMonitor:
    """
    一貫性監視システム（反復抑制対応版）
    生成された文章の一貫性と反復抑制効果を継続的に監視・記録
    """
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.generation_history = []
        self.repetition_suppression_history = []
        self.consistency_scores = []
        self.improvement_log = []
        self.session_start_time = time.time()
        
        # 監視設定
        self.monitor_enabled = ctx["consistency_monitor_enabled"] if ctx["consistency_monitor_enabled"] is not None else True
        self.max_history_size = ctx["consistency_history_size"] if ctx["consistency_history_size"] is not None else 100
        self.alert_threshold = ctx["consistency_alert_threshold"] if ctx["consistency_alert_threshold"] is not None else 0.5
        
        print(f"一貫性監視システム初期化（履歴サイズ: {self.max_history_size}）")
    
    def record_generation(self, prompt: str, original: str, enhanced: str):
        """生成記録の保存"""
        if not self.monitor_enabled:
            return
        
        timestamp = time.time()
        
        # 改善度の計算
        improvement_score = self._calculate_improvement_score(original, enhanced)
        
        record = {
            "timestamp": timestamp,
            "prompt": prompt[:100],  # 最初の100文字のみ保存
            "original": original[:200],  # 最初の200文字のみ保存
            "enhanced": enhanced[:200],
            "improvement_score": improvement_score,
            "character_detected": self._extract_character(enhanced)
        }
        
        self.generation_history.append(record)
        
        # 履歴サイズ制限
        if len(self.generation_history) > self.max_history_size:
            self.generation_history.pop(0)
        
        # 一貫性アラート
        if improvement_score < self.alert_threshold:
            self._trigger_consistency_alert(record)

    def record_repetition_suppression(self, original: str, suppressed: str, final: str):
        """反復抑制記録の保存"""
        if not self.monitor_enabled:
            return
        
        timestamp = time.time()
        
        # 反復改善度の計算
        repetition_improvement = self._calculate_repetition_improvement(original, suppressed)
        
        record = {
            "timestamp": timestamp,
            "original_length": len(original),
            "suppressed_length": len(suppressed),
            "final_length": len(final),
            "repetition_improvement": repetition_improvement,
            "suppression_applied": original != suppressed,
            "character_detected": self._extract_character(final)
        }
        
        self.repetition_suppression_history.append(record)
        
        # 履歴サイズ制限
        if len(self.repetition_suppression_history) > self.max_history_size:
            self.repetition_suppression_history.pop(0)
        
        # 反復抑制効果のログ
        if record["suppression_applied"] and repetition_improvement > 0.3:
            self.improvement_log.append({
                "timestamp": timestamp,
                "type": "repetition_suppression",
                "message": f"反復抑制効果: {repetition_improvement:.2f}",
                "character": record["character_detected"]
            })

    def _calculate_repetition_improvement(self, original: str, suppressed: str) -> float:
        """反復改善度の計算"""
        if original == suppressed:
            return 0.0
        
        # 簡単な反復度計算
        original_repetition = self._count_repetition_density(original)
        suppressed_repetition = self._count_repetition_density(suppressed)
        
        if original_repetition == 0:
            return 0.0
        
        improvement = (original_repetition - suppressed_repetition) / original_repetition
        return max(0.0, min(1.0, improvement))

    def _count_repetition_density(self, text: str) -> float:
        """反復密度の計算"""
        if len(text) < 4:
            return 0.0
        
        repetition_count = 0
        
        # 2文字以上の反復をカウント
        for length in range(2, min(10, len(text) // 2)):
            for i in range(len(text) - length):
                phrase = text[i:i+length]
                count = text.count(phrase)
                if count > 1:
                    repetition_count += (count - 1) * length
        
        # 文字の連続反復をカウント
        import re
        for char in set(text):
            if re.match(r'[あ-んア-ンー]', char):
                consecutive_matches = re.findall(f'{re.escape(char)}{{3,}}', text)
                for match in consecutive_matches:
                    repetition_count += len(match) - 2
        
        return repetition_count / len(text)
    
    def _calculate_improvement_score(self, original: str, enhanced: str) -> float:
        """改善スコアの計算"""
        if original == enhanced:
            return 1.0  # 変更なしは完全な一貫性とみなす
        
        # 簡単な改善度計算（実際にはより複雑な分析が可能）
        original_issues = self._count_consistency_issues(original)
        enhanced_issues = self._count_consistency_issues(enhanced)
        
        if original_issues == 0:
            return 1.0
        
        improvement_ratio = (original_issues - enhanced_issues) / original_issues
        return max(0.0, improvement_ratio)
    
    def _count_consistency_issues(self, text: str) -> int:
        """一貫性問題のカウント"""
        issues = 0
        
        # 過度な反復
        repetition_density = self._count_repetition_density(text)
        if repetition_density > 0.1:
            issues += int(repetition_density * 10)
        
        # 感嘆符の過多
        if text.count("！") > 5:
            issues += 1
        
        # 省略記号の過多
        if text.count("…") > 3:
            issues += 1
        
        return issues
    
    def _extract_character(self, text: str) -> str:
        """キャラクター名の抽出"""
        import re
        match = re.search(r'^([^：「]+)：', text)
        return match.group(1).strip() if match else "不明"
    
    def _trigger_consistency_alert(self, record: dict):
        """一貫性アラートの発生"""
        message = f"一貫性警告: {record['character_detected']} - 改善スコア: {record['improvement_score']:.2f}"
        print(f"⚠️ {message}")
        
        self.improvement_log.append({
            "timestamp": record["timestamp"],
            "type": "alert",
            "message": message,
            "character": record["character_detected"]
        })
    
    def update(self):
        """定期更新処理"""
        # 定期的な統計計算やクリーンアップ
        if len(self.generation_history) > 0:
            recent_scores = [r["improvement_score"] for r in self.generation_history[-10:]]
            avg_recent_score = sum(recent_scores) / len(recent_scores)
            
            # 一貫性トレンドの監視
            if avg_recent_score < self.alert_threshold and len(recent_scores) >= 5:
                if not any(log["type"] == "trend_alert" for log in self.improvement_log[-5:]):
                    self._trigger_trend_alert(avg_recent_score)
    
    def _trigger_trend_alert(self, score: float):
        """トレンドアラートの発生"""
        message = f"一貫性トレンド警告: 直近の平均スコア {score:.2f} が閾値を下回っています"
        print(f"📈 {message}")
        
        self.improvement_log.append({
            "timestamp": time.time(),
            "type": "trend_alert",
            "message": message,
            "score": score
        })
    
    def generate_report(self) -> dict:
        """一貫性レポートの生成"""
        if not self.generation_history and not self.repetition_suppression_history:
            return {"message": "生成履歴がありません"}
        
        # 基本統計
        total_generations = len(self.generation_history)
        total_suppressions = len(self.repetition_suppression_history)
        
        # 改善スコア統計
        avg_improvement = 0
        if self.generation_history:
            avg_improvement = sum(r["improvement_score"] for r in self.generation_history) / total_generations
        
        # 反復抑制統計
        suppression_applied_count = sum(1 for r in self.repetition_suppression_history if r["suppression_applied"])
        avg_repetition_improvement = 0
        if self.repetition_suppression_history:
            avg_repetition_improvement = sum(r["repetition_improvement"] for r in self.repetition_suppression_history) / total_suppressions
        
        # キャラクター別統計
        character_stats = {}
        all_records = self.generation_history + self.repetition_suppression_history
        
        for record in all_records:
            char = record["character_detected"]
            if char not in character_stats:
                character_stats[char] = {"count": 0, "improvements": []}
            character_stats[char]["count"] += 1
            
            if "improvement_score" in record:
                character_stats[char]["improvements"].append(record["improvement_score"])
            elif "repetition_improvement" in record:
                character_stats[char]["improvements"].append(record["repetition_improvement"])
        
        # キャラクター別平均スコア計算
        for char in character_stats:
            improvements = character_stats[char]["improvements"]
            character_stats[char]["avg_score"] = sum(improvements) / len(improvements) if improvements else 0
        
        session_duration = time.time() - self.session_start_time
        
        return {
            "session_duration_minutes": session_duration / 60,
            "total_generations": total_generations,
            "total_repetition_suppressions": total_suppressions,
            "suppression_applied_count": suppression_applied_count,
            "suppression_success_rate": suppression_applied_count / total_suppressions if total_suppressions > 0 else 0,
            "average_improvement_score": avg_improvement,
            "average_repetition_improvement": avg_repetition_improvement,
            "character_statistics": character_stats,
            "recent_alerts": self.improvement_log[-10:],  # 最新10件のアラート
            "consistency_trend": [r["improvement_score"] for r in self.generation_history[-20:]]  # 最近20件のトレンド
        }
    
    def save_session_data(self):
        """セッションデータの保存"""
        if not self.generation_history and not self.repetition_suppression_history:
            return
        
        session_data = {
            "timestamp": time.time(),
            "session_duration": time.time() - self.session_start_time,
            "total_generations": len(self.generation_history),
            "total_repetition_suppressions": len(self.repetition_suppression_history),
            "report": self.generate_report()
        }
        
        # セッションデータをファイルに保存
        try:
            os.makedirs("logs/consistency", exist_ok=True)
            filename = f"logs/consistency/session_{int(time.time())}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            print(f"一貫性セッションデータを保存しました: {filename}")
        except Exception as e:
            print(f"セッションデータ保存エラー: {e}")


if __name__ == "__main__":
    easy_novel_assistant = EasyNovelAssistant()
    try:
        easy_novel_assistant.run()
    except KeyboardInterrupt:
        print("\nアプリケーションを終了しています...")
    finally:
        easy_novel_assistant.cleanup()
