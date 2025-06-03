# -*- coding: utf-8 -*-
"""
NKAT理論統合準備システム v3.0 (NKAT Theory Integration Preparation v3.0)
理論的フレームワーク・感情表現エンジン・動的パラメータ調整・統合準備

主要機能:
1. NKAT理論フレームワーク実装
2. 感情表現エンジン統合
3. 動的パラメータ調整システム
4. リアルタイム協調制御統合
5. メモリ効率化連携
6. 性能最適化・監視システム
"""

import time
import threading
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
from enum import Enum, auto

# プロジェクト内モジュール統合
try:
    from ..integration.realtime_coordination_controller_v3 import RealtimeCoordinationControllerV3, TaskPriority
    from ..optimization.memory_efficiency_system_v3 import MemoryEfficiencySystemV3
    from ..utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
except ImportError:
    # フォールバック
    RealtimeCoordinationControllerV3 = None
    MemoryEfficiencySystemV3 = None
    AdvancedRepetitionSuppressorV3 = None


class NKATEmotionType(Enum):
    """NKAT感情タイプ"""
    JOY = auto()           # 喜び
    SADNESS = auto()       # 悲しみ
    ANGER = auto()         # 怒り
    FEAR = auto()          # 恐れ
    SURPRISE = auto()      # 驚き
    DISGUST = auto()       # 嫌悪
    LOVE = auto()          # 愛情
    NOSTALGIA = auto()     # 懐かしさ
    MELANCHOLY = auto()    # 憂鬱
    EXCITEMENT = auto()    # 興奮


class NKATCharacterArchetype(Enum):
    """NKATキャラクター原型"""
    INNOCENT = auto()      # 純真
    SAGE = auto()          # 賢者
    EXPLORER = auto()      # 探検家
    HERO = auto()          # 英雄
    OUTLAW = auto()        # 反逆者
    MAGICIAN = auto()      # 魔術師
    EVERYMAN = auto()      # 普通の人
    LOVER = auto()         # 恋人
    JESTER = auto()        # 道化師
    CAREGIVER = auto()     # 世話人
    RULER = auto()         # 支配者
    CREATOR = auto()       # 創造者


@dataclass
class NKATEmotionVector:
    """NKAT感情ベクトル"""
    primary_emotion: NKATEmotionType
    intensity: float  # 0.0-1.0
    secondary_emotions: Dict[NKATEmotionType, float] = field(default_factory=dict)
    temporal_decay: float = 0.95  # 時間減衰率
    contextual_modifiers: Dict[str, float] = field(default_factory=dict)


@dataclass
class NKATCharacterProfile:
    """NKATキャラクタープロファイル"""
    character_id: str
    archetype: NKATCharacterArchetype
    base_emotions: Dict[NKATEmotionType, float]
    personality_traits: Dict[str, float]
    speech_patterns: Dict[str, Any]
    memory_associations: Dict[str, List[str]]
    adaptation_rate: float = 0.1
    emotional_stability: float = 0.8


@dataclass
class NKATContext:
    """NKAT文脈情報"""
    scene_setting: str
    relationship_dynamics: Dict[str, float]
    emotional_atmosphere: NKATEmotionVector
    narrative_tension: float
    temporal_context: Dict[str, Any]
    cultural_context: Dict[str, Any]


class NKATTheoryIntegrationPreparationV3:
    """
    NKAT理論統合準備システム v3.0
    感情表現・キャラクター理論・動的適応統合版
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 基本設定
        self.theory_enabled = self.config.get('theory_enabled', True)
        self.emotion_engine_enabled = self.config.get('emotion_engine_enabled', True)
        self.dynamic_adaptation_enabled = self.config.get('dynamic_adaptation_enabled', True)
        self.real_time_processing = self.config.get('real_time_processing', True)
        
        # NKAT理論パラメータ
        self.narrative_coherence_weight = self.config.get('narrative_coherence_weight', 0.7)
        self.character_consistency_weight = self.config.get('character_consistency_weight', 0.8)
        self.emotional_authenticity_weight = self.config.get('emotional_authenticity_weight', 0.6)
        self.temporal_continuity_weight = self.config.get('temporal_continuity_weight', 0.5)
        
        # 感情エンジン設定
        self.emotion_update_interval = self.config.get('emotion_update_interval', 0.5)
        self.emotion_memory_window = self.config.get('emotion_memory_window', 100)
        self.emotion_influence_radius = self.config.get('emotion_influence_radius', 0.3)
        
        # 動的適応設定
        self.adaptation_learning_rate = self.config.get('adaptation_learning_rate', 0.01)
        self.pattern_recognition_threshold = self.config.get('pattern_recognition_threshold', 0.8)
        self.feedback_integration_weight = self.config.get('feedback_integration_weight', 0.2)
        
        # 状態管理
        self.is_active = False
        self.character_profiles: Dict[str, NKATCharacterProfile] = {}
        self.emotion_history: deque = deque(maxlen=self.emotion_memory_window)
        self.context_stack: List[NKATContext] = []
        
        # 統合システム
        self.coordination_controller: Optional[RealtimeCoordinationControllerV3] = None
        self.memory_system: Optional[MemoryEfficiencySystemV3] = None
        self.repetition_suppressor: Optional[AdvancedRepetitionSuppressorV3] = None
        
        # 性能監視
        self.performance_metrics = {
            'emotion_processing_time': deque(maxlen=100),
            'adaptation_accuracy': deque(maxlen=100),
            'theory_coherence_score': deque(maxlen=100),
            'integration_success_rate': deque(maxlen=100)
        }
        
        # 学習データ
        self.learned_patterns: Dict[str, Any] = {}
        self.feedback_history: List[Dict[str, Any]] = []
        self.optimization_history: List[Dict[str, Any]] = []
        
        # ログ設定
        self.logger = self._setup_logging()
        
        # 初期化処理
        self._initialize_theory_framework()
        self._initialize_emotion_engine()
        self._initialize_character_archetypes()
        
        print(f"🧠 NKAT理論統合準備システム v3.0 初期化完了")
        print(f"   ├─ 理論フレームワーク: {'有効' if self.theory_enabled else '無効'}")
        print(f"   ├─ 感情エンジン: {'有効' if self.emotion_engine_enabled else '無効'}")
        print(f"   ├─ 動的適応: {'有効' if self.dynamic_adaptation_enabled else '無効'}")
        print(f"   └─ リアルタイム処理: {'有効' if self.real_time_processing else '無効'}")

    def _setup_logging(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger('NKATIntegrationV3')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def _initialize_theory_framework(self):
        """NKAT理論フレームワーク初期化"""
        
        # 基本理論パラメータ設定
        self.theory_parameters = {
            'narrative_layers': {
                'surface_narrative': {'weight': 0.3, 'complexity': 1.0},
                'character_development': {'weight': 0.4, 'complexity': 1.5},
                'thematic_resonance': {'weight': 0.2, 'complexity': 2.0},
                'meta_narrative': {'weight': 0.1, 'complexity': 3.0}
            },
            'emotional_dynamics': {
                'primary_emotion_strength': 1.0,
                'secondary_emotion_influence': 0.6,
                'emotional_transition_smoothness': 0.8,
                'contextual_emotion_modifier': 0.4
            },
            'character_consistency': {
                'archetype_adherence': 0.8,
                'personality_flexibility': 0.3,
                'growth_potential': 0.5,
                'contradiction_tolerance': 0.2
            }
        }
        
        # 理論的制約条件
        self.theory_constraints = {
            'max_emotion_intensity_change': 0.3,
            'min_character_consistency': 0.7,
            'max_narrative_complexity_delta': 0.5,
            'temporal_coherence_window': 10
        }
        
        self.logger.info("✅ NKAT理論フレームワーク初期化完了")

    def _initialize_emotion_engine(self):
        """感情エンジン初期化"""
        
        # 感情間の相関マトリクス
        self.emotion_correlation_matrix = {
            NKATEmotionType.JOY: {
                NKATEmotionType.LOVE: 0.8,
                NKATEmotionType.EXCITEMENT: 0.7,
                NKATEmotionType.SURPRISE: 0.5,
                NKATEmotionType.SADNESS: -0.6,
                NKATEmotionType.ANGER: -0.4
            },
            NKATEmotionType.SADNESS: {
                NKATEmotionType.NOSTALGIA: 0.6,
                NKATEmotionType.MELANCHOLY: 0.8,
                NKATEmotionType.FEAR: 0.4,
                NKATEmotionType.JOY: -0.6,
                NKATEmotionType.EXCITEMENT: -0.5
            },
            NKATEmotionType.ANGER: {
                NKATEmotionType.DISGUST: 0.5,
                NKATEmotionType.FEAR: 0.3,
                NKATEmotionType.JOY: -0.4,
                NKATEmotionType.LOVE: -0.7
            },
            # ... 他の感情の相関関係
        }
        
        # 感情遷移確率
        self.emotion_transition_probabilities = {}
        for emotion in NKATEmotionType:
            self.emotion_transition_probabilities[emotion] = {}
            for target_emotion in NKATEmotionType:
                if emotion == target_emotion:
                    self.emotion_transition_probabilities[emotion][target_emotion] = 0.7
                else:
                    correlation = self.emotion_correlation_matrix.get(emotion, {}).get(target_emotion, 0.0)
                    self.emotion_transition_probabilities[emotion][target_emotion] = max(0.1, 0.3 + correlation * 0.2)
        
        self.logger.info("✅ 感情エンジン初期化完了")

    def _initialize_character_archetypes(self):
        """キャラクター原型初期化"""
        
        # 原型別基本感情傾向
        self.archetype_emotion_tendencies = {
            NKATCharacterArchetype.INNOCENT: {
                NKATEmotionType.JOY: 0.8,
                NKATEmotionType.SURPRISE: 0.6,
                NKATEmotionType.FEAR: 0.4,
                NKATEmotionType.SADNESS: 0.3
            },
            NKATCharacterArchetype.HERO: {
                NKATEmotionType.ANGER: 0.6,
                NKATEmotionType.JOY: 0.5,
                NKATEmotionType.FEAR: 0.2,
                NKATEmotionType.LOVE: 0.7
            },
            NKATCharacterArchetype.SAGE: {
                NKATEmotionType.MELANCHOLY: 0.5,
                NKATEmotionType.NOSTALGIA: 0.6,
                NKATEmotionType.JOY: 0.4,
                NKATEmotionType.ANGER: 0.1
            },
            # ... 他の原型の感情傾向
        }
        
        # 原型別発話パターン
        self.archetype_speech_patterns = {
            NKATCharacterArchetype.INNOCENT: {
                'formality_level': 0.3,
                'emotional_expressiveness': 0.8,
                'complexity_preference': 0.2,
                'optimism_bias': 0.7
            },
            NKATCharacterArchetype.SAGE: {
                'formality_level': 0.8,
                'emotional_expressiveness': 0.4,
                'complexity_preference': 0.9,
                'optimism_bias': 0.3
            }
            # ... 他の原型の発話パターン
        }
        
        self.logger.info("✅ キャラクター原型初期化完了")

    async def integrate_with_systems(self, 
                                   coordination_controller: Optional[RealtimeCoordinationControllerV3] = None,
                                   memory_system: Optional[MemoryEfficiencySystemV3] = None,
                                   repetition_suppressor: Optional[AdvancedRepetitionSuppressorV3] = None):
        """統合システム連携"""
        
        self.coordination_controller = coordination_controller
        self.memory_system = memory_system
        self.repetition_suppressor = repetition_suppressor
        
        # 協調制御システム連携
        if self.coordination_controller:
            self.coordination_controller.register_system_callback(
                'nkat_processing', 
                self._handle_coordination_request
            )
        
        # メモリシステム連携
        if self.memory_system:
            self.memory_system.register_emergency_callback(self._handle_memory_emergency)
        
        self.logger.info("🔗 統合システム連携完了")

    def create_character_profile(self, 
                               character_id: str,
                               archetype: NKATCharacterArchetype,
                               custom_traits: Dict[str, float] = None) -> NKATCharacterProfile:
        """キャラクタープロファイル作成"""
        
        # 基本感情傾向取得
        base_emotions = self.archetype_emotion_tendencies.get(archetype, {}).copy()
        
        # カスタム特性適用
        if custom_traits:
            for emotion_type, intensity in custom_traits.items():
                if isinstance(emotion_type, str):
                    try:
                        emotion_type = NKATEmotionType[emotion_type.upper()]
                    except KeyError:
                        continue
                base_emotions[emotion_type] = intensity
        
        # 発話パターン取得
        speech_patterns = self.archetype_speech_patterns.get(archetype, {}).copy()
        
        # プロファイル作成
        profile = NKATCharacterProfile(
            character_id=character_id,
            archetype=archetype,
            base_emotions=base_emotions,
            personality_traits=custom_traits or {},
            speech_patterns=speech_patterns,
            memory_associations=defaultdict(list)
        )
        
        self.character_profiles[character_id] = profile
        self.logger.info(f"👤 キャラクタープロファイル作成: {character_id} ({archetype.name})")
        
        return profile

    async def process_text_with_nkat(self, 
                                   text: str,
                                   character_id: str,
                                   context: Optional[NKATContext] = None) -> Tuple[str, Dict[str, Any]]:
        """NKATテキスト処理"""
        
        start_time = time.time()
        
        try:
            # キャラクタープロファイル取得
            if character_id not in self.character_profiles:
                self.logger.warning(f"未知のキャラクター: {character_id}")
                return text, {'error': 'unknown_character'}
            
            profile = self.character_profiles[character_id]
            
            # 文脈分析
            if context is None:
                context = await self._analyze_context(text, profile)
            
            # 感情状態更新
            current_emotion = await self._update_character_emotion(profile, context, text)
            
            # NKAT理論適用
            processed_text = await self._apply_nkat_theory(text, profile, current_emotion, context)
            
            # 反復抑制統合
            if self.repetition_suppressor:
                processed_text, suppression_info = self.repetition_suppressor.suppress_repetitions_with_debug_v3(
                    processed_text, character_id
                )
            else:
                suppression_info = {}
            
            # パフォーマンス記録
            processing_time = time.time() - start_time
            self.performance_metrics['emotion_processing_time'].append(processing_time)
            
            # 結果統計
            result_info = {
                'processing_time': processing_time,
                'character_emotion': current_emotion.__dict__,
                'context_analysis': context.__dict__,
                'nkat_modifications': {'theory_applied': True},
                'suppression_info': suppression_info,
                'coherence_score': await self._calculate_coherence_score(processed_text, profile)
            }
            
            self.logger.debug(f"🧠 NKAT処理完了: {character_id} ({processing_time:.3f}s)")
            
            return processed_text, result_info
            
        except Exception as e:
            self.logger.error(f"NKAT処理エラー: {e}")
            return text, {'error': str(e)}

    async def _analyze_context(self, text: str, profile: NKATCharacterProfile) -> NKATContext:
        """文脈分析"""
        
        # 基本的な文脈分析
        emotional_indicators = await self._extract_emotional_indicators(text)
        narrative_tension = await self._calculate_narrative_tension(text)
        
        # 文脈情報構築
        context = NKATContext(
            scene_setting="default",
            relationship_dynamics={},
            emotional_atmosphere=NKATEmotionVector(
                primary_emotion=emotional_indicators.get('primary', NKATEmotionType.JOY),
                intensity=emotional_indicators.get('intensity', 0.5)
            ),
            narrative_tension=narrative_tension,
            temporal_context={'timestamp': time.time()},
            cultural_context={'style': 'kansai'}
        )
        
        return context

    async def _extract_emotional_indicators(self, text: str) -> Dict[str, Any]:
        """感情指標抽出"""
        
        # 簡易感情分析（キーワードベース）
        emotion_keywords = {
            NKATEmotionType.JOY: ['嬉しい', '楽しい', '幸せ', 'わーい', 'やったー'],
            NKATEmotionType.SADNESS: ['悲しい', '辛い', '寂しい', 'うう'],
            NKATEmotionType.ANGER: ['怒り', '腹立つ', 'むかつく', 'イライラ'],
            NKATEmotionType.SURPRISE: ['驚き', 'びっくり', 'えっ', 'まじ'],
            NKATEmotionType.LOVE: ['愛', '好き', '大切', 'ラブ']
        }
        
        emotion_scores = {}
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                emotion_scores[emotion] = score / len(keywords)
        
        if emotion_scores:
            primary_emotion = max(emotion_scores.keys(), key=lambda e: emotion_scores[e])
            intensity = min(1.0, emotion_scores[primary_emotion] * 2)
        else:
            primary_emotion = NKATEmotionType.JOY
            intensity = 0.3
        
        return {
            'primary': primary_emotion,
            'intensity': intensity,
            'all_scores': emotion_scores
        }

    async def _calculate_narrative_tension(self, text: str) -> float:
        """物語的緊張度計算"""
        
        # 簡易緊張度計算
        tension_indicators = [
            '！', '？', '…', 'でも', 'しかし', 'だが', 'けど',
            '急に', '突然', 'いきなり', 'まさか'
        ]
        
        tension_score = sum(1 for indicator in tension_indicators if indicator in text)
        return min(1.0, tension_score / 10)

    async def _update_character_emotion(self, 
                                      profile: NKATCharacterProfile,
                                      context: NKATContext,
                                      text: str) -> NKATEmotionVector:
        """キャラクター感情状態更新"""
        
        # 現在の感情状態取得
        current_emotion = context.emotional_atmosphere
        
        # 原型に基づく感情調整
        archetype_influence = self.archetype_emotion_tendencies.get(profile.archetype, {})
        
        # 感情強度調整
        adjusted_intensity = current_emotion.intensity
        if current_emotion.primary_emotion in archetype_influence:
            archetype_weight = archetype_influence[current_emotion.primary_emotion]
            adjusted_intensity = (adjusted_intensity + archetype_weight) / 2
        
        # 新しい感情ベクトル作成
        updated_emotion = NKATEmotionVector(
            primary_emotion=current_emotion.primary_emotion,
            intensity=adjusted_intensity,
            secondary_emotions=current_emotion.secondary_emotions.copy(),
            contextual_modifiers={'archetype_influence': archetype_influence.get(current_emotion.primary_emotion, 0.5)}
        )
        
        # 感情履歴に追加
        self.emotion_history.append({
            'timestamp': time.time(),
            'character_id': profile.character_id,
            'emotion': updated_emotion,
            'text_trigger': text[:50]
        })
        
        return updated_emotion

    async def _apply_nkat_theory(self,
                               text: str,
                               profile: NKATCharacterProfile,
                               emotion: NKATEmotionVector,
                               context: NKATContext) -> str:
        """NKAT理論適用"""
        
        # 理論パラメータ取得
        narrative_weight = self.narrative_coherence_weight
        character_weight = self.character_consistency_weight
        emotional_weight = self.emotional_authenticity_weight
        
        # 原型一貫性チェック
        archetype_consistency = await self._check_archetype_consistency(text, profile)
        
        # 感情的真正性チェック
        emotional_authenticity = await self._check_emotional_authenticity(text, emotion)
        
        # 物語的一貫性チェック
        narrative_coherence = await self._check_narrative_coherence(text, context)
        
        # 総合スコア計算
        total_score = (
            archetype_consistency * character_weight +
            emotional_authenticity * emotional_weight +
            narrative_coherence * narrative_weight
        ) / (character_weight + emotional_weight + narrative_weight)
        
        # 理論スコア記録
        self.performance_metrics['theory_coherence_score'].append(total_score)
        
        # 閾値以下の場合は調整
        if total_score < self.pattern_recognition_threshold:
            text = await self._enhance_text_with_theory(text, profile, emotion, context)
        
        return text

    async def _check_archetype_consistency(self, text: str, profile: NKATCharacterProfile) -> float:
        """原型一貫性チェック"""
        
        # 発話パターンとの一致度
        speech_patterns = profile.speech_patterns
        
        consistency_score = 0.8  # 基本スコア
        
        # 丁寧度チェック
        if speech_patterns.get('formality_level', 0.5) > 0.7:
            if any(marker in text for marker in ['である', 'ます', 'です']):
                consistency_score += 0.1
        else:
            if any(marker in text for marker in ['や', 'やん', 'わ']):
                consistency_score += 0.1
        
        return min(1.0, consistency_score)

    async def _check_emotional_authenticity(self, text: str, emotion: NKATEmotionVector) -> float:
        """感情的真正性チェック"""
        
        # 感情表現の一致度
        emotion_markers = {
            NKATEmotionType.JOY: ['♪', '(*^^*)', 'うれしい', 'やったー'],
            NKATEmotionType.SADNESS: ['(T_T)', 'うう', '悲しい'],
            NKATEmotionType.ANGER: ['ムカつく', 'イライラ', '怒り'],
            NKATEmotionType.SURPRISE: ['！？', 'びっくり', 'まじで']
        }
        
        markers = emotion_markers.get(emotion.primary_emotion, [])
        authenticity_score = 0.6  # 基本スコア
        
        if any(marker in text for marker in markers):
            authenticity_score += 0.3 * emotion.intensity
        
        return min(1.0, authenticity_score)

    async def _check_narrative_coherence(self, text: str, context: NKATContext) -> float:
        """物語的一貫性チェック"""
        
        # 基本的な一貫性スコア
        coherence_score = 0.7
        
        # 文脈との整合性
        if context.narrative_tension > 0.7:
            tension_markers = ['！', '？', '…']
            if any(marker in text for marker in tension_markers):
                coherence_score += 0.2
        
        return min(1.0, coherence_score)

    async def _enhance_text_with_theory(self,
                                      text: str,
                                      profile: NKATCharacterProfile,
                                      emotion: NKATEmotionVector,
                                      context: NKATContext) -> str:
        """理論に基づくテキスト強化"""
        
        enhanced_text = text
        
        # 原型特有の表現追加
        if profile.archetype == NKATCharacterArchetype.INNOCENT:
            if emotion.primary_emotion == NKATEmotionType.JOY:
                enhanced_text += "♪"
        elif profile.archetype == NKATCharacterArchetype.SAGE:
            if '。' in enhanced_text and not enhanced_text.endswith('である。'):
                enhanced_text = enhanced_text.replace('。', 'である。')
        
        # 感情強度に基づく調整
        if emotion.intensity > 0.8:
            # 強い感情の場合は記号を追加
            if not any(symbol in enhanced_text for symbol in ['！', '♪', '(*^^*)']):
                enhanced_text += "！"
        
        return enhanced_text

    async def _calculate_coherence_score(self, text: str, profile: NKATCharacterProfile) -> float:
        """一貫性スコア計算"""
        
        # 複数の一貫性指標を統合
        archetype_score = await self._check_archetype_consistency(text, profile)
        
        # 簡易計算
        coherence_score = archetype_score * 0.8 + 0.2  # 基本点
        
        return min(1.0, coherence_score)

    def _handle_coordination_request(self, request_data: Dict[str, Any]):
        """協調制御要求処理"""
        self.logger.debug(f"協調制御要求受信: {request_data}")

    def _handle_memory_emergency(self):
        """メモリ緊急事態処理"""
        # 一時的に処理を軽量化
        self.emotion_memory_window = max(50, self.emotion_memory_window // 2)
        self.logger.warning(f"⚠️ メモリ緊急事態: 履歴ウィンドウを{self.emotion_memory_window}に縮小")

    def get_performance_report(self) -> Dict[str, Any]:
        """性能レポート取得"""
        
        if not self.performance_metrics['emotion_processing_time']:
            return {'error': '性能データなし'}
        
        processing_times = list(self.performance_metrics['emotion_processing_time'])
        coherence_scores = list(self.performance_metrics['theory_coherence_score'])
        
        return {
            'summary': {
                'total_characters': len(self.character_profiles),
                'total_emotions_processed': len(self.emotion_history),
                'average_processing_time': sum(processing_times) / len(processing_times),
                'average_coherence_score': sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0,
                'theory_enabled': self.theory_enabled,
                'emotion_engine_enabled': self.emotion_engine_enabled
            },
            'performance': {
                'fastest_processing': min(processing_times),
                'slowest_processing': max(processing_times),
                'peak_coherence': max(coherence_scores) if coherence_scores else 0.0,
                'emotion_diversity': len(set(entry['emotion'].primary_emotion for entry in self.emotion_history))
            },
            'integration': {
                'coordination_controller': self.coordination_controller is not None,
                'memory_system': self.memory_system is not None,
                'repetition_suppressor': self.repetition_suppressor is not None
            }
        }

    async def shutdown(self):
        """システム終了"""
        self.logger.info("🔄 NKAT理論統合準備システム終了中...")
        
        self.is_active = False
        
        # 統計保存
        await self._save_learning_data()
        
        # 最終レポート
        final_report = self.get_performance_report()
        self.logger.info(f"✅ NKAT システム終了完了 - 統計: {final_report['summary']}")

    async def _save_learning_data(self):
        """学習データ保存"""
        try:
            stats_dir = Path("logs/nkat_integration")
            stats_dir.mkdir(parents=True, exist_ok=True)
            
            learning_data = {
                'timestamp': time.time(),
                'character_profiles': {cid: {
                    'archetype': profile.archetype.name,
                    'base_emotions': {e.name: v for e, v in profile.base_emotions.items()},
                    'speech_patterns': profile.speech_patterns
                } for cid, profile in self.character_profiles.items()},
                'learned_patterns': self.learned_patterns,
                'performance_summary': self.get_performance_report(),
                'theory_parameters': self.theory_parameters
            }
            
            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            data_file = stats_dir / f"nkat_learning_{timestamp_str}.json"
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(learning_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"📊 学習データ保存: {data_file}")
            
        except Exception as e:
            self.logger.error(f"学習データ保存エラー: {e}")


# ファクトリ関数とテスト関数

def create_nkat_integration_system(config: Dict[str, Any] = None) -> NKATTheoryIntegrationPreparationV3:
    """NKAT理論統合準備システム v3.0 ファクトリ関数"""
    default_config = {
        'theory_enabled': True,
        'emotion_engine_enabled': True,
        'dynamic_adaptation_enabled': True,
        'real_time_processing': True,
        'narrative_coherence_weight': 0.7,
        'character_consistency_weight': 0.8,
        'emotional_authenticity_weight': 0.6,
        'emotion_update_interval': 0.5,
        'pattern_recognition_threshold': 0.8
    }
    
    if config:
        default_config.update(config)
    
    return NKATTheoryIntegrationPreparationV3(default_config)


async def test_nkat_integration_system():
    """NKAT理論統合システムのテスト"""
    print("🧪 NKAT理論統合準備システム v3.0 テスト開始")
    
    # システム作成
    nkat_system = create_nkat_integration_system({
        'emotion_update_interval': 0.1,
        'pattern_recognition_threshold': 0.5
    })
    
    try:
        # テストキャラクター作成
        profile1 = nkat_system.create_character_profile(
            character_id="test_innocent",
            archetype=NKATCharacterArchetype.INNOCENT,
            custom_traits={'JOY': 0.9, 'SADNESS': 0.2}
        )
        
        profile2 = nkat_system.create_character_profile(
            character_id="test_sage",
            archetype=NKATCharacterArchetype.SAGE,
            custom_traits={'MELANCHOLY': 0.8, 'ANGER': 0.1}
        )
        
        # テストテキスト処理
        test_texts = [
            ("おはようございます！今日もええ天気やなあ♪", "test_innocent"),
            ("なるほど、それは興味深い考察である。", "test_sage"),
            ("うう、悲しいわ…でも頑張るで！", "test_innocent")
        ]
        
        for text, character_id in test_texts:
            processed_text, result_info = await nkat_system.process_text_with_nkat(
                text, character_id
            )
            
            print(f"📝 処理結果 ({character_id}):")
            print(f"   入力: {text}")
            print(f"   出力: {processed_text}")
            print(f"   一貫性スコア: {result_info.get('coherence_score', 0):.3f}")
            print(f"   処理時間: {result_info.get('processing_time', 0):.3f}s")
            print()
        
        # 性能レポート
        performance_report = nkat_system.get_performance_report()
        print(f"📊 性能レポート: {performance_report['summary']}")
        
        print("✅ NKAT理論統合準備システム v3.0 テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        
    finally:
        # システム終了
        await nkat_system.shutdown()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_nkat_integration_system()) 