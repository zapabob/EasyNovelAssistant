# -*- coding: utf-8 -*-
"""
クロス抑制システム + メモリバッファエンジン v1.0

【概要】
複数のテキスト生成間で反復パターンを共有し、
文脈を考慮した反復抑制を行うクロス抑制システム。

【主要機能】
1. セッション横断の反復パターン記憶
2. キャラクター別反復履歴管理
3. 文脈考慮型抑制重み調整
4. リアルタイム学習・適応

Author: EasyNovelAssistant Development Team
Date: 2025-01-06
"""

import os
import sys
import json
import time
import threading
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
import numpy as np
import logging

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
src_dir = os.path.join(project_root, "src")
sys.path.insert(0, project_root)
sys.path.insert(0, src_dir)

try:
    from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
    from integration.lora_style_coordinator import LoRAStyleCoordinator
    V3_AVAILABLE = True
except ImportError:
    V3_AVAILABLE = False
    logging.warning("v3システムまたはLoRA協調システムが見つかりません")


@dataclass
class CrossSuppressionPattern:
    """クロス抑制パターン"""
    pattern: str
    frequency: int
    last_seen: float
    contexts: List[str]
    suppression_weight: float
    character_sources: Set[str]
    session_ids: Set[str]


@dataclass
class MemoryContext:
    """メモリ文脈情報"""
    session_id: str
    timestamp: float
    character: str
    text_snippet: str
    patterns_found: List[str]
    suppression_applied: List[str]


class SessionMemoryBuffer:
    """セッションメモリバッファ"""
    
    def __init__(self, max_size: int = 1000, context_window: int = 10):
        self.max_size = max_size
        self.context_window = context_window
        self.contexts = deque(maxlen=max_size)
        self.pattern_index = defaultdict(list)  # パターン -> コンテキストのインデックス
        self.character_index = defaultdict(list)  # キャラ -> コンテキストのインデックス
        self.session_index = defaultdict(list)  # セッション -> コンテキストのインデックス
        self.lock = threading.RLock()
    
    def add_context(self, context: MemoryContext):
        """コンテキストの追加"""
        with self.lock:
            context_idx = len(self.contexts)
            self.contexts.append(context)
            
            # インデックス更新
            for pattern in context.patterns_found:
                self.pattern_index[pattern].append(context_idx)
            
            self.character_index[context.character].append(context_idx)
            self.session_index[context.session_id].append(context_idx)
            
            # 古いインデックスのクリーンアップ
            if len(self.contexts) > self.max_size * 0.9:
                self._cleanup_old_indices()
    
    def _cleanup_old_indices(self):
        """古いインデックスのクリーンアップ"""
        cutoff = len(self.contexts) - self.max_size
        
        # パターンインデックスのクリーンアップ
        for pattern in list(self.pattern_index.keys()):
            self.pattern_index[pattern] = [
                idx for idx in self.pattern_index[pattern] if idx >= cutoff
            ]
            if not self.pattern_index[pattern]:
                del self.pattern_index[pattern]
        
        # 同様にキャラクターとセッションインデックスもクリーンアップ
        for char in list(self.character_index.keys()):
            self.character_index[char] = [
                idx for idx in self.character_index[char] if idx >= cutoff
            ]
            if not self.character_index[char]:
                del self.character_index[char]
        
        for session in list(self.session_index.keys()):
            self.session_index[session] = [
                idx for idx in self.session_index[session] if idx >= cutoff
            ]
            if not self.session_index[session]:
                del self.session_index[session]
    
    def get_relevant_contexts(self, pattern: str = None, character: str = None, 
                            session_id: str = None, limit: int = None) -> List[MemoryContext]:
        """関連コンテキストの取得"""
        with self.lock:
            indices = set()
            
            if pattern:
                indices.update(self.pattern_index.get(pattern, []))
            if character:
                indices.update(self.character_index.get(character, []))
            if session_id:
                indices.update(self.session_index.get(session_id, []))
            
            if not indices:
                # 最新のコンテキストを返す
                indices = range(max(0, len(self.contexts) - self.context_window), len(self.contexts))
            
            # インデックスを時間順でソート
            sorted_indices = sorted(indices, reverse=True)
            if limit:
                sorted_indices = sorted_indices[:limit]
            
            return [self.contexts[idx] for idx in sorted_indices if idx < len(self.contexts)]


class CrossSuppressionEngine:
    """クロス抑制エンジン"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/cross_suppression.json"
        self.logger = logging.getLogger(__name__)
        
        # コンポーネント
        self.memory_buffer = SessionMemoryBuffer()
        self.repetition_suppressor: Optional[AdvancedRepetitionSuppressorV3] = None
        self.lora_coordinator: Optional[LoRAStyleCoordinator] = None
        
        # パターン管理
        self.cross_patterns: Dict[str, CrossSuppressionPattern] = {}
        self.pattern_lock = threading.RLock()
        
        # 設定
        self.config = {
            'cross_suppression_threshold': 0.3,
            'pattern_decay_rate': 0.95,  # 時間経過による重み減衰
            'min_pattern_frequency': 2,  # 最小出現回数
            'context_influence_weight': 0.4,  # 文脈影響の重み
            'character_isolation': True,  # キャラクター別分離
            'session_memory_hours': 24,  # セッションメモリ保持時間
            'adaptive_learning': True,   # 適応学習
            'realtime_updates': True     # リアルタイム更新
        }
        
        # 統計
        self.stats = {
            'patterns_learned': 0,
            'cross_suppressions_applied': 0,
            'sessions_tracked': 0,
            'contexts_remembered': 0
        }
        
        self._load_configuration()
        self.logger.info("🧠 クロス抑制エンジン初期化完了")
    
    def _load_configuration(self):
        """設定の読み込み"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                self.config.update(loaded_config.get('engine_config', {}))
                
                # パターンの復元
                patterns_data = loaded_config.get('cross_patterns', {})
                for pattern_str, data in patterns_data.items():
                    pattern = CrossSuppressionPattern(
                        pattern=data['pattern'],
                        frequency=data['frequency'],
                        last_seen=data['last_seen'],
                        contexts=data['contexts'],
                        suppression_weight=data['suppression_weight'],
                        character_sources=set(data['character_sources']),
                        session_ids=set(data['session_ids'])
                    )
                    self.cross_patterns[pattern_str] = pattern
                
                self.logger.info(f"📖 設定読み込み完了: {len(self.cross_patterns)}パターン")
        except Exception as e:
            self.logger.warning(f"設定読み込み失敗: {e}")
    
    def _save_configuration(self):
        """設定の保存"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # パターンの辞書化
            patterns_data = {}
            for pattern_str, pattern in self.cross_patterns.items():
                patterns_data[pattern_str] = {
                    'pattern': pattern.pattern,
                    'frequency': pattern.frequency,
                    'last_seen': pattern.last_seen,
                    'contexts': pattern.contexts,
                    'suppression_weight': pattern.suppression_weight,
                    'character_sources': list(pattern.character_sources),
                    'session_ids': list(pattern.session_ids)
                }
            
            config_data = {
                'engine_config': self.config,
                'cross_patterns': patterns_data,
                'stats': self.stats
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info("💾 クロス抑制設定保存完了")
        except Exception as e:
            self.logger.error(f"設定保存失敗: {e}")
    
    def initialize_systems(self, repetition_config: Optional[Dict] = None,
                          lora_config: Optional[Dict] = None):
        """システムコンポーネントの初期化"""
        if V3_AVAILABLE:
            # 反復抑制システム初期化
            config = repetition_config or {
                'similarity_threshold': 0.30,
                'max_distance': 60,
                'min_compress_rate': 0.02,
                'enable_4gram_blocking': True,
                'ngram_block_size': 3,
                'enable_drp': True,
                'drp_base': 1.15,
                'drp_alpha': 0.6,
                'enable_mecab_normalization': False,
                'enable_rhetorical_protection': True,
                'enable_latin_number_detection': True,
                'debug_mode': True
            }
            self.repetition_suppressor = AdvancedRepetitionSuppressorV3(config)
            
            # LoRA協調システム初期化
            self.lora_coordinator = LoRAStyleCoordinator(lora_config)
            self.lora_coordinator.initialize_systems(config)
            
            self.logger.info("✅ システムコンポーネント初期化完了")
            return True
        
        return False
    
    def learn_patterns_from_text(self, text: str, character: str, session_id: str) -> List[str]:
        """テキストからパターンを学習"""
        patterns_found = []
        current_time = time.time()
        
        # 基本的な反復パターン検出
        words = text.split()
        pattern_counts = {}
        
        # 単語レベルでの反復検出
        word_counts = {}
        for word in words:
            if len(word) > 1:  # 1文字以上の単語
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # 2-4語のn-gramでパターンを検出
        for n in range(2, 5):  # 2, 3, 4語の組み合わせ
            for i in range(len(words) - n + 1):
                pattern = ' '.join(words[i:i+n])
                if len(pattern) > 2:  # 最小長制限緩和
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # 反復パターンの学習
        # 単語レベル（2回以上出現）
        for word, count in word_counts.items():
            if count >= 2 and len(word) > 1:
                patterns_found.append(word)
        
        # フレーズレベル（1回でも出現すれば記録）
        for pattern, count in pattern_counts.items():
            if count >= 1:
                patterns_found.append(pattern)
        
        # パターンの更新
        with self.pattern_lock:
            for pattern in patterns_found:
                if pattern in self.cross_patterns:
                    # 既存パターンの更新
                    existing = self.cross_patterns[pattern]
                    existing.frequency += 1
                    existing.last_seen = current_time
                    existing.character_sources.add(character)
                    existing.session_ids.add(session_id)
                    
                    # 文脈の追加（最新5件を保持）
                    context_snippet = text[:100] + "..." if len(text) > 100 else text
                    existing.contexts.append(context_snippet)
                    if len(existing.contexts) > 5:
                        existing.contexts.pop(0)
                    
                    # 重みの調整
                    existing.suppression_weight = min(2.0, 
                        existing.suppression_weight + 0.1)
                else:
                    # 新規パターンの追加
                    new_pattern = CrossSuppressionPattern(
                        pattern=pattern,
                        frequency=1,
                        last_seen=current_time,
                        contexts=[text[:100] + "..." if len(text) > 100 else text],
                        suppression_weight=0.5,
                        character_sources={character},
                        session_ids={session_id}
                    )
                    self.cross_patterns[pattern] = new_pattern
                    self.stats['patterns_learned'] += 1
        
        return patterns_found
    
    def process_with_cross_suppression(self, text: str, character: str = None, 
                                     session_id: str = None) -> Tuple[str, Dict[str, Any]]:
        """クロス抑制を適用したテキスト処理"""
        if not session_id:
            session_id = f"session_{int(time.time())}"
        
        start_time = time.time()
        
        # 学習フェーズ（元のテキストから学習）
        learned_patterns = self.learn_patterns_from_text(text, character, session_id)
        
        # デバッグ：学習結果を確認
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"📖 学習パターン: {learned_patterns}")
            self.logger.debug(f"📊 パターン数: {len(learned_patterns)}")
        
        # 関連コンテキストの取得
        relevant_contexts = self.memory_buffer.get_relevant_contexts(
            character=character, session_id=session_id, limit=10
        )
        
        # クロス抑制重みの計算
        cross_suppression_weights = self._calculate_cross_weights(
            text, character, relevant_contexts
        )
        
        # 基本反復抑制処理
        if self.repetition_suppressor:
            # クロス抑制重みを反映した設定調整
            if cross_suppression_weights:
                adjusted_config = self._adjust_config_with_cross_weights(
                    cross_suppression_weights
                )
                self.repetition_suppressor.update_config(adjusted_config)
            
            result_text, metrics = self.repetition_suppressor.suppress_repetitions_with_debug_v3(
                text, character
            )
        else:
            result_text = text
            metrics = None
        
        # クロス抑制の追加適用
        final_text, cross_stats = self._apply_cross_suppression(
            result_text, cross_suppression_weights
        )
        
        # メモリコンテキストの追加
        memory_context = MemoryContext(
            session_id=session_id,
            timestamp=time.time(),
            character=character or "unknown",
            text_snippet=text[:200] + "..." if len(text) > 200 else text,
            patterns_found=learned_patterns,
            suppression_applied=cross_stats.get('patterns_suppressed', [])
        )
        self.memory_buffer.add_context(memory_context)
        
        # 統計情報の構築
        processing_time = (time.time() - start_time) * 1000
        
        stats = {
            'session_id': session_id,
            'character': character,
            'original_length': len(text),
            'final_length': len(final_text),
            'total_compression_rate': (len(text) - len(final_text)) / len(text),
            'patterns_learned': len(learned_patterns),
            'cross_patterns_applied': cross_stats.get('suppressions_applied', 0),
            'relevant_contexts_used': len(relevant_contexts),
            'processing_time_ms': processing_time,
            'v3_metrics': metrics.__dict__ if metrics else {},
            'cross_suppression_weights': cross_suppression_weights,
            'learned_patterns': learned_patterns
        }
        
        self.stats['contexts_remembered'] += 1
        if cross_stats.get('suppressions_applied', 0) > 0:
            self.stats['cross_suppressions_applied'] += 1
        
        return final_text, stats
    
    def _calculate_cross_weights(self, text: str, character: str, 
                               contexts: List[MemoryContext]) -> Dict[str, float]:
        """クロス抑制重みの計算"""
        weights = {}
        current_time = time.time()
        
        with self.pattern_lock:
            for pattern_str, pattern in self.cross_patterns.items():
                if pattern.pattern in text:
                    # 基本重み
                    base_weight = pattern.suppression_weight
                    
                    # 頻度による調整
                    frequency_factor = min(2.0, pattern.frequency / 10.0)
                    
                    # 時間減衰
                    time_decay = self.config['pattern_decay_rate'] ** (
                        (current_time - pattern.last_seen) / 3600  # 時間単位
                    )
                    
                    # キャラクター分離
                    character_factor = 1.0
                    if self.config['character_isolation'] and character:
                        if character not in pattern.character_sources:
                            character_factor = 0.3  # 他キャラクターのパターンは抑制を弱く
                    
                    # 文脈影響
                    context_factor = 1.0
                    for context in contexts:
                        if pattern.pattern in context.text_snippet:
                            context_factor += self.config['context_influence_weight']
                    
                    final_weight = (base_weight * frequency_factor * time_decay * 
                                  character_factor * context_factor)
                    
                    if final_weight > self.config['cross_suppression_threshold']:
                        weights[pattern.pattern] = final_weight
        
        return weights
    
    def _adjust_config_with_cross_weights(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """クロス重みを反映した設定調整"""
        base_config = self.repetition_suppressor.config.copy()
        
        if weights:
            avg_weight = sum(weights.values()) / len(weights)
            
            # 重みが高いほど抑制を強化
            adjustment_factor = 1.0 + (avg_weight - 1.0) * 0.3
            
            base_config['similarity_threshold'] *= max(0.5, 1.0 / adjustment_factor)
            base_config['min_compress_rate'] *= adjustment_factor
        
        return base_config
    
    def _apply_cross_suppression(self, text: str, 
                               weights: Dict[str, float]) -> Tuple[str, Dict[str, Any]]:
        """クロス抑制の追加適用"""
        if not weights:
            return text, {'suppressions_applied': 0, 'patterns_suppressed': []}
        
        result_text = text
        suppressions_applied = 0
        patterns_suppressed = []
        
        # 重みの高い順にソート
        sorted_patterns = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        for pattern, weight in sorted_patterns:
            if pattern in result_text and weight > self.config['cross_suppression_threshold']:
                # パターンの出現回数をカウント
                count = result_text.count(pattern)
                if count > 1:
                    # 重みに基づいて抑制強度を決定
                    suppress_ratio = min(0.8, weight / 2.0)
                    target_count = max(1, int(count * (1 - suppress_ratio)))
                    
                    # パターンの削減
                    for _ in range(count - target_count):
                        # 最後の出現を削除
                        last_index = result_text.rfind(pattern)
                        if last_index != -1:
                            result_text = (result_text[:last_index] + 
                                         result_text[last_index + len(pattern):])
                            suppressions_applied += 1
                    
                    if suppressions_applied > 0:
                        patterns_suppressed.append(pattern)
        
        return result_text, {
            'suppressions_applied': suppressions_applied,
            'patterns_suppressed': patterns_suppressed
        }
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """セッション統計の取得"""
        contexts = self.memory_buffer.get_relevant_contexts(session_id=session_id)
        
        if not contexts:
            return {'error': 'セッションが見つかりません'}
        
        total_patterns = sum(len(ctx.patterns_found) for ctx in contexts)
        total_suppressions = sum(len(ctx.suppression_applied) for ctx in contexts)
        
        return {
            'session_id': session_id,
            'context_count': len(contexts),
            'total_patterns_learned': total_patterns,
            'total_suppressions_applied': total_suppressions,
            'time_span': contexts[-1].timestamp - contexts[0].timestamp if len(contexts) > 1 else 0,
            'characters_involved': list(set(ctx.character for ctx in contexts))
        }
    
    def get_cross_pattern_stats(self) -> Dict[str, Any]:
        """クロスパターン統計の取得"""
        with self.pattern_lock:
            total_patterns = len(self.cross_patterns)
            active_patterns = sum(1 for p in self.cross_patterns.values() 
                                if p.frequency >= self.config['min_pattern_frequency'])
            
            top_patterns = sorted(
                self.cross_patterns.items(),
                key=lambda x: x[1].frequency,
                reverse=True
            )[:10]
            
            return {
                'total_patterns': total_patterns,
                'active_patterns': active_patterns,
                'top_patterns': [
                    {
                        'pattern': pattern.pattern,
                        'frequency': pattern.frequency,
                        'weight': pattern.suppression_weight,
                        'characters': list(pattern.character_sources)
                    }
                    for _, pattern in top_patterns
                ],
                'engine_stats': self.stats
            }
    
    def cleanup_old_patterns(self, max_age_hours: float = 168):  # 1週間
        """古いパターンのクリーンアップ"""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        with self.pattern_lock:
            patterns_to_remove = [
                pattern_str for pattern_str, pattern in self.cross_patterns.items()
                if pattern.last_seen < cutoff_time and 
                   pattern.frequency < self.config['min_pattern_frequency']
            ]
            
            for pattern_str in patterns_to_remove:
                del self.cross_patterns[pattern_str]
            
            self.logger.info(f"🧹 古いパターンクリーンアップ: {len(patterns_to_remove)}件削除")
    
    def save_state(self):
        """状態の保存"""
        self._save_configuration()
    
    def get_engine_status(self) -> Dict[str, Any]:
        """エンジン状態の取得"""
        return {
            'patterns_count': len(self.cross_patterns),
            'memory_contexts': len(self.memory_buffer.contexts),
            'stats': self.stats,
            'config': self.config,
            'systems_available': {
                'repetition_suppressor': self.repetition_suppressor is not None,
                'lora_coordinator': self.lora_coordinator is not None
            }
        }


def create_default_cross_engine() -> CrossSuppressionEngine:
    """デフォルトクロス抑制エンジンの作成"""
    engine = CrossSuppressionEngine()
    engine.initialize_systems()
    return engine


if __name__ == "__main__":
    # デモ実行
    logging.basicConfig(level=logging.INFO)
    
    print("🧠 クロス抑制システム デモ")
    print("=" * 50)
    
    engine = create_default_cross_engine()
    
    # テストセッション
    session_id = "demo_session_001"
    character = "テストキャラ"
    
    try:
        # テストケース1
        text1 = "今日は良い天気ですね。今日は良い天気だから散歩しましょう。"
        result1, stats1 = engine.process_with_cross_suppression(text1, character, session_id)
        
        print(f"テスト1:")
        print(f"  入力: {text1}")
        print(f"  出力: {result1}")
        print(f"  学習パターン: {stats1['patterns_learned']}")
        print(f"  学習詳細: {stats1.get('learned_patterns', [])}")
        print(f"  圧縮率: {stats1['total_compression_rate']:.1%}")
        
        # テストケース2（同じパターンを含む）
        text2 = "今日は良い天気だし、今日は良い天気なので外に出ます。"
        result2, stats2 = engine.process_with_cross_suppression(text2, character, session_id)
        
        print(f"\nテスト2（クロス抑制適用）:")
        print(f"  入力: {text2}")
        print(f"  出力: {result2}")
        print(f"  圧縮率: {stats2['total_compression_rate']:.1%}")
        print(f"  クロス抑制: {stats2['cross_patterns_applied']}件")
    except Exception as e:
        print(f"❌ 処理エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # 統計表示
    pattern_stats = engine.get_cross_pattern_stats()
    print(f"\n📊 パターン統計:")
    print(f"  総パターン数: {pattern_stats['total_patterns']}")
    print(f"  アクティブパターン: {pattern_stats['active_patterns']}")
    
    if pattern_stats['top_patterns']:
        print(f"  上位パターン:")
        for i, pattern_info in enumerate(pattern_stats['top_patterns'][:3], 1):
            print(f"    {i}. '{pattern_info['pattern']}' 頻度:{pattern_info['frequency']} 重み:{pattern_info['weight']:.2f}")
    
    # セッション統計
    session_stats = engine.get_session_statistics(session_id)
    print(f"\n📈 セッション統計:")
    print(f"  コンテキスト数: {session_stats.get('context_count', 0)}")
    print(f"  学習パターン数: {session_stats.get('total_patterns_learned', 0)}")
    print(f"  適用抑制数: {session_stats.get('total_suppressions_applied', 0)}")
    
    engine.save_state()
    print("\n✅ デモ完了") 