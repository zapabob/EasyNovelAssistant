# -*- coding: utf-8 -*-
"""
高度語句反復抑制システム v2 (Advanced Repetition Suppression System v2)
同じ語句の反復を検出し、自然な表現に修正する - 成功率80%+を目指す改良版
"""

import re
import time
import json
import os
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict, Counter
from dataclasses import dataclass
import numpy as np
from tqdm import tqdm


@dataclass
class RepetitionPattern:
    """反復パターンの分析結果"""
    pattern: str
    count: int
    positions: List[int]
    pattern_type: str  # 'exact', 'similar', 'phonetic'
    severity: float  # 0.0-1.0の重要度
    similarity_score: float = 0.0  # デバッグ用類似度スコア
    suppression_result: str = ""  # 抑制結果タグ（MISS/OVER/OK）


@dataclass 
class SuppressionMetrics:
    """抑制効果メトリクス"""
    input_length: int
    output_length: int
    patterns_detected: int
    patterns_suppressed: int
    detection_misses: int
    over_compressions: int
    processing_time_ms: float
    success_rate: float


class AdvancedRepetitionSuppressor:
    """
    高度語句反復抑制システム v2
    
    新機能 v2:
    1. デバッグ強化（MISS/OVER検出）
    2. n-gramマスク併用
    3. 動的Repeat-Penalty
    4. MeCab/UniDic統合準備
    5. 成功率メトリクス詳細化
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # 基本設定パラメータ
        self.min_repeat_threshold = self.config.get('min_repeat_threshold', 1)  # 同語反復対応で厳格化
        self.max_distance = self.config.get('max_distance', 30)  # 検出距離短縮
        self.similarity_threshold = self.config.get('similarity_threshold', 0.68)  # 閾値下げる
        self.phonetic_threshold = self.config.get('phonetic_threshold', 0.8)  # 音韻閾値下げる
        
        # 同語反復対応パラメータ（v2強化）
        self.enable_aggressive_mode = self.config.get('enable_aggressive_mode', True)
        self.interjection_sensitivity = self.config.get('interjection_sensitivity', 0.5)  # 感度上げる
        self.exact_match_priority = self.config.get('exact_match_priority', True)
        self.character_repetition_limit = self.config.get('character_repetition_limit', 3)  # 制限厳格化
        
        # v2新機能パラメータ
        self.debug_mode = self.config.get('debug_mode', True)
        self.ngram_block_size = self.config.get('ngram_block_size', 4)  # 4-gram以上をブロック
        self.enable_drp = self.config.get('enable_drp', True)  # 動的Repeat-Penalty
        self.drp_alpha = self.config.get('drp_alpha', 0.5)
        self.drp_window = self.config.get('drp_window', 10)
        
        # 言語処理強化準備
        self.use_mecab = self.config.get('use_mecab', False)
        self.use_jaccard_similarity = self.config.get('use_jaccard_similarity', True)
        
        # メトリクス収集
        self.session_metrics = []
        self.total_success_count = 0
        self.total_attempts = 0
        
        # 反復パターンの分析履歴
        self.pattern_history = []
        self.character_patterns = defaultdict(list)
        self.replacement_cache = {}
        
        # 日本語固有の処理
        self.katakana_map = str.maketrans(
            'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン',
            'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'
        )
        
        # 感嘆詞・間投詞のパターン（v2拡張）
        self.interjection_patterns = [
            r'([あおうえい])\1{2,}',  # あああ, おおお等
            r'([きひんしち])\1{1,}っ*',  # きき, ひひ等
            r'([っー〜]){3,}',  # っっっ, ーーー等
            r'([！？]){2,}',  # !!!, ???等
            r'(そや|だめ|いや){2,}',  # そやそや等関西弁対応
            r'([あ-ん])\1{2,}[っ〜…！？]*'  # 一般的な重複パターン
        ]
        
        # 代替表現辞書（v2拡張版）
        self.load_replacement_dictionary()
        
        # デバッグログ設定
        self.debug_log = []
        
        # n-gramブロック用辞書
        self.ngram_cache = set()
        
        mode_text = "v2アグレッシブモード" if self.enable_aggressive_mode else "v2標準モード"
        features = []
        if self.debug_mode:
            features.append("デバッグ強化")
        if self.ngram_block_size > 0:
            features.append(f"{self.ngram_block_size}-gramブロック")
        if self.enable_drp:
            features.append("DRP")
        
        feature_text = "(" + ", ".join(features) + ")" if features else ""
        print(f"🔄 高度語句反復抑制システムv2が初期化されました（{mode_text}）{feature_text}")

    def load_replacement_dictionary(self):
        """代替表現辞書の読み込み（v2拡張版）"""
        self.replacement_dict = {
            # 感嘆表現（拡張）
            'あああ': ['ああ', 'はあ', 'うう', 'ふう'],
            'ああああ': ['ああ', 'はあっ', 'ふうう'],
            'あああああ': ['ああっ', 'はあっ'],
            'うううう': ['うう', 'んん', 'ふう'],
            'おおおお': ['おお', 'わあ', 'ほお'],
            'きゃああ': ['きゃあ', 'いや', 'わあ'],
            'ひいいい': ['ひい', 'いや', 'うう'],
            
            # 濁音・拗音反復（拡張）
            'っっっ': ['っ', 'ん', ''],
            'っっっっ': ['っ', ''],
            '〜〜〜': ['〜', '…', ''],
            '〜〜〜〜': ['〜', ''],
            '…………': ['…', '〜', ''],
            '………………': ['…', ''],
            '！！！！': ['！', '！？', ''],
            '！！！！！': ['！！', ''],
            '？？？？': ['？', '！？', ''],
            
            # 語尾反復（拡張）
            'ですです': ['です', 'ですね', 'ですよ'],
            'ますます': ['ます', 'ますね', 'ますよ'],
            'だっただった': ['だった', 'でした', 'だったね'],
            'でしょでしょ': ['でしょう', 'ですね', 'でしょうね'],
            'のですのです': ['のです', 'んです', 'のですよ'],
            
            # 接続詞反復（拡張）
            'そしてそして': ['そして', 'また', 'それから'],
            'でもでも': ['でも', 'しかし', 'だけど'],
            'だからだから': ['だから', 'それで', 'なので'],
            'それでそれで': ['それで', 'だから', 'そして'],
            'つまりつまり': ['つまり', 'すなわち', '要するに'],
            
            # 関西弁対応
            'そやそや': ['そや', 'ほんま', 'せやな'],
            'やなやな': ['やな', 'いややな', 'あかんな'],
            'あかんあかん': ['あかん', 'だめ', 'いや'],
            
            # 感情表現（拡張）
            '嬉しい嬉しい': ['とても嬉しい', '本当に嬉しい', 'すごく嬉しい'],
            '悲しい悲しい': ['とても悲しい', '本当に悲しい', 'すごく悲しい'],
            '怖い怖い': ['とても怖い', '本当に怖い', 'すごく怖い'],
            '痛い痛い': ['とても痛い', '本当に痛い', 'すごく痛い'],
            
            # キャラクター固有表現（拡張）
            'オス様オス様': ['オス様', '主人様', 'ご主人様'],
            'お兄ちゃんお兄ちゃん': ['お兄ちゃん', 'おにいちゃん'],
            'お姉ちゃんお姉ちゃん': ['お姉ちゃん', 'おねえちゃん'],
            
            # 頻出反復パターン
            'はいはい': ['はい', 'ええ', 'そうです'],
            'いえいえ': ['いえ', 'いいえ', 'そんな'],
            'ほんとほんと': ['ほんと', '本当に', 'マジで']
        }

    def suppress_repetitions_with_debug(self, text: str, character_name: str = None) -> Tuple[str, SuppressionMetrics]:
        """
        反復抑制処理（デバッグ強化版）
        
        Returns:
            (処理済みテキスト, 詳細メトリクス)
        """
        start_time = time.time()
        original_text = text
        
        # 分析フェーズ
        analysis = self.analyze_text(text, character_name)
        
        # n-gramブロック前処理
        if self.ngram_block_size > 0:
            text = self._apply_ngram_blocking(text)
        
        # 動的Repeat-Penalty適用
        if self.enable_drp:
            text = self._apply_dynamic_repeat_penalty(text)
        
        # 従来の抑制処理
        patterns = []
        for pattern_type, pattern_list in analysis['patterns'].items():
            patterns.extend(pattern_list)
        
        # パターンを重要度でソート
        patterns.sort(key=lambda p: p.severity, reverse=True)
        
        suppressed_count = 0
        missed_count = 0
        over_compressed_count = 0
        
        for pattern in patterns:
            if pattern.severity > 0.1:  # 閾値以上のパターンのみ処理
                old_text = text
                text = self._apply_suppression_with_debug(text, pattern, character_name)
                
                if text != old_text:
                    suppressed_count += 1
                    pattern.suppression_result = "OK"
                    
                    # 過剰圧縮チェック
                    if self._is_over_compressed(old_text, text):
                        over_compressed_count += 1
                        pattern.suppression_result = "OVER"
                        if self.debug_mode:
                            self.debug_log.append(f"<OVER> {pattern.pattern} -> 過剰圧縮検出")
                else:
                    missed_count += 1
                    pattern.suppression_result = "MISS"
                    if self.debug_mode:
                        self.debug_log.append(f"<MISS> {pattern.pattern} -> 抑制失敗 (sim={pattern.similarity_score:.2f} < {self.similarity_threshold:.2f})")
        
        # 最終的な隣接重複除去
        text = self._remove_adjacent_duplicates_v2(text)
        
        # メトリクス計算
        processing_time = (time.time() - start_time) * 1000
        total_patterns = len(patterns)
        success_rate = (suppressed_count / total_patterns) if total_patterns > 0 else 1.0
        
        metrics = SuppressionMetrics(
            input_length=len(original_text),
            output_length=len(text),
            patterns_detected=total_patterns,
            patterns_suppressed=suppressed_count,
            detection_misses=missed_count,
            over_compressions=over_compressed_count,
            processing_time_ms=processing_time,
            success_rate=success_rate
        )
        
        # セッションメトリクス記録
        self.session_metrics.append(metrics)
        self.total_attempts += 1
        if success_rate >= 0.8:
            self.total_success_count += 1
        
        # デバッグ出力
        if self.debug_mode and (missed_count > 0 or over_compressed_count > 0):
            print(f"🐛 デバッグ: 検知漏れ {missed_count}件, 過剰圧縮 {over_compressed_count}件")
            print(f"    成功率: {success_rate:.1%}, 処理時間: {processing_time:.1f}ms")
        
        return text, metrics

    def _apply_ngram_blocking(self, text: str) -> str:
        """n-gramレベルでの反復ブロック"""
        if self.ngram_block_size <= 0:
            return text
        
        # n-gramを抽出してブロック対象を特定
        ngrams = []
        for i in range(len(text) - self.ngram_block_size + 1):
            ngram = text[i:i + self.ngram_block_size]
            if re.search(r'[ひらがなカタカナ漢字]', ngram):
                ngrams.append((ngram, i))
        
        # 重複n-gramを検出
        ngram_counts = Counter([ngram for ngram, _ in ngrams])
        repeated_ngrams = {ngram for ngram, count in ngram_counts.items() if count > 1}
        
        if not repeated_ngrams:
            return text
        
        # 重複箇所を特定して除去
        result = text
        offset = 0
        
        for ngram, pos in ngrams:
            if ngram in repeated_ngrams:
                # 2回目以降の出現を削除
                if result.count(ngram) > 1:
                    # より賢い削除（文脈を考慮）
                    result = self._smart_ngram_removal(result, ngram)
        
        if result != text and self.debug_mode:
            self.debug_log.append(f"n-gramブロック適用: {len(repeated_ngrams)}個のパターンを処理")
        
        return result

    def _smart_ngram_removal(self, text: str, ngram: str) -> str:
        """文脈を考慮したn-gram除去"""
        positions = []
        start = 0
        while True:
            pos = text.find(ngram, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        if len(positions) <= 1:
            return text
        
        # 最初の出現を保持し、2回目以降を削除
        # ただし、文脈的に自然な位置を保持
        result = text
        for pos in reversed(positions[1:]):  # 後ろから削除
            # 周辺文脈をチェック
            before = text[max(0, pos-5):pos] if pos > 0 else ""
            after = text[pos+len(ngram):pos+len(ngram)+5] if pos+len(ngram) < len(text) else ""
            
            # 句読点や区切りがある場合は削除しやすい
            if any(char in before + after for char in "。、！？\n「」"):
                result = result[:pos] + result[pos+len(ngram):]
        
        return result

    def _apply_dynamic_repeat_penalty(self, text: str) -> str:
        """動的Repeat-Penalty適用"""
        if not self.enable_drp:
            return text
        
        # 簡易的なDRP実装（トークンレベルではなく文字レベル）
        window_size = self.drp_window
        result = ""
        
        for i, char in enumerate(text):
            if i < window_size:
                result += char
                continue
            
            # ウィンドウ内での文字出現率を計算
            window = text[i-window_size:i]
            char_count = window.count(char)
            repeat_rate = char_count / window_size
            
            # ペナルティ適用（高い反復率の文字をスキップ）
            penalty_threshold = 0.3 + self.drp_alpha * repeat_rate
            
            if repeat_rate < penalty_threshold or char in "。、！？\n":
                result += char
            # else: 文字をスキップ（実質的なペナルティ）
        
        if result != text and self.debug_mode:
            self.debug_log.append(f"DRP適用: {len(text) - len(result)}文字を抑制")
        
        return result

    def _apply_suppression_with_debug(self, text: str, pattern: RepetitionPattern, character_name: str = None) -> str:
        """デバッグ情報付きの抑制処理"""
        old_text = text
        
        # 既存の抑制ロジック
        if pattern.pattern_type == 'exact':
            text = self._suppress_exact_repetition(text, pattern)
        elif pattern.pattern_type == 'character':
            text = self._suppress_character_repetition(text, pattern)
        elif pattern.pattern_type == 'interjection':
            text = self._suppress_interjection_overuse(text, pattern)
        elif pattern.pattern_type == 'word' and self.enable_aggressive_mode:
            text = self._suppress_word_repetition(text, pattern)
        
        # 類似度スコアを記録（デバッグ用）
        if old_text != text:
            pattern.similarity_score = self._calculate_similarity(old_text, text)
        
        return text

    def _is_over_compressed(self, original: str, compressed: str) -> bool:
        """過剰圧縮の検出"""
        if len(compressed) < len(original) * 0.5:  # 50%以上短縮された場合
            return True
        
        # 重要な情報の消失チェック
        important_patterns = [
            r'[。！？]',  # 句読点
            r'[「」]',    # カギ括弧
            r'[あ-ん]{3,}',  # 長いひらがな語
            r'[ァ-ン]{3,}',  # 長いカタカナ語
        ]
        
        for pattern in important_patterns:
            original_count = len(re.findall(pattern, original))
            compressed_count = len(re.findall(pattern, compressed))
            
            if original_count > 0 and compressed_count < original_count * 0.7:
                return True
        
        return False

    def _remove_adjacent_duplicates_v2(self, text: str) -> str:
        """隣接重複除去（v2改良版）"""
        if not text:
            return text
        
        # より精密な隣接重複検出
        result = []
        i = 0
        
        while i < len(text):
            current_char = text[i]
            
            # 連続する同じ文字をカウント
            consecutive_count = 1
            j = i + 1
            while j < len(text) and text[j] == current_char:
                consecutive_count += 1
                j += 1
            
            # 制限に従って文字を追加
            if re.match(r'[あ-んア-ンーっ]', current_char):
                # ひらがな・カタカナは制限あり
                limit = self.character_repetition_limit
                add_count = min(consecutive_count, limit)
            elif current_char in "！？":
                # 感嘆符は最大2個
                add_count = min(consecutive_count, 2)
            elif current_char in "…〜":
                # 省略記号は最大3個
                add_count = min(consecutive_count, 3)
            else:
                # その他は制限なし
                add_count = consecutive_count
            
            result.extend([current_char] * add_count)
            i = j
        
        final_result = ''.join(result)
        
        # フレーズレベルの隣接重複除去
        final_result = self._remove_phrase_duplicates(final_result)
        
        return final_result

    def _remove_phrase_duplicates(self, text: str) -> str:
        """フレーズレベルの隣接重複除去"""
        # 2-5文字のフレーズ重複を検出・除去
        for length in range(5, 1, -1):  # 長いフレーズから処理
            pattern = r'(.{' + str(length) + r'})\1+'
            
            def replace_duplicate(match):
                original_phrase = match.group(1)
                # フレーズが意味のある内容かチェック
                if re.search(r'[あ-んア-ン漢字]', original_phrase):
                    return original_phrase  # 1回だけ残す
                return match.group(0)  # 記号等はそのまま
            
            text = re.sub(pattern, replace_duplicate, text)
        
        return text

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """テキスト類似度計算（デバッグ用）"""
        if not text1 or not text2:
            return 0.0
        
        # Jaccard類似度
        if self.use_jaccard_similarity:
            set1 = set(text1)
            set2 = set(text2)
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            return intersection / union if union > 0 else 0.0
        else:
            # 従来のdifflib
            import difflib
            return difflib.SequenceMatcher(None, text1, text2).ratio()

    def get_debug_report(self) -> Dict:
        """デバッグレポートの生成"""
        if not self.session_metrics:
            return {"message": "セッションデータがありません"}
        
        # 統計計算
        total_sessions = len(self.session_metrics)
        avg_success_rate = sum(m.success_rate for m in self.session_metrics) / total_sessions
        avg_processing_time = sum(m.processing_time_ms for m in self.session_metrics) / total_sessions
        
        total_patterns = sum(m.patterns_detected for m in self.session_metrics)
        total_misses = sum(m.detection_misses for m in self.session_metrics)
        total_over_compressions = sum(m.over_compressions for m in self.session_metrics)
        
        miss_rate = (total_misses / total_patterns) if total_patterns > 0 else 0
        over_compression_rate = (total_over_compressions / total_patterns) if total_patterns > 0 else 0
        
        # 最新のデバッグログ
        recent_debug_logs = self.debug_log[-20:] if len(self.debug_log) > 20 else self.debug_log
        
        return {
            "session_summary": {
                "total_sessions": total_sessions,
                "overall_success_rate": avg_success_rate,
                "target_achievement": avg_success_rate >= 0.8,
                "avg_processing_time_ms": avg_processing_time
            },
            "failure_analysis": {
                "detection_miss_rate": miss_rate,
                "over_compression_rate": over_compression_rate,
                "primary_issue": "detection_miss" if miss_rate > over_compression_rate else "over_compression"
            },
            "performance_metrics": {
                "total_patterns_detected": total_patterns,
                "total_misses": total_misses,
                "total_over_compressions": total_over_compressions,
                "processing_efficiency": f"{total_patterns / avg_processing_time:.1f} patterns/ms"
            },
            "recent_debug_logs": recent_debug_logs,
            "recommendations": self._generate_tuning_recommendations(miss_rate, over_compression_rate, avg_success_rate)
        }

    def _generate_tuning_recommendations(self, miss_rate: float, over_compression_rate: float, success_rate: float) -> List[str]:
        """チューニング推奨事項の生成"""
        recommendations = []
        
        if success_rate < 0.8:
            if miss_rate > 0.15:
                recommendations.append(f"検知漏れ率 {miss_rate:.1%} が高い → similarity_threshold を {self.similarity_threshold:.2f} から {self.similarity_threshold - 0.02:.2f} に下げる")
                recommendations.append("min_repeat_threshold を 1 に設定（より厳格な検出）")
            
            if over_compression_rate > 0.05:
                recommendations.append(f"過剰圧縮率 {over_compression_rate:.1%} が高い → character_repetition_limit を {self.character_repetition_limit} から {self.character_repetition_limit + 1} に上げる")
                recommendations.append("enable_aggressive_mode を False に設定")
            
            if miss_rate <= 0.1 and over_compression_rate <= 0.05:
                recommendations.append("n-gramブロックサイズを 4 から 5 に拡大")
                recommendations.append("DRPアルファ値を 0.5 から 0.6 に調整")
        else:
            recommendations.append("✅ 目標成功率 80% を達成しています！")
        
        return recommendations

    def analyze_text(self, text: str, character_name: str = None) -> Dict:
        """
        テキストの反復パターンを包括的に分析
        
        Args:
            text: 分析対象テキスト
            character_name: キャラクター名（キャラ別分析用）
            
        Returns:
            分析結果辞書
        """
        print(f"🔍 反復分析開始: {len(text)}文字")
        
        analysis_start = time.time()
        
        patterns = {
            'exact_repetitions': self._detect_exact_repetitions(text),
            'character_repetitions': self._detect_character_repetitions(text),
            'phonetic_repetitions': self._detect_phonetic_repetitions(text),
            'semantic_repetitions': self._detect_semantic_repetitions(text),
            'interjection_overuse': self._detect_interjection_overuse(text)
        }
        
        # アグレッシブモードでは語レベルの検出も追加
        if self.enable_aggressive_mode:
            patterns['word_repetitions'] = self._detect_word_repetitions(text)
        
        # 総合的な反復スコア計算
        total_severity = sum(
            sum(p.severity for p in pattern_list)
            for pattern_list in patterns.values()
        )
        
        # キャラクター別パターンの記録
        if character_name:
            self.character_patterns[character_name].extend([
                p for pattern_list in patterns.values() 
                for p in pattern_list
            ])
        
        analysis_time = time.time() - analysis_start
        
        result = {
            'patterns': patterns,
            'total_severity': total_severity,
            'analysis_time': analysis_time,
            'character': character_name,
            'text_length': len(text),
            'timestamp': time.time()
        }
        
        self.pattern_history.append(result)
        
        print(f"✅ 反復分析完了: 重要度 {total_severity:.2f} ({analysis_time:.3f}秒)")
        
        return result
    
    def _detect_exact_repetitions(self, text: str) -> List[RepetitionPattern]:
        """完全一致する語句の反復を検出"""
        patterns = []
        
        # 2文字以上の語句反復を検索
        for length in range(2, min(20, len(text) // 2)):
            for i in range(len(text) - length):
                phrase = text[i:i+length]
                
                # 空白や記号のみの場合はスキップ
                if not re.search(r'[ひらがなカタカナ漢字]', phrase):
                    continue
                
                positions = []
                for j in range(i + length, len(text) - length + 1):
                    if text[j:j+length] == phrase:
                        positions.append(j)
                
                if len(positions) >= self.min_repeat_threshold - 1:
                    severity = min(1.0, (len(positions) * length) / 10.0)
                    patterns.append(RepetitionPattern(
                        pattern=phrase,
                        count=len(positions) + 1,
                        positions=[i] + positions,
                        pattern_type='exact',
                        severity=severity
                    ))
        
        # 重複パターンの除去（より長いパターンを優先）
        patterns.sort(key=lambda p: (p.severity, len(p.pattern)), reverse=True)
        filtered_patterns = []
        used_positions = set()
        
        for pattern in patterns:
            if not any(pos in used_positions for pos in pattern.positions):
                filtered_patterns.append(pattern)
                used_positions.update(pattern.positions)
        
        return filtered_patterns
    
    def _detect_character_repetitions(self, text: str) -> List[RepetitionPattern]:
        """文字レベルの反復を検出"""
        patterns = []
        
        # 同じ文字の連続
        for char in set(text):
            if not re.match(r'[あ-んア-ンー]', char):
                continue
                
            consecutive_pattern = f'{char}{{3,}}'
            matches = list(re.finditer(consecutive_pattern, text))
            
            if matches:
                for match in matches:
                    length = match.end() - match.start()
                    severity = min(1.0, length / 5.0)
                    patterns.append(RepetitionPattern(
                        pattern=match.group(),
                        count=1,
                        positions=[match.start()],
                        pattern_type='character',
                        severity=severity
                    ))
        
        return patterns
    
    def _detect_phonetic_repetitions(self, text: str) -> List[RepetitionPattern]:
        """音韻的に類似した反復を検出"""
        patterns = []
        
        # ひらがな・カタカナの音韻的類似性
        hiragana_text = text.translate(self.katakana_map)
        
        # 語句を音韻グループに分類
        phonetic_groups = defaultdict(list)
        
        for length in range(2, 8):
            for i in range(len(hiragana_text) - length):
                phrase = hiragana_text[i:i+length]
                if re.match(r'^[あ-ん]+$', phrase):
                    # 濁音・半濁音を正規化
                    normalized = self._normalize_phonetic(phrase)
                    phonetic_groups[normalized].append((phrase, i))
        
        # 音韻的に類似したパターンの検出
        for normalized, occurrences in phonetic_groups.items():
            if len(occurrences) >= self.min_repeat_threshold:
                unique_phrases = list(set(occ[0] for occ in occurrences))
                if len(unique_phrases) > 1:  # 異なる表記で同じ音
                    severity = min(1.0, len(occurrences) / 8.0)
                    patterns.append(RepetitionPattern(
                        pattern=f"音韻類似: {'/'.join(unique_phrases[:3])}",
                        count=len(occurrences),
                        positions=[occ[1] for occ in occurrences],
                        pattern_type='phonetic',
                        severity=severity
                    ))
        
        return patterns
    
    def _normalize_phonetic(self, text: str) -> str:
        """音韻正規化（濁音・半濁音・拗音の統一）"""
        # 濁音・半濁音の正規化
        phonetic_map = str.maketrans(
            'がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ',
            'かきくけこさしすせそたちつてとはひふへほはひふへほ'
        )
        
        # 拗音の正規化
        normalized = text.translate(phonetic_map)
        normalized = re.sub(r'[ゃゅょっ]', '', normalized)
        
        return normalized
    
    def _detect_semantic_repetitions(self, text: str) -> List[RepetitionPattern]:
        """意味的に類似した反復を検出"""
        patterns = []
        
        # 同義語・類義語のパターン
        semantic_groups = {
            '感嘆': ['わあ', 'うわあ', 'きゃあ', 'ひゃあ'],
            '確認': ['ですね', 'ですよね', 'でしょう', 'でしょうね'],
            '強調': ['とても', 'すごく', 'めちゃくちゃ', 'かなり'],
            '同意': ['そうです', 'そうですね', 'はい', 'ええ']
        }
        
        for group_name, words in semantic_groups.items():
            found_words = []
            positions = []
            
            for word in words:
                for match in re.finditer(re.escape(word), text):
                    found_words.append(word)
                    positions.append(match.start())
            
            if len(found_words) >= self.min_repeat_threshold:
                unique_words = list(set(found_words))
                if len(unique_words) > 1:
                    severity = min(1.0, len(found_words) / 6.0)
                    patterns.append(RepetitionPattern(
                        pattern=f"意味類似({group_name}): {'/'.join(unique_words[:3])}",
                        count=len(found_words),
                        positions=positions,
                        pattern_type='semantic',
                        severity=severity
                    ))
        
        return patterns
    
    def _detect_interjection_overuse(self, text: str) -> List[RepetitionPattern]:
        """感嘆詞・間投詞の過剰使用を検出"""
        patterns = []
        
        for pattern_str in self.interjection_patterns:
            matches = list(re.finditer(pattern_str, text))
            
            if len(matches) >= 3:  # 3回以上の使用で過剰と判定
                severity = min(1.0, len(matches) / 5.0)
                patterns.append(RepetitionPattern(
                    pattern=f"感嘆詞過多: {pattern_str}",
                    count=len(matches),
                    positions=[m.start() for m in matches],
                    pattern_type='interjection',
                    severity=severity
                ))
        
        return patterns
    
    def suppress_repetitions(self, text: str, character_name: str = None) -> str:
        """
        反復を抑制したテキストを生成
        
        Args:
            text: 処理対象テキスト
            character_name: キャラクター名
            
        Returns:
            反復抑制済みテキスト
        """
        print(f"🔧 反復抑制処理開始: {len(text)}文字")
        
        # 分析実行
        analysis = self.analyze_text(text, character_name)
        
        # アグレッシブモードでは低い重要度でも処理
        severity_threshold = 0.1 if self.enable_aggressive_mode else 0.3
        
        if analysis['total_severity'] < 0.05:
            print("✅ 反復問題なし")
            return text
        
        suppressed_text = text
        original_length = len(text)
        
        # アグレッシブモードでは完全一致を最優先で処理
        if self.enable_aggressive_mode and self.exact_match_priority:
            # 完全一致パターンを最初に処理
            exact_patterns = analysis['patterns'].get('exact_repetitions', [])
            for pattern in sorted(exact_patterns, key=lambda p: p.severity, reverse=True):
                if pattern.severity > severity_threshold:
                    suppressed_text = self._apply_suppression(
                        suppressed_text, pattern, character_name
                    )
        
        # その他のパターンを処理
        for pattern_type, pattern_list in analysis['patterns'].items():
            if self.enable_aggressive_mode and pattern_type == 'exact_repetitions':
                continue  # 既に処理済み
                
            for pattern in sorted(pattern_list, key=lambda p: p.severity, reverse=True):
                if pattern.severity > severity_threshold:
                    suppressed_text = self._apply_suppression(
                        suppressed_text, pattern, character_name
                    )
        
        # アグレッシブモードでの追加処理：隣接する同一語句の除去
        if self.enable_aggressive_mode:
            suppressed_text = self._remove_adjacent_duplicates(suppressed_text)
        
        compression_ratio = (original_length - len(suppressed_text)) / original_length * 100
        print(f"✅ 反復抑制完了: 重要度 {analysis['total_severity']:.2f} → 改善済み (圧縮率: {compression_ratio:.1f}%)")
        
        return suppressed_text
    
    def _apply_suppression(self, text: str, pattern: RepetitionPattern, character_name: str = None) -> str:
        """
        特定パターンの反復抑制を適用
        """
        if pattern.pattern_type == 'exact':
            return self._suppress_exact_repetition(text, pattern)
        elif pattern.pattern_type == 'character':
            return self._suppress_character_repetition(text, pattern)
        elif pattern.pattern_type == 'interjection':
            return self._suppress_interjection_overuse(text, pattern)
        elif pattern.pattern_type == 'word':
            return self._suppress_word_repetition(text, pattern)
        else:
            return text
    
    def _suppress_exact_repetition(self, text: str, pattern: RepetitionPattern) -> str:
        """完全一致反復の抑制"""
        original_phrase = pattern.pattern
        
        # キャッシュから代替表現を取得
        if original_phrase in self.replacement_cache:
            alternatives = self.replacement_cache[original_phrase]
        elif original_phrase in self.replacement_dict:
            alternatives = self.replacement_dict[original_phrase]
        else:
            # 動的代替表現生成
            alternatives = self._generate_alternatives(original_phrase)
            self.replacement_cache[original_phrase] = alternatives
        
        # 反復箇所を代替表現で置換
        result = text
        positions = sorted(pattern.positions, reverse=True)  # 後ろから処理
        
        for i, pos in enumerate(positions[1:], 1):  # 最初の出現は保持
            if i < len(alternatives):
                replacement = alternatives[i - 1]
            else:
                replacement = alternatives[i % len(alternatives)]
            
            # 置換実行
            end_pos = pos + len(original_phrase)
            result = result[:pos] + replacement + result[end_pos:]
        
        return result
    
    def _suppress_character_repetition(self, text: str, pattern: RepetitionPattern) -> str:
        """文字反復の抑制"""
        repeated_char = pattern.pattern[0]
        length = len(pattern.pattern)
        
        # 適切な長さに短縮
        if length > 5:
            replacement = repeated_char * 2
        elif length > 3:
            replacement = repeated_char * 2
        else:
            replacement = pattern.pattern
        
        return text.replace(pattern.pattern, replacement, 1)
    
    def _suppress_interjection_overuse(self, text: str, pattern: RepetitionPattern) -> str:
        """感嘆詞過多の抑制"""
        # 感嘆詞パターンから実際の文字列を抽出して処理
        pattern_matches = re.findall(pattern.pattern.replace('感嘆詞過多: ', ''), text)
        
        if pattern_matches:
            # 最初の2回を残して他を削除または簡略化
            for i, match in enumerate(pattern_matches[2:], 2):
                if i % 2 == 0:  # 偶数番目は削除
                    text = text.replace(match, '', 1)
                else:  # 奇数番目は簡略化
                    simplified = self._simplify_interjection(match)
                    text = text.replace(match, simplified, 1)
        
        return text
    
    def _simplify_interjection(self, interjection: str) -> str:
        """感嘆詞の簡略化"""
        # 基本形に戻す
        if len(interjection) > 3:
            base_char = interjection[0]
            return base_char * 2
        return interjection
    
    def _generate_alternatives(self, phrase: str) -> List[str]:
        """動的代替表現生成"""
        alternatives = []
        
        # 基本的な変形パターン
        if re.match(r'^[あ-ん]+$', phrase):
            # ひらがなの場合
            if len(phrase) <= 2:
                alternatives = [phrase[0], phrase + 'っ', 'ん' + phrase]
            else:
                alternatives = [phrase[:2], phrase[0] + 'っ', phrase[:-1]]
        
        elif re.match(r'^[ア-ン]+$', phrase):
            # カタカナの場合
            alternatives = [phrase[:2], phrase + '！', phrase[:-1]]
        
        else:
            # 漢字・混合の場合
            alternatives = [phrase[:len(phrase)//2], phrase + 'ね', phrase + 'よ']
        
        # 最低限の代替表現を保証
        if not alternatives:
            alternatives = [phrase[:-1] if len(phrase) > 1 else phrase]
        
        return alternatives[:3]  # 最大3つの代替表現
    
    def _remove_adjacent_duplicates(self, text: str) -> str:
        """隣接する同一語句の除去（アグレッシブモード専用）"""
        if not text:
            return text
        
        # 語句境界での分割（日本語対応）
        words = re.split(r'([。、！？：\s]+)', text)
        cleaned_words = []
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # 空文字や記号のみの場合はそのまま追加
            if not word or not re.search(r'[ひらがなカタカナ漢字]', word):
                cleaned_words.append(word)
                i += 1
                continue
            
            # 隣接する同一語句をチェック
            duplicate_count = 1
            while (i + duplicate_count < len(words) and 
                   words[i + duplicate_count] == word):
                duplicate_count += 1
            
            # 重複が見つかった場合
            if duplicate_count > 1:
                # 2つ以上の重複は1つに削減
                cleaned_words.append(word)
                if duplicate_count > 2:  # 3つ以上の場合は削減効果をログ
                    print(f"   📝 隣接重複語句を削減: '{word}' ({duplicate_count} → 1)")
                i += duplicate_count
            else:
                cleaned_words.append(word)
                i += 1
        
        return ''.join(cleaned_words)
    
    def _detect_word_repetitions(self, text: str) -> List[RepetitionPattern]:
        """語レベルでの反復検出（アグレッシブモード用）"""
        patterns = []
        
        # 形態素解析的な語句分割（簡易版）
        words = re.findall(r'[ひらがなカタカナ漢字]+|[A-Za-z]+|\d+', text)
        word_positions = {}
        
        # 語句の位置を記録
        current_pos = 0
        for word in words:
            pos = text.find(word, current_pos)
            if word not in word_positions:
                word_positions[word] = []
            word_positions[word].append(pos)
            current_pos = pos + len(word)
        
        # 反復語句を検出
        for word, positions in word_positions.items():
            if len(positions) >= self.min_repeat_threshold and len(word) >= 2:
                # 近接している反復のみを対象
                close_positions = []
                for i, pos in enumerate(positions):
                    if i == 0:
                        close_positions.append(pos)
                    elif pos - positions[i-1] <= self.max_distance:
                        close_positions.append(pos)
                
                if len(close_positions) >= self.min_repeat_threshold:
                    severity = min(1.0, (len(close_positions) * len(word)) / 20.0)
                    patterns.append(RepetitionPattern(
                        pattern=word,
                        count=len(close_positions),
                        positions=close_positions,
                        pattern_type='word',
                        severity=severity
                    ))
        
        return patterns
    
    def _suppress_word_repetition(self, text: str, pattern: RepetitionPattern) -> str:
        """語レベル反復の抑制"""
        word = pattern.pattern
        positions = sorted(pattern.positions, reverse=True)
        
        # 代替表現を生成
        alternatives = self._generate_alternatives(word)
        
        # 後ろから置換（位置がずれないように）
        result = text
        for i, pos in enumerate(positions[1:], 1):  # 最初の出現は保持
            if i < len(alternatives):
                replacement = alternatives[i - 1]
            else:
                # 代替表現が足りない場合は削除
                replacement = ""
            
            # 置換実行
            end_pos = pos + len(word)
            if replacement:
                result = result[:pos] + replacement + result[end_pos:]
            else:
                # 語句を完全に削除
                result = result[:pos] + result[end_pos:]
                
        return result
    
    def get_statistics(self) -> Dict:
        """反復抑制統計の取得"""
        if not self.pattern_history:
            return {"message": "分析履歴がありません"}
        
        total_analyses = len(self.pattern_history)
        avg_severity = sum(h['total_severity'] for h in self.pattern_history) / total_analyses
        
        # パターンタイプ別統計
        pattern_type_stats = defaultdict(int)
        for analysis in self.pattern_history:
            for pattern_type, patterns in analysis['patterns'].items():
                pattern_type_stats[pattern_type] += len(patterns)
        
        # キャラクター別統計
        char_stats = {}
        for char, patterns in self.character_patterns.items():
            char_stats[char] = {
                'total_patterns': len(patterns),
                'avg_severity': sum(p.severity for p in patterns) / len(patterns) if patterns else 0
            }
        
        return {
            'total_analyses': total_analyses,
            'average_severity': avg_severity,
            'pattern_type_distribution': dict(pattern_type_stats),
            'character_statistics': char_stats,
            'replacement_cache_size': len(self.replacement_cache),
            'recent_severity_trend': [h['total_severity'] for h in self.pattern_history[-10:]]
        }
    
    def save_session_data(self, filepath: str = None):
        """セッションデータの保存"""
        if filepath is None:
            os.makedirs("logs/repetition", exist_ok=True)
            filepath = f"logs/repetition/session_{int(time.time())}.json"
        
        session_data = {
            'timestamp': time.time(),
            'statistics': self.get_statistics(),
            'replacement_cache': self.replacement_cache,
            'character_patterns': {
                char: [
                    {
                        'pattern': p.pattern,
                        'count': p.count,
                        'severity': p.severity,
                        'type': p.pattern_type
                    }
                    for p in patterns
                ]
                for char, patterns in self.character_patterns.items()
            }
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            print(f"📊 反復抑制セッションデータを保存: {filepath}")
        except Exception as e:
            print(f"❌ セッションデータ保存エラー: {e}")


def demo_repetition_suppression():
    """反復抑制システムのデモンストレーション"""
    suppressor = AdvancedRepetitionSuppressor()
    
    test_texts = [
        "あああああ…！ オス様…！ あああああ…！ うわああああああああああああぁっ…！",
        "嬉しいです嬉しいです。とても嬉しいです。嬉しい気持ちです。",
        "そうですねそうですね。でもでもでも、やっぱりやっぱり。",
        "ひゃあああああ！ きゃああああ！ わああああ！ うわああああ！"
    ]
    
    print("🎯 反復抑制システムデモ")
    print("=" * 50)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 テストケース {i}:")
        print(f"原文: {text}")
        
        suppressed = suppressor.suppress_repetitions(text, f"テストキャラ{i}")
        print(f"改善: {suppressed}")
        
        print("-" * 30)
    
    # 統計表示
    stats = suppressor.get_statistics()
    print(f"\n📊 セッション統計:")
    print(f"- 分析回数: {stats['total_analyses']}")
    print(f"- 平均重要度: {stats['average_severity']:.2f}")
    print(f"- パターンタイプ分布: {stats['pattern_type_distribution']}")


if __name__ == "__main__":
    demo_repetition_suppression() 