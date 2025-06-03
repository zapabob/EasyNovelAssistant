# -*- coding: utf-8 -*-
"""
NKAT (Non-commutative Kolmogorov-Arnold Representation Theory) 統合モジュール
文章の一貫性向上に特化したEasyNovelAssistant統合機能
"""

import json
import logging
import numpy as np
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple, Any, Deque
from collections import deque
import torch
import torch.nn as nn
from tqdm import tqdm
import hashlib
import re

# 高度一貫性プロセッサをインポート
try:
    from .advanced_consistency import AdvancedConsistencyProcessor, ConsistencyLevel
    ADVANCED_CONSISTENCY_AVAILABLE = True
except ImportError:
    ADVANCED_CONSISTENCY_AVAILABLE = False


class TextConsistencyProcessor:
    """
    テキスト一貫性処理プロセッサ
    文章の論理的流れと文体の一貫性を維持
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger = self._setup_logging()
        
        # 一貫性維持パラメータ
        self.consistency_mode = config.get("nkat_consistency_mode", True)
        self.stability_factor = config.get("nkat_stability_factor", 0.8)
        self.context_memory = config.get("nkat_context_memory", 3)
        self.smoothing_enabled = config.get("nkat_smoothing_enabled", True)
        
        # コンテキスト履歴管理
        self.context_history: Deque[str] = deque(maxlen=self.context_memory)
        self.output_history: Deque[str] = deque(maxlen=self.context_memory)
        self.style_patterns = {}
        
        # キャッシュシステム
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.max_cache_size = config.get("nkat_cache_size", 500)
        
        # 高度一貫性プロセッサ
        if ADVANCED_CONSISTENCY_AVAILABLE and config.get("nkat_advanced_mode", True):
            self.advanced_processor = AdvancedConsistencyProcessor(config)
            self.use_advanced_mode = True
            self.logger.info("高度一貫性モードが有効化されました")
        else:
            self.advanced_processor = None
            self.use_advanced_mode = False
            self.logger.info("標準一貫性モードで動作します")
        
        # 処理統計
        self.stats = {
            "processed_texts": 0,
            "consistency_improvements": 0,
            "cache_hits": 0,
            "average_processing_time": 0,
            "total_processing_time": 0,
            "advanced_mode_enabled": self.use_advanced_mode
        }
        
        self.logger.info(f"TextConsistencyProcessor初期化完了 (Device: {self.device})")
        
    def _setup_logging(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger("NKAT_Consistency")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def analyze_text_style(self, text: str) -> Dict[str, Any]:
        """テキストの文体分析"""
        style_features = {
            "sentence_length": len(text.split()),
            "punctuation_density": sum(1 for c in text if c in "。！？…") / max(len(text), 1),
            "exclamation_ratio": text.count("！") / max(len(text), 1),
            "ellipsis_usage": text.count("…") / max(len(text), 1),
            "dialogue_ratio": text.count("「") / max(len(text), 1),
            "repetition_pattern": self._detect_repetition_pattern(text),
            "emotional_intensity": self._calculate_emotional_intensity(text)
        }
        return style_features
    
    def _detect_repetition_pattern(self, text: str) -> float:
        """反復パターンの検出"""
        words = text.split()
        if len(words) < 2:
            return 0.0
        
        repetitions = 0
        for i in range(len(words) - 1):
            if words[i] == words[i + 1]:
                repetitions += 1
        
        return repetitions / max(len(words) - 1, 1)
    
    def _calculate_emotional_intensity(self, text: str) -> float:
        """感情強度の計算"""
        emotional_chars = "！？…あああああ"
        intensity = sum(text.count(char) for char in emotional_chars)
        return min(intensity / max(len(text), 1) * 10, 1.0)
    
    def maintain_consistency(self, new_text: str, context: Optional[str] = None) -> str:
        """一貫性維持処理"""
        if not self.consistency_mode:
            return new_text
        
        start_time = time.time()
        
        # 高度一貫性モードが有効な場合
        if self.use_advanced_mode and self.advanced_processor:
            try:
                enhanced_text = self.advanced_processor.enhance_consistency(new_text, context or "")
                self._update_basic_stats(time.time() - start_time)
                return enhanced_text
            except Exception as e:
                self.logger.error(f"高度一貫性処理エラー（標準モードにフォールバック）: {e}")
                # 標準処理に続行
        
        # 標準一貫性処理
        return self._standard_consistency_processing(new_text, context, start_time)
    
    def _standard_consistency_processing(self, new_text: str, context: Optional[str], start_time: float) -> str:
        """標準一貫性処理"""
        # キャッシュチェック
        cache_key = hashlib.md5((new_text + str(context)).encode()).hexdigest()
        
        with self.cache_lock:
            if cache_key in self.cache:
                self.stats["cache_hits"] += 1
                return self.cache[cache_key]
        
        try:
            # 現在のテキストの文体分析
            current_style = self.analyze_text_style(new_text)
            
            # 過去のコンテキストとの一貫性チェック
            consistency_score = self._calculate_consistency_score(current_style)
            
            # 一貫性が低い場合の補正処理
            if consistency_score < self.stability_factor:
                corrected_text = self._apply_consistency_correction(
                    new_text, current_style, consistency_score
                )
                self.stats["consistency_improvements"] += 1
            else:
                corrected_text = new_text
            
            # スムージング処理
            if self.smoothing_enabled:
                corrected_text = self._apply_text_smoothing(corrected_text)
            
            # 履歴更新
            self.context_history.append(context or "")
            self.output_history.append(corrected_text)
            self._update_style_patterns(current_style)
            
            # キャッシュ保存
            with self.cache_lock:
                if len(self.cache) >= self.max_cache_size:
                    # LRU削除
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                
                self.cache[cache_key] = corrected_text
            
            # 統計更新
            processing_time = time.time() - start_time
            self._update_stats(processing_time)
            
            return corrected_text
            
        except Exception as e:
            self.logger.error(f"一貫性維持処理エラー: {e}")
            return new_text  # フォールバック
    
    def _calculate_consistency_score(self, current_style: Dict[str, Any]) -> float:
        """一貫性スコア計算"""
        if not self.style_patterns:
            return 1.0  # 初回は一貫性あり
        
        # 過去の文体パターンとの比較
        avg_patterns = {}
        for key in current_style.keys():
            if key in self.style_patterns:
                avg_patterns[key] = np.mean(self.style_patterns[key])
            else:
                avg_patterns[key] = current_style[key]
        
        # 各要素の類似度計算
        similarities = []
        for key, current_value in current_style.items():
            if key in avg_patterns:
                avg_value = avg_patterns[key]
                if avg_value > 0:
                    similarity = min(current_value / avg_value, avg_value / current_value)
                    similarities.append(similarity)
                else:
                    similarities.append(1.0 if current_value == 0 else 0.5)
        
        return np.mean(similarities) if similarities else 1.0
    
    def _apply_consistency_correction(self, text: str, style: Dict[str, Any], score: float) -> str:
        """一貫性補正の適用"""
        corrected = text
        
        # 文体の過度な変化を緩和
        if score < 0.5:
            # 急激な変化の場合、より穏やかな表現に調整
            corrected = self._moderate_extreme_expressions(corrected)
        
        # 反復パターンの正規化
        if style["repetition_pattern"] > 0.3:
            corrected = self._normalize_repetitions(corrected)
        
        # 感情強度の調整
        if style["emotional_intensity"] > 0.8 and self.output_history:
            # 前回出力と比較して急激な感情変化を緩和
            last_output = self.output_history[-1]
            last_style = self.analyze_text_style(last_output)
            if abs(style["emotional_intensity"] - last_style["emotional_intensity"]) > 0.5:
                corrected = self._adjust_emotional_intensity(corrected, last_style["emotional_intensity"])
        
        return corrected
    
    def _moderate_extreme_expressions(self, text: str) -> str:
        """極端な表現の緩和"""
        # 過度な反復を削減
        text = re.sub(r'あ{6,}', 'あああああ', text)
        text = re.sub(r'！{4,}', '！！！', text)
        text = re.sub(r'…{4,}', '…', text)
        
        return text
    
    def _normalize_repetitions(self, text: str) -> str:
        """反復パターンの正規化"""
        # 同じ単語の連続を制限
        words = text.split()
        normalized_words = []
        prev_word = ""
        count = 0
        
        for word in words:
            if word == prev_word:
                count += 1
                if count <= 2:  # 最大2回の連続まで許可
                    normalized_words.append(word)
            else:
                count = 1
                normalized_words.append(word)
                prev_word = word
        
        return " ".join(normalized_words)
    
    def _adjust_emotional_intensity(self, text: str, target_intensity: float) -> str:
        """感情強度の調整"""
        current_intensity = self._calculate_emotional_intensity(text)
        
        if current_intensity > target_intensity * 1.5:
            # 強度を下げる
            text = text.replace("！！！", "！")
            text = text.replace("あああああ", "ああ")
        elif current_intensity < target_intensity * 0.5:
            # 強度を上げる（ただし穏やかに）
            text = text.replace("。", "！")
        
        return text
    
    def _apply_text_smoothing(self, text: str) -> str:
        """テキストスムージング処理"""
        # 不自然な文字列の除去
        text = re.sub(r'\s+', ' ', text)  # 複数スペースを単一に
        text = re.sub(r'([。！？])\1+', r'\1', text)  # 句読点の重複除去
        
        # 自然な改行の挿入
        sentences = text.split('。')
        if len(sentences) > 3:
            # 長い段落を適切に分割
            reformed_sentences = []
            for i, sentence in enumerate(sentences):
                reformed_sentences.append(sentence)
                if i > 0 and i % 2 == 0 and i < len(sentences) - 1:
                    reformed_sentences.append("\n")
            text = "。".join(reformed_sentences)
        
        return text.strip()
    
    def _update_style_patterns(self, style: Dict[str, Any]):
        """文体パターンの更新"""
        for key, value in style.items():
            if key not in self.style_patterns:
                self.style_patterns[key] = []
            
            self.style_patterns[key].append(value)
            
            # 履歴サイズ制限
            if len(self.style_patterns[key]) > self.context_memory * 2:
                self.style_patterns[key] = self.style_patterns[key][-self.context_memory:]
    
    def _update_stats(self, processing_time: float):
        """統計情報更新"""
        self.stats["processed_texts"] += 1
        self.stats["total_processing_time"] += processing_time
        self.stats["average_processing_time"] = (
            self.stats["total_processing_time"] / self.stats["processed_texts"]
        )
    
    def _update_basic_stats(self, processing_time: float):
        """基本統計情報更新（高度モード使用時）"""
        self.stats["processed_texts"] += 1
        self.stats["total_processing_time"] += processing_time
        self.stats["average_processing_time"] = (
            self.stats["total_processing_time"] / self.stats["processed_texts"]
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計取得"""
        cache_hit_rate = (
            self.stats["cache_hits"] / max(self.stats["processed_texts"], 1) * 100
        )
        
        consistency_rate = (
            self.stats["consistency_improvements"] / max(self.stats["processed_texts"], 1) * 100
        )
        
        base_stats = {
            "processed_texts": self.stats["processed_texts"],
            "consistency_improvements": self.stats["consistency_improvements"],
            "consistency_improvement_rate": f"{consistency_rate:.2f}%",
            "cache_hit_rate": f"{cache_hit_rate:.2f}%",
            "average_processing_time": f"{self.stats['average_processing_time']:.4f}s",
            "cache_size": len(self.cache),
            "context_memory_usage": f"{len(self.context_history)}/{self.context_memory}",
            "device": str(self.device),
            "advanced_mode_enabled": self.use_advanced_mode
        }
        
        # 高度一貫性統計を追加
        if self.use_advanced_mode and self.advanced_processor:
            advanced_stats = self.advanced_processor.get_comprehensive_stats()
            base_stats["advanced_stats"] = advanced_stats
        
        return base_stats
    
    def clear_cache_and_history(self):
        """キャッシュと履歴のクリア"""
        with self.cache_lock:
            self.cache.clear()
        
        self.context_history.clear()
        self.output_history.clear()
        self.style_patterns.clear()
        
        # 高度一貫性プロセッサもクリア
        if self.use_advanced_mode and self.advanced_processor:
            self.advanced_processor.reset_all_context()
        
        self.logger.info("NKAT一貫性プロセッサをクリアしました")


class NKATIntegration:
    """
    EasyNovelAssistantとNKAT一貫性プロセッサの統合管理クラス
    """
    
    def __init__(self, easy_novel_context):
        self.ctx = easy_novel_context
        self.config = self._load_nkat_config()
        
        # 一貫性プロセッサ初期化
        self.processor = TextConsistencyProcessor(self.config)
        
        # 非同期処理用
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        self.logger = logging.getLogger("NKAT_Integration")
        self.logger.info("NKAT統合モジュール初期化完了（一貫性モード）")
    
    def _load_nkat_config(self) -> Dict[str, Any]:
        """NKAT設定読み込み"""
        default_config = {
            "nkat_enabled": True,
            "nkat_consistency_mode": True,
            "nkat_stability_factor": 0.8,
            "nkat_context_memory": 3,
            "nkat_smoothing_enabled": True,
            "nkat_cache_size": 500,
            "nkat_async_processing": True,
            "nkat_advanced_mode": True,
            "consistency_level": "moderate",
            "character_memory_depth": 10,
            "emotion_smoothing_factor": 0.7,
            "style_adaptation_rate": 0.3
        }
        
        try:
            # config.jsonからNKAT設定を読み込み（UTF-8 BOM対応）
            with open("config.json", "r", encoding="utf-8-sig") as f:
                config = json.load(f)
            
            # NKAT関連設定をマージ
            for key, default_value in default_config.items():
                if key not in config:
                    config[key] = default_value
            
            return config
            
        except Exception as e:
            self.logger.warning(f"NKAT設定読み込み失敗、デフォルト設定を使用: {e}")
            return default_config
    
    def enhance_text_generation(self, prompt: str, llm_output: str) -> str:
        """
        LLM出力の一貫性向上処理
        """
        if not self.config.get("nkat_enabled", True):
            return llm_output
        
        try:
            # 一貫性維持処理
            enhanced_text = self.processor.maintain_consistency(llm_output, context=prompt)
            
            return enhanced_text
            
        except Exception as e:
            self.logger.error(f"テキスト生成強化エラー: {e}")
            return llm_output
    
    def async_process_text(self, text: str, context: str = "", callback=None):
        """非同期テキスト処理"""
        if not self.config.get("nkat_async_processing", True):
            return self.enhance_text_generation(context, text)
        
        def process():
            try:
                result = self.enhance_text_generation(context, text)
                if callback:
                    callback(result)
                return result
            except Exception as e:
                self.logger.error(f"非同期処理エラー: {e}")
                if callback:
                    callback(text)
                return text
        
        future = self.executor.submit(process)
        return future
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """統合統計情報取得"""
        processor_stats = self.processor.get_performance_stats()
        
        integration_stats = {
            "nkat_enabled": self.config.get("nkat_enabled", True),
            "consistency_mode": self.config.get("nkat_consistency_mode", True),
            "advanced_mode": self.config.get("nkat_advanced_mode", True),
            "config": {
                "stability_factor": self.config.get("nkat_stability_factor", 0.8),
                "context_memory": self.config.get("nkat_context_memory", 3),
                "smoothing_enabled": self.config.get("nkat_smoothing_enabled", True),
                "consistency_level": self.config.get("consistency_level", "moderate")
            },
            "processor_stats": processor_stats,
            "async_enabled": self.config.get("nkat_async_processing", True)
        }
        
        return integration_stats
    
    def reset_consistency_context(self):
        """一貫性コンテキストのリセット"""
        self.processor.clear_cache_and_history()
        self.logger.info("NKAT一貫性コンテキストをリセットしました")
    
    def cleanup(self):
        """リソースクリーンアップ"""
        self.processor.clear_cache_and_history()
        self.executor.shutdown(wait=True)
        self.logger.info("NKAT統合モジュールをクリーンアップしました")


# EasyNovelAssistantへの統合用関数
def integrate_nkat_with_easy_novel_assistant(ctx):
    """
    EasyNovelAssistantのContextにNKAT機能を統合
    """
    try:
        ctx.nkat = NKATIntegration(ctx)
        print("NKAT統合モジュール初期化完了（文章一貫性向上モード）")
        if ADVANCED_CONSISTENCY_AVAILABLE:
            print("高度一貫性機能が有効化されました")
        return True
    except Exception as e:
        print(f"NKAT統合エラー: {e}")
        return False


if __name__ == "__main__":
    # テスト実行
    test_config = {
        "nkat_enabled": True,
        "nkat_consistency_mode": True,
        "nkat_stability_factor": 0.8,
        "nkat_context_memory": 3,
        "nkat_smoothing_enabled": True,
        "nkat_advanced_mode": True,
        "consistency_level": "moderate"
    }
    
    processor = TextConsistencyProcessor(test_config)
    
    # ダミーテキスト処理
    test_texts = [
        "あああああ…！ オス様…！",
        "！！！！！ うわああああああああああああぁっ…！",
        "静かな夜でした。",
        "あああああああああああああああ！！！！！！"
    ]
    
    for i, text in enumerate(test_texts):
        result = processor.maintain_consistency(text, f"テストコンテキスト{i}")
        print(f"入力: {text}")
        print(f"出力: {result}")
        print("---")
    
    print("NKAT一貫性処理テスト完了")
    print(f"統計: {processor.get_performance_stats()}") 