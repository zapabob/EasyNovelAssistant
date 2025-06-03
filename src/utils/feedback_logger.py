# -*- coding: utf-8 -*-
"""
反復抑制フィードバック・ログシステム
ユーザー体験改善とLoRA微調整データ収集
"""

import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

@dataclass
class RepetitionFeedback:
    """反復抑制フィードバックデータ"""
    timestamp: str
    input_text: str
    output_text: str
    user_rating: int  # 1-5スケール（1=過剰, 3=適切, 5=不足）
    feedback_type: str  # "over_suppression", "under_suppression", "appropriate"
    success_rate: float
    compression_rate: float
    v3_features_used: Dict[str, int]
    character_context: Optional[str] = None
    user_comments: Optional[str] = None
    session_id: Optional[str] = None


class RepetitionFeedbackLogger:
    """反復抑制フィードバック記録システム"""
    
    def __init__(self, log_dir: str = "logs/feedback"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ログファイル設定
        self.feedback_file = self.log_dir / "user_feedback.jsonl"
        self.misfire_samples_file = self.log_dir / "misfire_samples.json"
        self.daily_stats_file = self.log_dir / f"daily_stats_{datetime.now().strftime('%Y%m%d')}.json"
        
        # ロガー設定
        self.setup_logger()
        
        # セッション統計
        self.session_stats = {
            'total_generations': 0,
            'success_count': 0,
            'over_suppressions': 0,
            'under_suppressions': 0,
            'user_feedbacks': 0,
            'session_start': datetime.now().isoformat()
        }
        
        print(f"📊 フィードバックログシステム初期化完了")
        print(f"   ├─ ログディレクトリ: {self.log_dir}")
        print(f"   ├─ フィードバックファイル: {self.feedback_file.name}")
        print(f"   └─ 誤動作サンプル: {self.misfire_samples_file.name}")
    
    def setup_logger(self):
        """ロガーの設定"""
        self.logger = logging.getLogger('RepetitionSuppressor')
        self.logger.setLevel(logging.INFO)
        
        # ファイルハンドラー
        handler = logging.FileHandler(
            self.log_dir / "repetition_suppressor.log",
            encoding='utf-8'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_generation_result(self, 
                            input_text: str, 
                            output_text: str, 
                            metrics: Any,
                            character_name: str = None) -> Dict:
        """生成結果のログ記録"""
        
        success_rate = getattr(metrics, 'success_rate', 0.0)
        compression_rate = (len(input_text) - len(output_text)) / len(input_text) if len(input_text) > 0 else 0.0
        
        # セッション統計更新
        self.session_stats['total_generations'] += 1
        if success_rate >= 0.7:
            self.session_stats['success_count'] += 1
        
        # v3機能使用状況
        v3_features = {
            'ngram_blocks': getattr(metrics, 'ngram_blocks_applied', 0),
            'mecab_normalizations': getattr(metrics, 'mecab_normalizations', 0),
            'rhetorical_exceptions': getattr(metrics, 'rhetorical_exceptions', 0),
            'latin_blocks': getattr(metrics, 'latin_number_blocks', 0)
        }
        
        ngram_hits = v3_features['ngram_blocks']
        
        # ログ出力
        self.logger.info(
            f"RepSuppress: success={self.session_stats['success_count']}/{self.session_stats['total_generations']} "
            f"compress={compression_rate*100:.1f}% ngram={ngram_hits}blk"
        )
        
        # 成功率が70%未満の場合は警告
        if success_rate < 0.7:
            self.logger.warning(
                f"Low success rate detected: {success_rate:.1%} "
                f"(input_len={len(input_text)}, output_len={len(output_text)}, "
                f"patterns_detected={getattr(metrics, 'patterns_detected', 0)})"
            )
            
            # 誤動作サンプルとして記録
            self.record_misfire_sample(input_text, output_text, metrics, character_name)
        
        return {
            'success_rate': success_rate,
            'compression_rate': compression_rate,
            'v3_features_used': v3_features,
            'warning_issued': success_rate < 0.7
        }
    
    def record_user_feedback(self,
                           input_text: str,
                           output_text: str,
                           user_rating: int,
                           feedback_type: str,
                           metrics: Any,
                           character_name: str = None,
                           comments: str = None) -> str:
        """ユーザーフィードバックの記録"""
        
        session_id = f"session_{int(time.time())}"
        
        feedback = RepetitionFeedback(
            timestamp=datetime.now().isoformat(),
            input_text=input_text,
            output_text=output_text,
            user_rating=user_rating,
            feedback_type=feedback_type,
            success_rate=getattr(metrics, 'success_rate', 0.0),
            compression_rate=(len(input_text) - len(output_text)) / len(input_text) if len(input_text) > 0 else 0.0,
            v3_features_used={
                'ngram_blocks': getattr(metrics, 'ngram_blocks_applied', 0),
                'mecab_normalizations': getattr(metrics, 'mecab_normalizations', 0),
                'rhetorical_exceptions': getattr(metrics, 'rhetorical_exceptions', 0),
                'latin_blocks': getattr(metrics, 'latin_number_blocks', 0)
            },
            character_context=character_name,
            user_comments=comments,
            session_id=session_id
        )
        
        # JSONLファイルに追記
        with open(self.feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(feedback), ensure_ascii=False) + '\n')
        
        # セッション統計更新
        self.session_stats['user_feedbacks'] += 1
        if feedback_type == "over_suppression":
            self.session_stats['over_suppressions'] += 1
        elif feedback_type == "under_suppression":
            self.session_stats['under_suppressions'] += 1
        
        self.logger.info(f"User feedback recorded: {feedback_type} (rating: {user_rating}/5)")
        
        return session_id
    
    def record_misfire_sample(self,
                            input_text: str,
                            output_text: str,
                            metrics: Any,
                            character_name: str = None):
        """誤動作サンプルの記録（LoRA微調整用）"""
        
        misfire_sample = {
            'timestamp': datetime.now().isoformat(),
            'input_text': input_text,
            'output_text': output_text,
            'success_rate': getattr(metrics, 'success_rate', 0.0),
            'patterns_detected': getattr(metrics, 'patterns_detected', 0),
            'patterns_suppressed': getattr(metrics, 'patterns_suppressed', 0),
            'compression_rate': (len(input_text) - len(output_text)) / len(input_text) if len(input_text) > 0 else 0.0,
            'character_context': character_name,
            'issue_type': 'low_success_rate',
            'v3_features_used': {
                'ngram_blocks': getattr(metrics, 'ngram_blocks_applied', 0),
                'mecab_normalizations': getattr(metrics, 'mecab_normalizations', 0),
                'rhetorical_exceptions': getattr(metrics, 'rhetorical_exceptions', 0),
                'latin_blocks': getattr(metrics, 'latin_number_blocks', 0)
            }
        }
        
        # 既存のmisfireサンプルを読み込み
        misfire_samples = []
        if self.misfire_samples_file.exists():
            try:
                with open(self.misfire_samples_file, 'r', encoding='utf-8') as f:
                    misfire_samples = json.load(f)
            except:
                misfire_samples = []
        
        # 新しいサンプルを追加
        misfire_samples.append(misfire_sample)
        
        # ファイルに保存（最新100件のみ保持）
        with open(self.misfire_samples_file, 'w', encoding='utf-8') as f:
            json.dump(misfire_samples[-100:], f, ensure_ascii=False, indent=2)
    
    def get_session_stats(self) -> Dict:
        """セッション統計の取得"""
        stats = dict(self.session_stats)
        
        # 追加計算
        if stats['total_generations'] > 0:
            stats['session_success_rate'] = stats['success_count'] / stats['total_generations']
            stats['over_suppression_rate'] = stats['over_suppressions'] / stats['total_generations']
            stats['under_suppression_rate'] = stats['under_suppressions'] / stats['total_generations']
        else:
            stats['session_success_rate'] = 0.0
            stats['over_suppression_rate'] = 0.0
            stats['under_suppression_rate'] = 0.0
        
        return stats
    
    def should_show_warning_banner(self) -> Tuple[bool, str]:
        """警告バナー表示判定"""
        if self.session_stats['total_generations'] < 5:
            return False, ""
        
        success_rate = self.session_stats['success_count'] / self.session_stats['total_generations']
        
        if success_rate < 0.7:
            return True, f"⚠️ 反復抑制の成功率が低下しています ({success_rate:.1%})"
        
        over_rate = self.session_stats['over_suppressions'] / self.session_stats['total_generations']
        if over_rate > 0.3:
            return True, f"⚠️ 過剰抑制が多く発生しています ({over_rate:.1%})"
        
        return False, ""
    
    def generate_daily_report(self) -> Dict:
        """日次レポートの生成"""
        stats = self.get_session_stats()
        
        # フィードバックデータの分析
        feedback_analysis = self.analyze_feedback_data()
        
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'session_stats': stats,
            'feedback_analysis': feedback_analysis,
            'recommendations': self.generate_recommendations(stats, feedback_analysis)
        }
        
        # ファイルに保存
        with open(self.daily_stats_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report
    
    def analyze_feedback_data(self) -> Dict:
        """フィードバックデータの分析"""
        if not self.feedback_file.exists():
            return {'total_feedbacks': 0}
        
        feedbacks = []
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                for line in f:
                    feedbacks.append(json.loads(line.strip()))
        except:
            return {'total_feedbacks': 0, 'error': 'Failed to read feedback file'}
        
        if not feedbacks:
            return {'total_feedbacks': 0}
        
        # 今日のフィードバックのみ抽出
        today = datetime.now().strftime('%Y-%m-%d')
        today_feedbacks = [f for f in feedbacks if f['timestamp'].startswith(today)]
        
        if not today_feedbacks:
            return {'total_feedbacks': len(feedbacks), 'today_feedbacks': 0}
        
        # 分析
        ratings = [f['user_rating'] for f in today_feedbacks]
        feedback_types = [f['feedback_type'] for f in today_feedbacks]
        
        analysis = {
            'total_feedbacks': len(feedbacks),
            'today_feedbacks': len(today_feedbacks),
            'average_rating': sum(ratings) / len(ratings),
            'rating_distribution': {i: ratings.count(i) for i in range(1, 6)},
            'feedback_type_distribution': {
                'over_suppression': feedback_types.count('over_suppression'),
                'under_suppression': feedback_types.count('under_suppression'),
                'appropriate': feedback_types.count('appropriate')
            }
        }
        
        return analysis
    
    def generate_recommendations(self, stats: Dict, feedback_analysis: Dict) -> List[str]:
        """改善推奨事項の生成"""
        recommendations = []
        
        # 成功率ベース
        if stats.get('session_success_rate', 0) < 0.7:
            recommendations.append("similarity_threshold を 0.35 → 0.30 に下げることを検討してください")
        
        # フィードバックベース
        if feedback_analysis.get('today_feedbacks', 0) > 0:
            over_rate = feedback_analysis['feedback_type_distribution'].get('over_suppression', 0)
            under_rate = feedback_analysis['feedback_type_distribution'].get('under_suppression', 0)
            
            if over_rate > under_rate:
                recommendations.append("enable_rhetorical_protection=True で修辞的保護を有効化してください")
            elif under_rate > over_rate:
                recommendations.append("ngram_block_size を 3 → 2 に下げてより積極的に抑制してください")
        
        # 平均評価ベース
        avg_rating = feedback_analysis.get('average_rating', 3.0)
        if avg_rating < 2.5:
            recommendations.append("全体的に過剰抑制の傾向があります。設定を緩めることをお勧めします")
        elif avg_rating > 3.5:
            recommendations.append("抑制が不足している可能性があります。設定を強化することをお勧めします")
        
        if not recommendations:
            recommendations.append("現在の設定は適切に動作しています 👍")
        
        return recommendations
    
    def export_lora_training_data(self, output_file: str = None) -> str:
        """LoRA微調整用データのエクスポート"""
        if output_file is None:
            output_file = self.log_dir / f"lora_training_data_{datetime.now().strftime('%Y%m%d')}.json"
        
        training_data = []
        
        # misfireサンプルから学習データを生成
        if self.misfire_samples_file.exists():
            with open(self.misfire_samples_file, 'r', encoding='utf-8') as f:
                misfire_samples = json.load(f)
            
            for sample in misfire_samples:
                training_example = {
                    'input': sample['input_text'],
                    'output_good': sample['input_text'],  # 理想的には手動で修正された版
                    'output_bad': sample['output_text'],
                    'issue_type': sample['issue_type'],
                    'context': sample.get('character_context', '')
                }
                training_data.append(training_example)
        
        # フィードバックからも学習データを追加
        if self.feedback_file.exists():
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                for line in f:
                    feedback = json.loads(line.strip())
                    if feedback['user_rating'] in [1, 2, 4, 5]:  # 極端な評価のみ
                        training_example = {
                            'input': feedback['input_text'],
                            'output_actual': feedback['output_text'],
                            'user_rating': feedback['user_rating'],
                            'feedback_type': feedback['feedback_type'],
                            'comments': feedback.get('user_comments', ''),
                            'context': feedback.get('character_context', '')
                        }
                        training_data.append(training_example)
        
        # エクスポート
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)
        
        print(f"📦 LoRA学習データエクスポート完了: {output_file} ({len(training_data)}件)")
        return str(output_file)


# グローバルインスタンス
feedback_logger = RepetitionFeedbackLogger()


def log_repetition_result(input_text: str, output_text: str, metrics: Any, character_name: str = None) -> Dict:
    """反復抑制結果のログ記録（便利関数）"""
    return feedback_logger.log_generation_result(input_text, output_text, metrics, character_name)


def record_user_feedback(input_text: str, output_text: str, rating: int, feedback_type: str, 
                        metrics: Any, character_name: str = None, comments: str = None) -> str:
    """ユーザーフィードバックの記録（便利関数）"""
    return feedback_logger.record_user_feedback(
        input_text, output_text, rating, feedback_type, metrics, character_name, comments
    ) 