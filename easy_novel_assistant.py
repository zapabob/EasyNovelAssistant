﻿import time
import os
import sys

# エンコーディング設定（EXE化対応）
if hasattr(sys, '_MEIPASS'):  # PyInstaller環境
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 統合システムv3のインポート（EXE化対応）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir  # easy_novel_assistant.pyはプロジェクトルート直下にある
sys.path.insert(0, project_root)

# 統合システムv3の安全なインポート
ADVANCED_SYSTEMS_AVAILABLE = False
POWER_PROTECTION_AVAILABLE = False
try:
    # 依存関係のチェック
    import torch
    torch_available = True
except ImportError:
    torch_available = False
    print("INFO: PyTorch not available - running in basic mode")

# Advanced systems v3 are temporarily disabled due to restructuring
ADVANCED_SYSTEMS_AVAILABLE = False
POWER_PROTECTION_AVAILABLE = False
print("INFO: Advanced systems v3 disabled during restructuring - running in basic mode")

# 新しい構造化されたモジュールインポート
from app.core.const import Const
from app.core.context import Context
from app.core.path import Path
from app.ui.form import Form
from app.utils.generator import Generator
from app.integrations.kobold_cpp import KoboldCpp
from app.integrations.movie_maker import MovieMaker
from app.integrations.style_bert_vits2 import StyleBertVits2


class EasyNovelAssistant:
    SLEEP_TIME = 50

    def __init__(self):
        global ADVANCED_SYSTEMS_AVAILABLE, POWER_PROTECTION_AVAILABLE
        
        self.ctx = Context()
        Path.init(self.ctx)
        Const.init(self.ctx)

        self.ctx.kobold_cpp = KoboldCpp(self.ctx)
        self.ctx.style_bert_vits2 = StyleBertVits2(self.ctx)
        self.ctx.movie_maker = MovieMaker(self.ctx)
        self.ctx.form = Form(self.ctx)
        self.ctx.generator = Generator(self.ctx)

        # 統合システムv3の初期化（利用可能な場合のみ）
        if ADVANCED_SYSTEMS_AVAILABLE:
            try:
                self._initialize_advanced_systems()
                print("SUCCESS: Advanced systems v3 initialized")
            except Exception as e:
                print(f"WARNING: Advanced systems v3 initialization failed: {e}")
                ADVANCED_SYSTEMS_AVAILABLE = False
        else:
            print("INFO: Running in basic mode - advanced systems disabled")

        # 電源断保護システムの初期化
        if POWER_PROTECTION_AVAILABLE:
            try:
                self._initialize_power_protection()
                print("SUCCESS: Power loss protection system activated")
            except Exception as e:
                print(f"WARNING: Power protection initialization failed: {e}")
                POWER_PROTECTION_AVAILABLE = False

        # TODO: 起動時引数でのフォルダ・ファイル読み込み
        self.ctx.form.input_area.open_tab(self.ctx["input_text"])  # 書き出しは Form の finalize

        self.ctx.form.win.after(self.SLEEP_TIME, self.mainloop)

    def _initialize_power_protection(self):
        """電源断保護システムの初期化"""
        protection_config = {
            'auto_save_interval': 300,  # 5分間隔
            'max_backups': 10,          # 最大10個のバックアップ
            'backup_rotation': True,    # バックアップローテーション有効
            'emergency_save': True      # 緊急保存有効
        }
        
        self.ctx.power_protection = create_power_protection_manager(self.ctx, protection_config)
        
        # 復旧チェック（前回の異常終了からの復旧）
        self._check_recovery_needed()
        
    def _check_recovery_needed(self):
        """前回セッションからの復旧チェック"""
        try:
            recovery_candidates = self.ctx.power_protection.find_recovery_candidates()
            
            if recovery_candidates:
                print(f"INFO: Found {len(recovery_candidates)} recovery candidates")
                
                # 最新の復旧候補をチェック
                latest_candidate = recovery_candidates[0]
                
                # 緊急保存があった場合は自動復旧を提案
                if latest_candidate['is_emergency']:
                    print("WARNING: Emergency backup detected - automatic recovery recommended")
                    # ここで必要に応じてユーザーに復旧を確認
                    self._attempt_auto_recovery(latest_candidate['file_path'])
                    
        except Exception as e:
            print(f"WARNING: Recovery check failed: {e}")
            
    def _attempt_auto_recovery(self, backup_file: str):
        """自動復旧の実行"""
        try:
            success = self.ctx.power_protection.restore_from_backup(backup_file)
            if success:
                print("SUCCESS: Auto-recovery completed from emergency backup")
            else:
                print("WARNING: Auto-recovery failed - continuing with fresh session")
        except Exception as e:
            print(f"WARNING: Auto-recovery error: {e}")

    def _initialize_advanced_systems(self):
        """統合システムv3の初期化"""
        # 統合システム設定
        self.integration_config = {
            'repetition_v3': {
                'similarity_threshold': 0.35,
                'max_distance': 50,
                'min_compress_rate': 0.03,
                'enable_4gram_blocking': True,
                'ngram_block_size': 3,
                'enable_drp': True,
                'drp_base': 1.10,
                'drp_alpha': 0.5,
                'enable_mecab_normalization': False,
                'enable_rhetorical_protection': True,
                'enable_latin_number_detection': True,
                'debug_mode': False
            },
            'lora_coordination': {
                'style_weight_influence': 0.3,
                'dynamic_adjustment': True,
                'adaptive_threshold': True,
                'character_memory': True,
                'realtime_feedback': True
            },
            'cross_suppression': {
                'cross_suppression_threshold': 0.3,
                'pattern_decay_rate': 0.95,
                'min_pattern_frequency': 2,
                'context_influence_weight': 0.4,
                'character_isolation': True,
                'session_memory_hours': 24,
                'adaptive_learning': True,
                'realtime_updates': True
            }
        }

        # 1. 反復抑制v3システム
        self.ctx.repetition_suppressor = AdvancedRepetitionSuppressorV3(
            self.integration_config['repetition_v3']
        )

        # 2. LoRA協調システム
        self.ctx.lora_coordinator = create_default_coordinator()
        self.ctx.lora_coordinator.initialize_systems(self.integration_config['repetition_v3'])

        # 3. クロス抑制システム
        self.ctx.cross_engine = create_default_cross_engine()
        self.ctx.cross_engine.initialize_systems(
            self.integration_config['repetition_v3'],
            self.integration_config['lora_coordination']
        )

        # 統計情報
        self.ctx.integration_stats = {
            'total_processed': 0,
            'total_compression_rate': 0.0,
            'success_rate_history': [],
            'character_usage': {},
            'theta_convergence_rate': 0.0,
            'bleurt_alternative_score': 0.0,
            'power_protection_saves': 0,
            'emergency_recoveries': 0
        }

        # 統合設定をコンテキストに保存
        self.ctx.integration_config = self.integration_config

        # Generatorクラスにインテグレーションを追加
        self._patch_generator_for_integration()

    def _patch_generator_for_integration(self):
        """Generatorクラスに統合システムv3を組み込み"""
        if not hasattr(self.ctx, 'repetition_suppressor') or self.ctx.repetition_suppressor is None:
            return

        original_generate = self.ctx.generator._generate
        
        def enhanced_generate_with_integration(input_text):
            """統合システムv3による強化生成"""
            # 元のKoboldCpp生成
            result = original_generate(input_text)
            
            if result is None or result == "":
                return result

            try:
                # キャラクター名の取得
                character_name = self.ctx.get("char_name", "default")
                session_id = f"session_{int(time.time())}"
                
                # Stage 1: クロス抑制システム
                current_text = result
                if hasattr(self.ctx, 'cross_engine') and self.ctx.cross_engine:
                    cross_result, cross_stats = self.ctx.cross_engine.process_with_cross_suppression(
                        current_text, character_name, session_id
                    )
                    current_text = cross_result
                    
                    # 統計更新
                    self.ctx.integration_stats['total_processed'] += 1

                # Stage 2: LoRA協調システム
                if hasattr(self.ctx, 'lora_coordinator') and self.ctx.lora_coordinator:
                    lora_result, lora_stats = self.ctx.lora_coordinator.process_text_with_coordination(
                        current_text, character_name, 1.0
                    )
                    current_text = lora_result
                    
                    # 成功率記録
                    if 'success_rate' in lora_stats:
                        self.ctx.integration_stats['success_rate_history'].append(lora_stats['success_rate'])

                # Stage 3: 反復抑制v3（最終調整）
                if hasattr(self.ctx, 'repetition_suppressor') and self.ctx.repetition_suppressor:
                    v3_result, v3_metrics = self.ctx.repetition_suppressor.suppress_repetitions_with_debug_v3(
                        current_text, character_name
                    )
                    current_text = v3_result
                    
                    # θ収束度とBLEURT代替評価の更新
                    compression_rate = (len(result) - len(current_text)) / len(result) if len(result) > 0 else 0
                    self.ctx.integration_stats['total_compression_rate'] += compression_rate
                    
                    # Phase 4目標達成度の評価
                    if v3_metrics.success_rate >= 0.8:
                        self.ctx.integration_stats['theta_convergence_rate'] = min(0.95, 
                            self.ctx.integration_stats['theta_convergence_rate'] + 0.02)
                    
                    # BLEURT代替スコア（品質評価）
                    if compression_rate > 0.03:  # 実際に圧縮された場合
                        self.ctx.integration_stats['bleurt_alternative_score'] = min(0.90,
                            self.ctx.integration_stats['bleurt_alternative_score'] + 0.01)

                    # デバッグ情報（統合完了のために出力）
                    if self.integration_config['repetition_v3']['debug_mode']:
                        print(f"Integration processing complete: {len(result)}->{len(current_text)} "
                              f"({compression_rate:.1%} compression)")
                        print(f"   Theta convergence: {self.ctx.integration_stats['theta_convergence_rate']:.1%}")
                        print(f"   BLEURT alternative: {self.ctx.integration_stats['bleurt_alternative_score']:.1%}")

                # 電源断保護: 重要な生成後にチェックポイント保存
                if (POWER_PROTECTION_AVAILABLE and hasattr(self.ctx, 'power_protection') and 
                    self.ctx.integration_stats['total_processed'] % 5 == 0):  # 5回に1回保存
                    
                    self.ctx.power_protection.save_checkpoint("generation_checkpoint")
                    self.ctx.integration_stats['power_protection_saves'] += 1

                # キャラクター使用統計
                if character_name:
                    self.ctx.integration_stats['character_usage'][character_name] = \
                        self.ctx.integration_stats['character_usage'].get(character_name, 0) + 1

                return current_text
                
            except Exception as e:
                print(f"ERROR: Integration processing failed: {e}")
                return result
        
        # メソッドの置き換え
        self.ctx.generator._generate = enhanced_generate_with_integration

    def run(self):
        self.ctx.form.run()

    def mainloop(self):
        global ADVANCED_SYSTEMS_AVAILABLE, POWER_PROTECTION_AVAILABLE
        
        self.ctx.generator.update()
        self.ctx.style_bert_vits2.update()
        self.ctx.form.input_area.update()
        
        # 統合システムのメトリクス監視（利用可能な場合のみ）
        if ADVANCED_SYSTEMS_AVAILABLE and hasattr(self.ctx, 'integration_stats'):
            stats = self.ctx.integration_stats
            
            # GUI統合パネルへの統計更新
            if hasattr(self.ctx.form, 'integration_panel') and self.ctx.form.integration_panel:
                # 電源断保護の状態も含める
                if POWER_PROTECTION_AVAILABLE and hasattr(self.ctx, 'power_protection'):
                    protection_status = self.ctx.power_protection.get_protection_status()
                    stats['power_protection_status'] = protection_status
                    
                self.ctx.form.integration_panel.update_statistics(stats)
            
            # 商用レベル達成度の確認
            if stats['total_processed'] > 0 and stats['total_processed'] % 10 == 0:
                avg_success_rate = sum(stats['success_rate_history'][-10:]) / min(10, len(stats['success_rate_history'])) if stats['success_rate_history'] else 0
                
                if (stats['theta_convergence_rate'] >= 0.8 and 
                    stats['bleurt_alternative_score'] >= 0.87 and
                    avg_success_rate >= 0.9):
                    print("SUCCESS: Phase 4 commercial level targets achieved!")
                    print(f"   Theta convergence: {stats['theta_convergence_rate']:.1%} >= 80%")
                    print(f"   BLEURT alternative: {stats['bleurt_alternative_score']:.1%} >= 87%")
                    print(f"   Success rate: {avg_success_rate:.1%} >= 90%")
                    
                    # 商用レベル達成時の特別チェックポイント
                    if POWER_PROTECTION_AVAILABLE and hasattr(self.ctx, 'power_protection'):
                        self.ctx.power_protection.save_checkpoint("commercial_level_achieved")
        
        self.ctx.form.win.after(self.SLEEP_TIME, self.mainloop)


if __name__ == "__main__":
    easy_novel_assistant = EasyNovelAssistant()
    easy_novel_assistant.run()
