# -*- coding: utf-8 -*-
"""
Enhanced NKAT Expression Engine
表現空間拡大に特化したNKAT拡張エンジン
語彙多様性、文体変化、感情表現の豊かさを大幅に向上
"""

import re
import time
import random
import json
import numpy as np
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
import os
import hashlib


@dataclass
class ExpressionVariant:
    """表現バリエーション"""
    original: str
    variants: List[str]
    context_type: str  # 'emotional', 'formal', 'casual', 'descriptive'
    usage_count: int = 0


class ExpressionExpansionEngine:
    """
    表現拡張エンジン
    単調な表現を多様で豊かな表現に変換
    """
    
    def __init__(self):
        self.expression_database = {}
        self.context_patterns = {}
        self.character_styles = {}
        self.expansion_history = deque(maxlen=1000)
        
        # 表現拡張辞書を初期化
        self._initialize_expression_database()
        
        # 統計情報
        self.stats = {
            "expressions_expanded": 0,
            "vocabulary_additions": 0,
            "style_variations": 0,
            "emotional_enhancements": 0,
            "pattern_diversifications": 0
        }
        
        print("🌟 Enhanced NKAT Expression Engine initialized")
    
    def _initialize_expression_database(self):
        """表現拡張データベースの初期化"""
        
        # 感情表現の拡張
        self.expression_database["emotional"] = {
            # 喜び系
            "嬉しい": ["歓喜に満ちた", "心躍る", "幸福感に包まれた", "喜びに震える", "感激した", "胸が躍る", "晴れやかな"],
            "嬉しいです": ["心から喜んでいます", "本当に幸せです", "感謝の気持ちでいっぱいです", "胸が熱くなります", "涙が出そうです"],
            "とても嬉しい": ["言葉にできないほど嬉しい", "夢のように嬉しい", "空に舞い上がりそうなほど嬉しい", "心が弾む", "胸がいっぱいになる"],
            
            # 驚き系
            "わあ": ["なんということでしょう", "信じられない", "まさか", "これは驚いた", "目を疑う"],
            "すごい": ["圧倒的", "驚異的", "息を呑む", "言葉を失う", "想像を超える", "壮観な", "眩しい"],
            "きれい": ["美しい", "華麗な", "優雅な", "洗練された", "気品ある", "上品な", "エレガントな"],
            
            # 興奮系
            "あああああ": ["胸が高鳴る", "心臓が跳ね上がる", "血がたぎる", "全身が震える", "息が荒くなる"],
            "うわああああ": ["圧倒される", "衝撃が走る", "雷に打たれたよう", "稲妻が走る", "全てが変わる瞬間"],
            
            # 困惑系
            "難しい": ["複雑で悩ましい", "頭を抱える", "思考が混乱する", "答えが見つからない", "迷宮入りしそうな"]
        }
        
        # 文体パターンの拡張
        self.expression_database["style"] = {
            "です": ["ですね", "でございます", "なのです", "ですから", "ですが"],
            "ます": ["ますね", "ますよ", "ますから", "ますが", "ますし"],
            "だ": ["だね", "だよ", "だから", "だし", "だけど"],
            "である": ["であるね", "であるから", "であるが", "であるし", "であった"]
        }
        
        # 接続詞・副詞の拡張
        self.expression_database["connective"] = {
            "そうですね": ["そうですね、確かに", "なるほど", "おっしゃる通りです", "その通りです", "いかにも"],
            "でも": ["しかし", "けれど", "ただ", "それでも", "とはいえ", "一方で"],
            "だから": ["それで", "なので", "従って", "ゆえに", "というわけで", "そういうわけで"],
            "やっぱり": ["やはり", "結局", "つまるところ", "案の定", "予想通り", "思った通り"]
        }
        
        # 感嘆詞の多様化
        self.expression_database["interjection"] = {
            "！": ["！", "…！", "っ！", "！？"],
            "？": ["？", "…？", "っ？", "！？"],
            "…": ["…", "〜", "……", "…っ"],
            "〜": ["〜", "…", "ー", "～～"]
        }
        
        # キャラクター別の特徴的表現
        self.character_expressions = {
            "樹里": {
                "興奮": ["胸が張り裂けそう", "心臓が爆発しそう", "全身が火照る", "意識が飛びそう"],
                "喜び": ["天にも昇る心地", "夢心地", "この上ない幸福", "至福の瞬間"],
                "驚き": ["目を見張る", "言葉を失う", "息を呑む", "心臓が止まりそう"]
            },
            "美里": {
                "喜び": ["心が躍る", "笑顔がこぼれる", "幸せいっぱい", "気分最高"],
                "驚き": ["びっくり", "まさか", "信じられない", "どうしよう"],
                "困惑": ["どうしたらいいの", "分からない", "迷っちゃう", "困ったな"]
            }
        }
    
    def expand_expression(self, text: str, character: str = "general", context: str = "") -> str:
        """
        表現の拡張処理
        
        Args:
            text: 拡張対象テキスト
            character: キャラクター名
            context: コンテキスト情報
            
        Returns:
            拡張されたテキスト
        """
        
        if not text or len(text.strip()) == 0:
            return text
        
        print(f"🔍 表現拡張開始: {text[:50]}...")
        
        expanded_text = text
        expansion_applied = False
        
        # 1. 反復の単調性を解決
        expanded_text, repetition_fixed = self._diversify_repetitions(expanded_text)
        if repetition_fixed:
            expansion_applied = True
            self.stats["pattern_diversifications"] += 1
        
        # 2. 感情表現の豊かさを向上
        expanded_text, emotion_enhanced = self._enhance_emotional_expressions(expanded_text, character)
        if emotion_enhanced:
            expansion_applied = True
            self.stats["emotional_enhancements"] += 1
        
        # 3. 語彙の多様性を向上
        expanded_text, vocab_expanded = self._expand_vocabulary(expanded_text)
        if vocab_expanded:
            expansion_applied = True
            self.stats["vocabulary_additions"] += 1
        
        # 4. 文体の変化を追加
        expanded_text, style_varied = self._vary_sentence_styles(expanded_text)
        if style_varied:
            expansion_applied = True
            self.stats["style_variations"] += 1
        
        # 5. キャラクター固有の表現を追加
        expanded_text = self._add_character_specific_expressions(expanded_text, character)
        
        # 拡張履歴に記録
        if expansion_applied:
            self.expansion_history.append({
                "original": text,
                "expanded": expanded_text,
                "character": character,
                "timestamp": time.time(),
                "improvements": {
                    "repetition_fixed": repetition_fixed,
                    "emotion_enhanced": emotion_enhanced,
                    "vocab_expanded": vocab_expanded,
                    "style_varied": style_varied
                }
            })
            self.stats["expressions_expanded"] += 1
        
        print(f"✨ 表現拡張完了: {expanded_text[:50]}... ({'変更あり' if expansion_applied else '変更なし'})")
        
        return expanded_text
    
    def _diversify_repetitions(self, text: str) -> Tuple[str, bool]:
        """反復の多様化"""
        
        changed = False
        result = text
        
        # 完全一致する語句の反復を検出・多様化
        words = re.findall(r'[ぁ-ゖァ-ヺー一-龯]+', text)
        word_positions = {}
        
        for i, word in enumerate(words):
            if len(word) >= 2:
                if word not in word_positions:
                    word_positions[word] = []
                word_positions[word].append(i)
        
        # 2回以上出現する語句を多様化
        for word, positions in word_positions.items():
            if len(positions) >= 2 and word in self.expression_database["emotional"]:
                variants = self.expression_database["emotional"][word]
                
                # 反復箇所に異なる表現を適用
                for i, pos in enumerate(positions[1:], 1):  # 最初は保持
                    if i < len(variants):
                        replacement = variants[i-1]
                        # 単語境界を考慮した置換
                        pattern = r'\b' + re.escape(word) + r'\b'
                        result = re.sub(pattern, replacement, result, count=1)
                        changed = True
        
        # 文字レベルの反復も多様化
        for char in ['あ', 'う', 'お', 'わ', 'ん']:
            pattern = f'{char}{{4,}}'  # 4文字以上の連続
            matches = re.findall(pattern, result)
            for match in matches:
                if len(match) > 3:
                    # 段階的な感情表現に変換
                    variations = [
                        f"{char}{char}…",
                        f"{char}っ…",
                        f"{char}あ…",
                        f"{char}ー…"
                    ]
                    replacement = random.choice(variations)
                    result = result.replace(match, replacement, 1)
                    changed = True
        
        return result, changed
    
    def _enhance_emotional_expressions(self, text: str, character: str) -> Tuple[str, bool]:
        """感情表現の強化"""
        
        changed = False
        result = text
        
        # 感情表現の検出と強化
        emotional_patterns = [
            (r'(嬉しい)(?![\w])', self.expression_database["emotional"].get("嬉しい", [])),
            (r'(すごい)(?![\w])', self.expression_database["emotional"].get("すごい", [])),
            (r'(きれい)(?![\w])', self.expression_database["emotional"].get("きれい", [])),
            (r'(わあ)(?![\w])', self.expression_database["emotional"].get("わあ", [])),
        ]
        
        for pattern, replacements in emotional_patterns:
            if replacements and re.search(pattern, result):
                replacement = random.choice(replacements)
                result = re.sub(pattern, replacement, result, count=1)
                changed = True
        
        # 感嘆符の多様化
        if "！！！" in result:
            variations = ["！", "…！", "！？", "っ！"]
            result = result.replace("！！！", random.choice(variations))
            changed = True
        
        # 省略記号の多様化
        if "……" in result:
            variations = ["…", "〜", "ー", "……っ"]
            result = result.replace("……", random.choice(variations))
            changed = True
        
        return result, changed
    
    def _expand_vocabulary(self, text: str) -> Tuple[str, bool]:
        """語彙の拡張"""
        
        changed = False
        result = text
        
        # 接続詞・副詞の多様化
        for original, variants in self.expression_database["connective"].items():
            if original in result:
                replacement = random.choice(variants)
                result = result.replace(original, replacement, 1)
                changed = True
        
        # 語尾の多様化
        patterns = [
            (r'です。', ["ですね。", "ですよ。", "でございます。"]),
            (r'ます。', ["ますね。", "ますよ。", "ますから。"]),
            (r'だ。', ["だね。", "だよ。", "だし。"])
        ]
        
        for pattern, replacements in patterns:
            if re.search(pattern, result):
                replacement = random.choice(replacements)
                result = re.sub(pattern, replacement, result, count=1)
                changed = True
        
        return result, changed
    
    def _vary_sentence_styles(self, text: str) -> Tuple[str, bool]:
        """文体の変化"""
        
        changed = False
        result = text
        
        sentences = re.split(r'([。！？])', result)
        if len(sentences) > 3:  # 複数文がある場合
            
            # 文長の変化を追加
            for i in range(0, len(sentences)-1, 2):  # 文のみ対象
                sentence = sentences[i].strip()
                if len(sentence) > 0:
                    
                    # 短い文に感情的な修飾を追加
                    if len(sentence) < 10:
                        emotional_modifiers = ["本当に", "とても", "すごく", "心から"]
                        if not any(mod in sentence for mod in emotional_modifiers):
                            modifier = random.choice(emotional_modifiers)
                            sentences[i] = f"{modifier}{sentence}"
                            changed = True
                    
                    # 長い文を分割
                    elif len(sentence) > 30 and "、" in sentence:
                        parts = sentence.split("、", 1)
                        if len(parts) == 2:
                            sentences[i] = f"{parts[0]}。{parts[1]}"
                            changed = True
            
            result = "".join(sentences)
        
        return result, changed
    
    def _add_character_specific_expressions(self, text: str, character: str) -> str:
        """キャラクター固有表現の追加"""
        
        if character not in self.character_expressions:
            return text
        
        char_expressions = self.character_expressions[character]
        result = text
        
        # 感情状態に応じた表現を追加
        if "あああああ" in text or "うわああああ" in text:
            # 興奮状態
            if "興奮" in char_expressions:
                additional = random.choice(char_expressions["興奮"])
                result = f"{result} {additional}…！"
        
        elif "嬉しい" in text:
            # 喜びの状態
            if "喜び" in char_expressions:
                additional = random.choice(char_expressions["喜び"])
                result = result.replace("嬉しい", f"{additional}で嬉しい")
        
        elif "わあ" in text or "すごい" in text:
            # 驚きの状態
            if "驚き" in char_expressions:
                additional = random.choice(char_expressions["驚き"])
                result = f"{result} {additional}…！"
        
        return result
    
    def get_expansion_stats(self) -> Dict:
        """拡張統計の取得"""
        
        recent_expansions = list(self.expansion_history)[-10:]
        
        return {
            "total_expansions": self.stats["expressions_expanded"],
            "vocabulary_additions": self.stats["vocabulary_additions"],
            "style_variations": self.stats["style_variations"],
            "emotional_enhancements": self.stats["emotional_enhancements"],
            "pattern_diversifications": self.stats["pattern_diversifications"],
            "recent_expansions": len(recent_expansions),
            "database_size": {
                "emotional": len(self.expression_database["emotional"]),
                "style": len(self.expression_database["style"]),
                "connective": len(self.expression_database["connective"])
            }
        }
    
    def analyze_expression_diversity(self, text: str) -> Dict:
        """表現多様性の分析"""
        
        # 語彙多様性
        words = re.findall(r'[ぁ-ゖァ-ヺー一-龯]+', text)
        unique_words = set(words)
        vocab_diversity = len(unique_words) / max(len(words), 1)
        
        # 文体多様性
        sentences = text.split("。")
        sentence_patterns = []
        for sentence in sentences:
            if "です" in sentence:
                sentence_patterns.append("polite")
            elif "だ" in sentence:
                sentence_patterns.append("casual")
            elif "である" in sentence:
                sentence_patterns.append("formal")
            else:
                sentence_patterns.append("neutral")
        
        pattern_diversity = len(set(sentence_patterns)) / max(len(sentence_patterns), 1)
        
        # 感情表現多様性
        emotional_chars = text.count("！") + text.count("？") + text.count("…")
        emotion_density = emotional_chars / max(len(text), 1)
        
        return {
            "vocabulary_diversity": vocab_diversity,
            "pattern_diversity": pattern_diversity,
            "emotion_density": emotion_density,
            "total_words": len(words),
            "unique_words": len(unique_words),
            "sentence_count": len([s for s in sentences if s.strip()])
        }


def test_expression_expansion():
    """表現拡張エンジンのテスト"""
    
    engine = ExpressionExpansionEngine()
    
    test_cases = [
        {
            "name": "感情表現の限定性",
            "text": "嬉しいです。とても嬉しいです。本当に嬉しいです。嬉しい気持ちです。",
            "character": "樹里"
        },
        {
            "name": "反復表現の単調性",
            "text": "あああああ…！ あああああ…！ うわああああ…！ あああああ…！",
            "character": "樹里"
        },
        {
            "name": "語彙の限定性",
            "text": "そうですね。そうですね。でも難しいですね。やっぱり難しいですね。",
            "character": "美里"
        },
        {
            "name": "感嘆表現の貧困性",
            "text": "わあ！わあ！すごい！わあ！きれい！わあ！",
            "character": "美里"
        }
    ]
    
    print("🚀 Enhanced NKAT Expression Engine Test")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {case['name']}")
        print(f"Character: {case['character']}")
        print(f"Original: {case['text']}")
        
        # 拡張前の分析
        before_analysis = engine.analyze_expression_diversity(case['text'])
        
        # 表現拡張実行
        expanded = engine.expand_expression(case['text'], case['character'])
        
        # 拡張後の分析
        after_analysis = engine.analyze_expression_diversity(expanded)
        
        print(f"Expanded: {expanded}")
        print(f"\n📊 Diversity Analysis:")
        print(f"  Vocabulary: {before_analysis['vocabulary_diversity']:.3f} → {after_analysis['vocabulary_diversity']:.3f}")
        print(f"  Patterns: {before_analysis['pattern_diversity']:.3f} → {after_analysis['pattern_diversity']:.3f}")
        print(f"  Emotion: {before_analysis['emotion_density']:.3f} → {after_analysis['emotion_density']:.3f}")
        print(f"  Words: {before_analysis['unique_words']} → {after_analysis['unique_words']}")
        
        print("-" * 50)
    
    # 統計表示
    stats = engine.get_expansion_stats()
    print(f"\n📈 Expansion Statistics:")
    print(f"Total Expansions: {stats['total_expansions']}")
    print(f"Vocabulary Additions: {stats['vocabulary_additions']}")
    print(f"Style Variations: {stats['style_variations']}")
    print(f"Emotional Enhancements: {stats['emotional_enhancements']}")
    print(f"Pattern Diversifications: {stats['pattern_diversifications']}")


# NKATとの統合クラス
class NKATExpressionIntegration:
    """NKAT統合表現拡張システム"""
    
    def __init__(self, easy_novel_context):
        self.ctx = easy_novel_context
        self.expression_engine = ExpressionExpansionEngine()
        
        # 統合設定
        self.integration_enabled = self.ctx.get("nkat_expression_expansion", True)
        self.expansion_strength = self.ctx.get("expression_expansion_strength", 0.7)
        
        print("🎯 NKAT Expression Integration initialized")
    
    def enhance_text_with_expression_expansion(self, prompt: str, llm_output: str) -> str:
        """表現拡張を含む文章強化"""
        
        if not self.integration_enabled:
            return llm_output
        
        # キャラクター抽出
        character = self._extract_character(llm_output)
        
        # 表現拡張実行
        expanded = self.expression_engine.expand_expression(
            llm_output, character, prompt
        )
        
        return expanded
    
    def _extract_character(self, text: str) -> str:
        """テキストからキャラクター名を抽出"""
        
        # 発話形式の検出
        speaker_match = re.match(r'^([^：「]+)：', text)
        if speaker_match:
            return speaker_match.group(1).strip()
        
        # デフォルト
        return self.ctx.get("char_name", "general")
    
    def get_integration_stats(self) -> Dict:
        """統合統計の取得"""
        
        engine_stats = self.expression_engine.get_expansion_stats()
        
        return {
            "integration_enabled": self.integration_enabled,
            "expansion_strength": self.expansion_strength,
            "engine_stats": engine_stats,
            "context_character": self.ctx.get("char_name", "unknown")
        }


if __name__ == "__main__":
    test_expression_expansion() 