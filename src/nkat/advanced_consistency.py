# -*- coding: utf-8 -*-
"""
高度一貫性プロセッサ（Advanced Consistency Processor）
深層学習技術とNKAT理論を活用した文章一貫性向上システム
"""

import json
import logging
import time
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Deque
from collections import defaultdict, deque
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm


class ConsistencyLevel(Enum):
    """一貫性レベル定義"""
    LIGHT = "light"
    MODERATE = "moderate"
    STRICT = "strict"
    ADAPTIVE = "adaptive"


class EmotionalState:
    """感情状態管理クラス"""
    
    def __init__(self):
        self.intensity = 0.5  # 感情強度 (0.0-1.0)
        self.valence = 0.5   # 感情価 (0.0-1.0: 負-正)
        self.arousal = 0.5   # 覚醒度 (0.0-1.0: 低-高)
        self.dominant_emotion = "neutral"
        self.stability = 1.0  # 感情安定性
        self.last_update = time.time()
    
    def update(self, text: str):
        """テキストから感情状態を更新"""
        # 基本的な感情分析
        exclamation_count = text.count("！") + text.count("!")
        question_count = text.count("？") + text.count("?")
        ellipsis_count = text.count("…")
        
        # 覚醒度計算
        self.arousal = min(1.0, (exclamation_count * 0.2 + question_count * 0.1))
        
        # 感情強度計算
        emotional_chars = ["あ", "う", "わ", "ひ", "ふ"]
        emotional_density = sum(text.count(char) for char in emotional_chars) / max(len(text), 1)
        self.intensity = min(1.0, emotional_density * 5)
        
        # 感情価計算（簡単な語彙ベース）
        positive_words = ["嬉しい", "楽しい", "素晴らしい", "最高", "幸せ"]
        negative_words = ["悲しい", "辛い", "苦しい", "嫌", "ダメ"]
        
        positive_score = sum(1 for word in positive_words if word in text)
        negative_score = sum(1 for word in negative_words if word in text)
        
        if positive_score > negative_score:
            self.valence = 0.7
            self.dominant_emotion = "positive"
        elif negative_score > positive_score:
            self.valence = 0.3
            self.dominant_emotion = "negative"
        else:
            self.valence = 0.5
            self.dominant_emotion = "neutral"
        
        self.last_update = time.time()
    
    def distance_from(self, other: 'EmotionalState') -> float:
        """他の感情状態からの距離を計算"""
        intensity_diff = abs(self.intensity - other.intensity)
        valence_diff = abs(self.valence - other.valence)
        arousal_diff = abs(self.arousal - other.arousal)
        
        return (intensity_diff + valence_diff + arousal_diff) / 3.0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で状態を出力"""
        return {
            "intensity": self.intensity,
            "valence": self.valence,
            "arousal": self.arousal,
            "dominant_emotion": self.dominant_emotion,
            "stability": self.stability
        }


class CharacterProfile:
    """キャラクター特性プロファイル"""
    
    def __init__(self, character_name: str):
        self.character_name = character_name
        self.speech_patterns = {}  # 話し方パターン
        self.emotional_tendencies = EmotionalState()
        self.vocabulary_preferences = {}  # 語彙傾向
        self.response_patterns = []  # 応答パターン履歴
        self.consistency_score = 1.0
        self.last_appearance = time.time()
        
        # 統計情報
        self.total_appearances = 0
        self.emotional_history: Deque[EmotionalState] = deque(maxlen=10)
        
    def update_profile(self, text: str):
        """テキストからプロファイルを更新"""
        self.total_appearances += 1
        self.last_appearance = time.time()
        
        # 感情状態更新
        current_emotion = EmotionalState()
        current_emotion.update(text)
        self.emotional_history.append(current_emotion)
        
        # 話し方パターン更新
        self._analyze_speech_patterns(text)
        
        # 語彙傾向更新
        self._analyze_vocabulary(text)
        
        # 一貫性スコア計算
        self._calculate_consistency_score()
    
    def _analyze_speech_patterns(self, text: str):
        """話し方パターンの分析"""
        patterns = {
            "sentence_ending": self._extract_sentence_endings(text),
            "exclamation_usage": text.count("！") / max(len(text), 1),
            "question_usage": text.count("？") / max(len(text), 1),
            "ellipsis_usage": text.count("…") / max(len(text), 1),
            "average_sentence_length": len(text.split("。")) / max(text.count("。"), 1)
        }
        
        for key, value in patterns.items():
            if key not in self.speech_patterns:
                self.speech_patterns[key] = []
            self.speech_patterns[key].append(value)
            
            # 履歴サイズ制限
            if len(self.speech_patterns[key]) > 20:
                self.speech_patterns[key] = self.speech_patterns[key][-15:]
    
    def _extract_sentence_endings(self, text: str) -> Dict[str, int]:
        """文末表現の抽出"""
        endings = {
            "だ": text.count("だ。") + text.count("だ！"),
            "である": text.count("である"),
            "です": text.count("です"),
            "ます": text.count("ます"),
            "だね": text.count("だね"),
            "よ": text.count("よ。") + text.count("よ！"),
            "な": text.count("な。") + text.count("な！"),
            "の": text.count("の。") + text.count("の？")
        }
        return endings
    
    def _analyze_vocabulary(self, text: str):
        """語彙傾向の分析"""
        words = re.findall(r'[ぁ-ゖァ-ヺー一-龯]+', text)
        
        for word in words:
            if len(word) >= 2:  # 2文字以上の単語のみ
                if word not in self.vocabulary_preferences:
                    self.vocabulary_preferences[word] = 0
                self.vocabulary_preferences[word] += 1
        
        # 上位100語彙のみ保持
        if len(self.vocabulary_preferences) > 100:
            sorted_vocab = sorted(
                self.vocabulary_preferences.items(),
                key=lambda x: x[1],
                reverse=True
            )
            self.vocabulary_preferences = dict(sorted_vocab[:100])
    
    def _calculate_consistency_score(self):
        """一貫性スコアの計算"""
        if len(self.emotional_history) < 2:
            self.consistency_score = 1.0
            return
        
        # 感情変化の激しさを評価
        emotional_variance = 0.0
        for i in range(1, len(self.emotional_history)):
            distance = self.emotional_history[i].distance_from(self.emotional_history[i-1])
            emotional_variance += distance
        
        emotional_variance /= (len(self.emotional_history) - 1)
        
        # 話し方パターンの一貫性を評価
        pattern_consistency = self._calculate_pattern_consistency()
        
        # 総合一貫性スコア
        self.consistency_score = max(0.0, 1.0 - emotional_variance * 0.5 - (1.0 - pattern_consistency) * 0.3)
    
    def _calculate_pattern_consistency(self) -> float:
        """話し方パターンの一貫性計算"""
        if not self.speech_patterns:
            return 1.0
        
        consistency_scores = []
        
        for pattern_name, pattern_values in self.speech_patterns.items():
            if len(pattern_values) >= 3:
                # 標準偏差ベースの一貫性評価
                std_dev = np.std(pattern_values[-10:])  # 最近10回の標準偏差
                mean_val = np.mean(pattern_values[-10:])
                
                if mean_val > 0:
                    coefficient_of_variation = std_dev / mean_val
                    consistency = max(0.0, 1.0 - coefficient_of_variation)
                    consistency_scores.append(consistency)
        
        return np.mean(consistency_scores) if consistency_scores else 1.0
    
    def get_profile_summary(self) -> Dict[str, Any]:
        """プロファイル要約の取得"""
        recent_emotion = self.emotional_history[-1] if self.emotional_history else EmotionalState()
        
        return {
            "character_name": self.character_name,
            "total_appearances": self.total_appearances,
            "consistency_score": self.consistency_score,
            "current_emotion": recent_emotion.to_dict(),
            "dominant_speech_patterns": self._get_dominant_patterns(),
            "vocabulary_size": len(self.vocabulary_preferences),
            "last_appearance": self.last_appearance
        }
    
    def _get_dominant_patterns(self) -> Dict[str, float]:
        """支配的な話し方パターンを取得"""
        dominant = {}
        for pattern_name, values in self.speech_patterns.items():
            if values:
                dominant[pattern_name] = np.mean(values[-5:])  # 最新5回の平均
        return dominant


class AdvancedConsistencyProcessor:
    """
    高度一貫性プロセッサ
    深層学習とNKAT理論を活用した文章一貫性向上システム
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger = self._setup_logging()
        
        # 一貫性レベル設定
        self.consistency_level = ConsistencyLevel(
            config.get("consistency_level", "moderate")
        )
        
        # キャラクター管理
        self.character_profiles: Dict[str, CharacterProfile] = {}
        self.active_character = None
        
        # 高度設定
        self.character_memory_depth = config.get("character_memory_depth", 10)
        self.emotion_smoothing_factor = config.get("emotion_smoothing_factor", 0.7)
        self.style_adaptation_rate = config.get("style_adaptation_rate", 0.3)
        
        # 統計情報
        self.stats = {
            "processed_texts": 0,
            "character_switches": 0,
            "consistency_corrections": 0,
            "emotion_smoothing_applied": 0,
            "style_adaptations": 0
        }
        
        # コンテキスト履歴
        self.conversation_history = deque(maxlen=20)
        self.context_memory = deque(maxlen=self.character_memory_depth)
        
        self.logger.info(f"高度一貫性プロセッサ初期化完了 (Level: {self.consistency_level.value})")
    
    def _setup_logging(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger("AdvancedConsistency")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def enhance_consistency(self, text: str, context: str = "") -> str:
        """
        文章の一貫性を向上させる
        """
        try:
            self.stats["processed_texts"] += 1
            
            # キャラクター識別
            character_name = self._identify_character(text)
            
            # キャラクタープロファイル取得/作成
            if character_name not in self.character_profiles:
                self.character_profiles[character_name] = CharacterProfile(character_name)
                self.logger.info(f"新キャラクター '{character_name}' のプロファイルを作成")
            
            character_profile = self.character_profiles[character_name]
            
            # キャラクター切り替え検出
            if self.active_character != character_name:
                self.active_character = character_name
                self.stats["character_switches"] += 1
                self.logger.info(f"アクティブキャラクターを '{character_name}' に切り替え")
            
            # プロファイル更新
            character_profile.update_profile(text)
            
            # 一貫性レベルに応じた処理
            enhanced_text = self._apply_consistency_enhancement(
                text, character_profile, context
            )
            
            # コンテキスト履歴更新
            self.conversation_history.append({
                "character": character_name,
                "original": text,
                "enhanced": enhanced_text,
                "timestamp": time.time()
            })
            
            return enhanced_text
            
        except Exception as e:
            self.logger.error(f"一貫性向上処理エラー: {e}")
            return text
    
    def _identify_character(self, text: str) -> str:
        """テキストからキャラクター名を識別"""
        # 発話形式の検出
        speaker_match = re.match(r'^([^：「]+)：', text)
        if speaker_match:
            return speaker_match.group(1).strip()
        
        # ナレーション形式の検出
        narrator_match = re.search(r'（([^）]+)）', text)
        if narrator_match:
            narrator_text = narrator_match.group(1)
            if any(pronoun in narrator_text for pronoun in ["私", "僕", "俺", "あたし"]):
                return "主人公"
        
        # デフォルトキャラクター
        if self.active_character:
            return self.active_character
        
        return "不明"
    
    def _apply_consistency_enhancement(self, text: str, profile: CharacterProfile, context: str) -> str:
        """一貫性向上処理の適用"""
        enhanced = text
        
        if self.consistency_level == ConsistencyLevel.LIGHT:
            enhanced = self._light_enhancement(enhanced, profile)
        elif self.consistency_level == ConsistencyLevel.MODERATE:
            enhanced = self._moderate_enhancement(enhanced, profile, context)
        elif self.consistency_level == ConsistencyLevel.STRICT:
            enhanced = self._strict_enhancement(enhanced, profile, context)
        elif self.consistency_level == ConsistencyLevel.ADAPTIVE:
            enhanced = self._adaptive_enhancement(enhanced, profile, context)
        
        return enhanced
    
    def _light_enhancement(self, text: str, profile: CharacterProfile) -> str:
        """軽度の一貫性向上"""
        # 基本的な文体修正のみ
        enhanced = self._normalize_punctuation(text)
        enhanced = self._smooth_emotional_intensity(enhanced, profile, factor=0.9)
        return enhanced
    
    def _moderate_enhancement(self, text: str, profile: CharacterProfile, context: str) -> str:
        """中程度の一貫性向上"""
        enhanced = text
        
        # 基本修正
        enhanced = self._normalize_punctuation(enhanced)
        
        # 感情スムージング
        enhanced = self._smooth_emotional_intensity(enhanced, profile, factor=0.7)
        
        # 話し方パターン調整
        enhanced = self._adjust_speech_patterns(enhanced, profile)
        
        # 語彙一貫性チェック
        enhanced = self._maintain_vocabulary_consistency(enhanced, profile)
        
        return enhanced
    
    def _strict_enhancement(self, text: str, profile: CharacterProfile, context: str) -> str:
        """厳格な一貫性向上"""
        enhanced = text
        
        # 全ての中程度処理を適用
        enhanced = self._moderate_enhancement(enhanced, profile, context)
        
        # 追加の厳格処理
        enhanced = self._enforce_character_consistency(enhanced, profile)
        enhanced = self._context_aware_adjustment(enhanced, context, profile)
        
        self.stats["consistency_corrections"] += 1
        
        return enhanced
    
    def _adaptive_enhancement(self, text: str, profile: CharacterProfile, context: str) -> str:
        """適応的一貫性向上"""
        # プロファイルの一貫性スコアに基づいて強度を調整
        if profile.consistency_score >= 0.8:
            return self._light_enhancement(text, profile)
        elif profile.consistency_score >= 0.6:
            return self._moderate_enhancement(text, profile, context)
        else:
            return self._strict_enhancement(text, profile, context)
    
    def _normalize_punctuation(self, text: str) -> str:
        """句読点の正規化"""
        # 過度な反復を削減
        text = re.sub(r'！{4,}', '！！！', text)
        text = re.sub(r'？{3,}', '？？', text)
        text = re.sub(r'…{4,}', '…', text)
        text = re.sub(r'あ{8,}', 'あああああああ', text)
        
        return text
    
    def _smooth_emotional_intensity(self, text: str, profile: CharacterProfile, factor: float) -> str:
        """感情強度のスムージング"""
        if not profile.emotional_history:
            return text
        
        current_emotion = EmotionalState()
        current_emotion.update(text)
        
        if len(profile.emotional_history) > 0:
            last_emotion = profile.emotional_history[-1]
            intensity_diff = abs(current_emotion.intensity - last_emotion.intensity)
            
            # 急激な感情変化の場合にスムージング適用
            if intensity_diff > 0.5:
                self.stats["emotion_smoothing_applied"] += 1
                
                # 感情表現の強度を調整
                if current_emotion.intensity > last_emotion.intensity:
                    # 強度を下げる
                    text = self._reduce_emotional_intensity(text, factor)
                else:
                    # 強度を上げる（穏やかに）
                    text = self._enhance_emotional_intensity(text, factor)
        
        return text
    
    def _reduce_emotional_intensity(self, text: str, factor: float) -> str:
        """感情強度の削減"""
        # 過度な反復を削減
        exclamation_count = text.count("！")
        if exclamation_count > 3:
            target_count = max(1, int(exclamation_count * factor))
            text = text.replace("！", "", exclamation_count - target_count)
        
        # 反復文字の削減
        text = re.sub(r'あ{6,}', lambda m: 'あ' * max(3, int(len(m.group()) * factor)), text)
        
        return text
    
    def _enhance_emotional_intensity(self, text: str, factor: float) -> str:
        """感情強度の向上（穏やかに）"""
        # 適度な感情表現を追加
        if "。" in text and "！" not in text:
            text = text.replace("。", "！", 1)  # 最初の句点を感嘆符に
        
        return text
    
    def _adjust_speech_patterns(self, text: str, profile: CharacterProfile) -> str:
        """話し方パターンの調整"""
        if not profile.speech_patterns:
            return text
        
        # 文末表現の一貫性チェック
        current_endings = profile._extract_sentence_endings(text)
        
        if "sentence_ending" in profile.speech_patterns:
            historical_endings = profile.speech_patterns["sentence_ending"]
            if len(historical_endings) >= 3:
                # 最も使用頻度の高い文末表現を特定
                ending_freq = defaultdict(int)
                for ending_dict in historical_endings[-5:]:  # 最近5回
                    for ending, count in ending_dict.items():
                        ending_freq[ending] += count
                
                dominant_ending = max(ending_freq.items(), key=lambda x: x[1])[0]
                
                # 一貫性の低い文末表現を調整
                if dominant_ending in ["です", "ます"] and ("だ" in text or "である" in text):
                    # 丁寧語に統一
                    text = text.replace("だ。", "です。")
                    text = text.replace("である。", "です。")
                    self.stats["style_adaptations"] += 1
        
        return text
    
    def _maintain_vocabulary_consistency(self, text: str, profile: CharacterProfile) -> str:
        """語彙一貫性の維持"""
        if not profile.vocabulary_preferences:
            return text
        
        # よく使用する語彙の特定
        common_vocab = {
            word: freq for word, freq in profile.vocabulary_preferences.items()
            if freq >= 3  # 3回以上使用された語彙
        }
        
        # 類似語彙の置換提案（簡易版）
        synonyms = {
            "すごい": ["素晴らしい", "amazing"],
            "やばい": ["大変", "ひどい"],
            "かわいい": ["可愛らしい", "愛らしい"]
        }
        
        for original, alternatives in synonyms.items():
            if original in common_vocab:
                for alt in alternatives:
                    if alt in text and original not in text:
                        text = text.replace(alt, original)
                        break
        
        return text
    
    def _enforce_character_consistency(self, text: str, profile: CharacterProfile) -> str:
        """キャラクター一貫性の強制"""
        # 一人称の一貫性チェック
        pronouns_in_text = re.findall(r'(私|僕|俺|あたし|わたくし)', text)
        
        if pronouns_in_text and profile.vocabulary_preferences:
            # 最も使用頻度の高い一人称を特定
            pronoun_freq = {p: profile.vocabulary_preferences.get(p, 0) for p in ["私", "僕", "俺", "あたし"]}
            if any(freq > 0 for freq in pronoun_freq.values()):
                dominant_pronoun = max(pronoun_freq.items(), key=lambda x: x[1])[0]
                
                # 他の一人称を統一
                for pronoun in pronouns_in_text:
                    if pronoun != dominant_pronoun:
                        text = text.replace(pronoun, dominant_pronoun)
        
        return text
    
    def _context_aware_adjustment(self, text: str, context: str, profile: CharacterProfile) -> str:
        """コンテキスト認識調整"""
        if not context:
            return text
        
        # コンテキストの感情状態を分析
        context_emotion = EmotionalState()
        context_emotion.update(context)
        
        current_emotion = EmotionalState()
        current_emotion.update(text)
        
        # コンテキストとの感情の連続性をチェック
        emotion_gap = current_emotion.distance_from(context_emotion)
        
        if emotion_gap > 0.7:  # 大きな感情変化
            # 段階的な感情遷移を提案
            text = self._create_emotional_bridge(text, context_emotion, current_emotion)
        
        return text
    
    def _create_emotional_bridge(self, text: str, from_emotion: EmotionalState, to_emotion: EmotionalState) -> str:
        """感情的な橋渡し表現の作成"""
        # 感情変化の方向を分析
        intensity_change = to_emotion.intensity - from_emotion.intensity
        valence_change = to_emotion.valence - from_emotion.valence
        
        bridge_phrases = []
        
        if intensity_change > 0.3:  # 強度上昇
            bridge_phrases.append("でも、")
        elif intensity_change < -0.3:  # 強度下降
            bridge_phrases.append("そして、")
        
        if valence_change > 0.3:  # ポジティブ変化
            bridge_phrases.append("それでも、")
        elif valence_change < -0.3:  # ネガティブ変化
            bridge_phrases.append("しかし、")
        
        if bridge_phrases:
            # 最初の文に橋渡し表現を追加
            sentences = text.split("。")
            if len(sentences) > 1:
                sentences[0] = bridge_phrases[0] + sentences[0]
                text = "。".join(sentences)
        
        return text
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """包括的統計情報の取得"""
        character_stats = {}
        
        for name, profile in self.character_profiles.items():
            character_stats[name] = profile.get_profile_summary()
        
        return {
            "processing_stats": self.stats.copy(),
            "consistency_level": self.consistency_level.value,
            "active_character": self.active_character,
            "total_characters": len(self.character_profiles),
            "character_profiles": character_stats,
            "conversation_length": len(self.conversation_history),
            "device": str(self.device)
        }
    
    def reset_all_context(self):
        """全コンテキストのリセット"""
        self.conversation_history.clear()
        self.context_memory.clear()
        self.active_character = None
        
        # 統計のリセット（キャラクタープロファイルは保持）
        self.stats = {
            "processed_texts": 0,
            "character_switches": 0,
            "consistency_corrections": 0,
            "emotion_smoothing_applied": 0,
            "style_adaptations": 0
        }
        
        self.logger.info("高度一貫性プロセッサのコンテキストをリセットしました")
    
    def export_character_profiles(self, filepath: str):
        """キャラクタープロファイルのエクスポート"""
        try:
            export_data = {}
            for name, profile in self.character_profiles.items():
                export_data[name] = {
                    "summary": profile.get_profile_summary(),
                    "speech_patterns": profile.speech_patterns,
                    "vocabulary_preferences": profile.vocabulary_preferences
                }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"キャラクタープロファイルをエクスポート: {filepath}")
            
        except Exception as e:
            self.logger.error(f"エクスポートエラー: {e}")


if __name__ == "__main__":
    # テスト実行
    config = {
        "consistency_level": "moderate",
        "character_memory_depth": 10,
        "emotion_smoothing_factor": 0.7,
        "style_adaptation_rate": 0.3
    }
    
    processor = AdvancedConsistencyProcessor(config)
    
    # テストデータ
    test_conversations = [
        "樹里：あああああ…！ オス様…！",
        "樹里：でも、それでも私は…",
        "樹里：うれしいです！ とても嬉しいです！",
        "樹里：もう疲れました。"
    ]
    
    print("高度一貫性プロセッサテスト開始")
    
    for i, text in enumerate(test_conversations):
        enhanced = processor.enhance_consistency(text, "前のコンテキスト")
        print(f"\n{i+1}. 入力: {text}")
        print(f"   強化: {enhanced}")
    
    # 統計出力
    stats = processor.get_comprehensive_stats()
    print(f"\n統計情報: {json.dumps(stats, indent=2, ensure_ascii=False)}")
