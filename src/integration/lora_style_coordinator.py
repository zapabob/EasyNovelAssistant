# -*- coding: utf-8 -*-
"""
LoRA文体制御 × 反復抑制システム協調エンジン v1.0

【概要】
文体LoRA（Style-Bert-VITS2）と反復抑制v3システムの統合により、
キャラクター特有の口調を保持しながら反復パターンを抑制する。

【主要機能】
1. Style-VITSからのstyle_vectorとstyle_weightの取得
2. 反復抑制パラメータへのスタイル重み反映
3. キャラクター別の最適化設定プリセット
4. リアルタイム協調制御

Author: EasyNovelAssistant Development Team
Date: 2025-01-06
"""

import os
import sys
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
src_dir = os.path.join(project_root, "src")
sys.path.insert(0, project_root)
sys.path.insert(0, src_dir)

try:
    from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
    V3_AVAILABLE = True
except ImportError:
    try:
        # 直接パスでも試行
        sys.path.insert(0, os.path.join(project_root, "src", "utils"))
        from repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
        V3_AVAILABLE = True
    except ImportError:
        V3_AVAILABLE = False
        logging.warning("反復抑制v3システムが見つかりません")

# Style-Bert-VITS2の統合試行
try:
    style_vits_path = os.path.join(project_root, "Style-Bert-VITS2", "style_bert_vits2")
    sys.path.insert(0, style_vits_path)
    from style_bert_vits2.tts_model import TTSModel
    from style_bert_vits2.constants import Languages
    STYLE_VITS_AVAILABLE = True
except ImportError:
    STYLE_VITS_AVAILABLE = False
    logging.warning("Style-Bert-VITS2システムが見つかりません")


class CharacterStyleProfile:
    """キャラクター文体プロファイル"""
    
    def __init__(self, name: str, style_vector: np.ndarray, 
                 repetition_config: Dict[str, Any]):
        self.name = name
        self.style_vector = style_vector  # 256次元のスタイルベクトル
        self.repetition_config = repetition_config
        self.usage_count = 0
        self.success_rate_history = []
    
    def update_success_rate(self, rate: float):
        """成功率履歴の更新"""
        self.success_rate_history.append(rate)
        if len(self.success_rate_history) > 100:  # 最新100件を保持
            self.success_rate_history.pop(0)
    
    def get_average_success_rate(self) -> float:
        """平均成功率の取得"""
        if not self.success_rate_history:
            return 0.0
        return sum(self.success_rate_history) / len(self.success_rate_history)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式への変換"""
        return {
            'name': self.name,
            'style_vector': self.style_vector.tolist(),
            'repetition_config': self.repetition_config,
            'usage_count': self.usage_count,
            'success_rate_history': self.success_rate_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterStyleProfile':
        """辞書からの復元"""
        profile = cls(
            name=data['name'],
            style_vector=np.array(data['style_vector']),
            repetition_config=data['repetition_config']
        )
        profile.usage_count = data.get('usage_count', 0)
        profile.success_rate_history = data.get('success_rate_history', [])
        return profile


class LoRAStyleCoordinator:
    """LoRA文体制御×反復抑制協調システム"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path or "config/lora_style_coordination.json"
        self.logger = logging.getLogger(__name__)
        
        # システムコンポーネント
        self.repetition_suppressor: Optional[AdvancedRepetitionSuppressorV3] = None
        self.tts_model: Optional[TTSModel] = None
        
        # キャラクタープロファイル管理
        self.character_profiles: Dict[str, CharacterStyleProfile] = {}
        self.current_character: Optional[str] = None
        
        # 協調設定
        self.coordination_config = {
            'style_weight_influence': 0.3,  # スタイル重みの反復抑制への影響度
            'dynamic_adjustment': True,     # 動的調整の有効化
            'adaptive_threshold': True,     # 適応的閾値調整
            'character_memory': True,       # キャラクター別設定記憶
            'realtime_feedback': True       # リアルタイムフィードバック
        }
        
        # 初期化
        self._load_configuration()
        self._initialize_default_profiles()
        
        self.logger.info("🚀 LoRA文体協調システム初期化完了")
    
    def _load_configuration(self):
        """設定ファイルの読み込み"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.coordination_config.update(config.get('coordination', {}))
                
                # キャラクタープロファイルの復元
                for name, data in config.get('character_profiles', {}).items():
                    self.character_profiles[name] = CharacterStyleProfile.from_dict(data)
                
                self.logger.info(f"✅ 設定ファイル読み込み完了: {len(self.character_profiles)}キャラクター")
        except Exception as e:
            self.logger.warning(f"設定ファイル読み込み失敗: {e}")
    
    def _save_configuration(self):
        """設定ファイルの保存"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            config = {
                'coordination': self.coordination_config,
                'character_profiles': {
                    name: profile.to_dict() 
                    for name, profile in self.character_profiles.items()
                }
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info("💾 設定ファイル保存完了")
        except Exception as e:
            self.logger.error(f"設定ファイル保存失敗: {e}")
    
    def _initialize_default_profiles(self):
        """デフォルトキャラクタープロファイルの初期化"""
        if not self.character_profiles:
            # デフォルトプロファイル
            default_profiles = [
                {
                    'name': '標準',
                    'style_vector': np.zeros(256),  # ニュートラル
                    'repetition_config': {
                        'similarity_threshold': 0.35,
                        'max_distance': 50,
                        'min_compress_rate': 0.03,
                        'enable_rhetorical_protection': False
                    }
                },
                {
                    'name': '関西弁キャラ',
                    'style_vector': np.random.normal(0, 0.1, 256),  # サンプル
                    'repetition_config': {
                        'similarity_threshold': 0.40,  # 方言特有の表現を保護
                        'max_distance': 60,
                        'min_compress_rate': 0.02,
                        'enable_rhetorical_protection': True
                    }
                },
                {
                    'name': '丁寧語キャラ',
                    'style_vector': np.random.normal(0, 0.1, 256),
                    'repetition_config': {
                        'similarity_threshold': 0.30,
                        'max_distance': 40,
                        'min_compress_rate': 0.04,
                        'enable_rhetorical_protection': False
                    }
                },
                {
                    'name': '感情豊かキャラ',
                    'style_vector': np.random.normal(0, 0.15, 256),
                    'repetition_config': {
                        'similarity_threshold': 0.45,  # 感嘆詞を多めに保護
                        'max_distance': 80,
                        'min_compress_rate': 0.01,
                        'enable_rhetorical_protection': True
                    }
                }
            ]
            
            for profile_data in default_profiles:
                profile = CharacterStyleProfile(
                    name=profile_data['name'],
                    style_vector=profile_data['style_vector'],
                    repetition_config=profile_data['repetition_config']
                )
                self.character_profiles[profile.name] = profile
            
            self.logger.info(f"📝 デフォルトプロファイル作成: {len(default_profiles)}種類")
    
    def initialize_systems(self, repetition_config: Optional[Dict] = None):
        """システムコンポーネントの初期化"""
        # 反復抑制システム初期化
        if V3_AVAILABLE:
            config = repetition_config or {
                'similarity_threshold': 0.35,
                'max_distance': 50,
                'min_compress_rate': 0.03,
                'enable_4gram_blocking': True,
                'ngram_block_size': 3,
                'enable_drp': True,
                'drp_base': 1.10,
                'drp_alpha': 0.5,
                'enable_mecab_normalization': False,
                'enable_rhetorical_protection': False,
                'enable_latin_number_detection': True,
                'debug_mode': True
            }
            self.repetition_suppressor = AdvancedRepetitionSuppressorV3(config)
            self.logger.info("✅ 反復抑制v3システム初期化完了")
        
        # Style-Bert-VITS2システム初期化（今後実装）
        if STYLE_VITS_AVAILABLE:
            # TTSモデルの初期化は重いので、必要時に遅延初期化
            self.logger.info("✅ Style-Bert-VITS2システム利用可能")
        
        return self.repetition_suppressor is not None
    
    def set_character(self, character_name: str, 
                      style_vector: Optional[np.ndarray] = None,
                      style_weight: float = 1.0) -> bool:
        """
        キャラクターの設定と切り替え
        
        Args:
            character_name: キャラクター名
            style_vector: スタイルベクトル（256次元）
            style_weight: スタイル重み（0.0-2.0）
        
        Returns:
            bool: 設定成功可否
        """
        try:
            if character_name not in self.character_profiles:
                # 新キャラクターの場合、デフォルト設定で作成
                if style_vector is None:
                    style_vector = np.zeros(256)
                
                profile = CharacterStyleProfile(
                    name=character_name,
                    style_vector=style_vector,
                    repetition_config=self.character_profiles['標準'].repetition_config.copy()
                )
                self.character_profiles[character_name] = profile
                self.logger.info(f"🆕 新キャラクター作成: {character_name}")
            
            self.current_character = character_name
            current_profile = self.character_profiles[character_name]
            
            # 反復抑制設定の動的調整
            if self.repetition_suppressor and self.coordination_config['dynamic_adjustment']:
                adjusted_config = self._calculate_adjusted_config(
                    current_profile, style_weight
                )
                self.repetition_suppressor.update_config(adjusted_config)
                
                self.logger.info(f"🔄 {character_name}の設定適用完了")
                self.logger.debug(f"   調整後設定: {adjusted_config}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"キャラクター設定エラー: {e}")
            return False
    
    def _calculate_adjusted_config(self, profile: CharacterStyleProfile, 
                                  style_weight: float) -> Dict[str, Any]:
        """
        スタイル重みを考慮した反復抑制設定の計算
        
        Args:
            profile: キャラクタープロファイル
            style_weight: スタイル重み
        
        Returns:
            Dict: 調整済み設定
        """
        base_config = profile.repetition_config.copy()
        influence = self.coordination_config['style_weight_influence']
        
        # スタイル重みに基づく調整
        style_factor = 1.0 + (style_weight - 1.0) * influence
        
        adjusted_config = base_config.copy()
        
        # 類似度閾値の調整: スタイル重みが高いほど緩く（文体保護）
        adjusted_config['similarity_threshold'] = min(0.8, 
            base_config['similarity_threshold'] * style_factor
        )
        
        # 最小圧縮率の調整: スタイル重みが高いほど低く（文体保護）
        adjusted_config['min_compress_rate'] = max(0.01,
            base_config['min_compress_rate'] / style_factor
        )
        
        # スタイルベクトルの分析による追加調整
        style_intensity = np.linalg.norm(profile.style_vector)
        if style_intensity > 0.5:  # 特徴的なスタイル
            adjusted_config['enable_rhetorical_protection'] = True
            adjusted_config['max_distance'] = int(base_config['max_distance'] * 1.2)
        
        return adjusted_config
    
    def process_text_with_coordination(self, text: str, 
                                     character_name: Optional[str] = None,
                                     style_weight: float = 1.0) -> Tuple[str, Dict[str, Any]]:
        """
        協調システムによるテキスト処理
        
        Args:
            text: 入力テキスト
            character_name: キャラクター名
            style_weight: スタイル重み
        
        Returns:
            Tuple[str, Dict]: 処理済みテキストと統計情報
        """
        if character_name and character_name != self.current_character:
            self.set_character(character_name, style_weight=style_weight)
        
        if not self.repetition_suppressor:
            self.logger.warning("反復抑制システムが初期化されていません")
            return text, {}
        
        try:
            # 反復抑制処理
            result_text, metrics = self.repetition_suppressor.suppress_repetitions_with_debug_v3(
                text, character_name or self.current_character
            )
            
            # 統計情報の更新
            if self.current_character and self.coordination_config['character_memory']:
                profile = self.character_profiles[self.current_character]
                profile.update_success_rate(metrics.success_rate)
                profile.usage_count += 1
            
            # 協調統計の作成
            coordination_stats = {
                'original_length': len(text),
                'processed_length': len(result_text),
                'compression_rate': (len(text) - len(result_text)) / len(text),
                'success_rate': metrics.success_rate,
                'character': self.current_character,
                'style_weight': style_weight,
                'patterns_detected': metrics.patterns_detected,
                'patterns_suppressed': metrics.patterns_suppressed,
                'v3_features_used': {
                    'ngram_blocks': getattr(metrics, 'ngram_blocks_applied', 0),
                    'rhetorical_exceptions': getattr(metrics, 'rhetorical_exceptions', 0),
                    'latin_blocks': getattr(metrics, 'latin_number_blocks', 0)
                }
            }
            
            # フィードバック学習（将来実装）
            if self.coordination_config['realtime_feedback']:
                self._process_feedback(coordination_stats)
            
            return result_text, coordination_stats
        
        except Exception as e:
            self.logger.error(f"協調処理エラー: {e}")
            return text, {'error': str(e)}
    
    def _process_feedback(self, stats: Dict[str, Any]):
        """リアルタイムフィードバック処理（将来実装）"""
        # 成功率が低い場合の自動調整ロジック
        if stats['success_rate'] < 0.7 and self.current_character:
            # 設定の微調整を実施
            pass
    
    def get_character_list(self) -> List[str]:
        """キャラクター一覧の取得"""
        return list(self.character_profiles.keys())
    
    def get_character_stats(self, character_name: str) -> Optional[Dict[str, Any]]:
        """キャラクター統計の取得"""
        if character_name not in self.character_profiles:
            return None
        
        profile = self.character_profiles[character_name]
        return {
            'name': profile.name,
            'usage_count': profile.usage_count,
            'average_success_rate': profile.get_average_success_rate(),
            'recent_success_rate': profile.success_rate_history[-10:] if profile.success_rate_history else [],
            'style_intensity': float(np.linalg.norm(profile.style_vector)),
            'config': profile.repetition_config
        }
    
    def export_character_profile(self, character_name: str, filepath: str) -> bool:
        """キャラクタープロファイルのエクスポート"""
        if character_name not in self.character_profiles:
            return False
        
        try:
            profile_data = self.character_profiles[character_name].to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"プロファイルエクスポート失敗: {e}")
            return False
    
    def import_character_profile(self, filepath: str) -> Optional[str]:
        """キャラクタープロファイルのインポート"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            profile = CharacterStyleProfile.from_dict(profile_data)
            self.character_profiles[profile.name] = profile
            return profile.name
        except Exception as e:
            self.logger.error(f"プロファイルインポート失敗: {e}")
            return None
    
    def save_state(self):
        """状態の保存"""
        self._save_configuration()
    
    def get_coordination_status(self) -> Dict[str, Any]:
        """協調システムの状態取得"""
        return {
            'repetition_suppressor_available': self.repetition_suppressor is not None,
            'style_vits_available': STYLE_VITS_AVAILABLE,
            'current_character': self.current_character,
            'character_count': len(self.character_profiles),
            'coordination_config': self.coordination_config,
            'total_usage': sum(p.usage_count for p in self.character_profiles.values())
        }


def create_default_coordinator() -> LoRAStyleCoordinator:
    """デフォルト協調システムの作成"""
    coordinator = LoRAStyleCoordinator()
    coordinator.initialize_systems()
    return coordinator


if __name__ == "__main__":
    # デモ実行
    logging.basicConfig(level=logging.INFO)
    
    print("🎯 LoRA文体協調システム デモ")
    print("=" * 50)
    
    coordinator = create_default_coordinator()
    
    # キャラクター設定
    coordinator.set_character("関西弁キャラ", style_weight=1.5)
    
    # テスト処理
    test_text = "そやそやそや、あかんあかんあかん、やなやなそれは。"
    result, stats = coordinator.process_text_with_coordination(test_text)
    
    print(f"入力: {test_text}")
    print(f"出力: {result}")
    print(f"統計: {stats}")
    
    # 状態確認
    status = coordinator.get_coordination_status()
    print(f"\n協調システム状態: {status}")
    
    coordinator.save_state()
    print("\n✅ デモ完了") 