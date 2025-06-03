# -*- coding: utf-8 -*-
"""
Continuous Learning System for NKAT Expression Enhancement
継続評価&学習システム - フィードバック収集とLoRA微調整
"""

import json
import os
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import numpy as np
from tqdm import tqdm
import logging

@dataclass
class UserFeedback:
    """ユーザーフィードバック"""
    timestamp: float
    session_id: str
    input_text: str
    generated_text: str
    user_rating: int  # 1-5スケール
    feedback_type: str  # "like", "dislike", "neutral"
    quality_metrics: Dict[str, float]
    nkat_parameters: Dict[str, Any]
    comments: Optional[str] = None
    user_id: Optional[str] = None

@dataclass
class GenerationMetrics:
    """生成メトリクス"""
    timestamp: float
    session_id: str
    diversity_score: float
    contradiction_rate: float
    style_consistency: float
    processing_time: float
    memory_usage: float
    nkat_parameters: Dict[str, Any]
    
class FeedbackCollector:
    """フィードバック収集器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('feedback_db_path', 'data/feedback.db')
        self.auto_collect = config.get('auto_collect_feedback', True)
        self.collection_interval = config.get('collection_interval', 3600)  # 1時間
        
        # データベース初期化
        self._init_database()
        
        # 収集統計
        self.stats = {
            'total_feedbacks': 0,
            'positive_feedbacks': 0,
            'negative_feedbacks': 0,
            'average_rating': 0.0,
            'collection_rate': 0.0
        }
        
        # 一時バッファ
        self.feedback_buffer = deque(maxlen=100)
        self.metrics_buffer = deque(maxlen=500)
        
        # バックグラウンド収集
        if self.auto_collect:
            self.collection_thread = threading.Thread(target=self._auto_collection_loop, daemon=True)
            self.collection_thread.start()
        
        logging.info("フィードバック収集器初期化完了")
    
    def _init_database(self):
        """データベース初期化"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # フィードバックテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedbacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    session_id TEXT,
                    input_text TEXT,
                    generated_text TEXT,
                    user_rating INTEGER,
                    feedback_type TEXT,
                    quality_metrics TEXT,
                    nkat_parameters TEXT,
                    comments TEXT,
                    user_id TEXT
                )
            ''')
            
            # メトリクステーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    session_id TEXT,
                    diversity_score REAL,
                    contradiction_rate REAL,
                    style_consistency REAL,
                    processing_time REAL,
                    memory_usage REAL,
                    nkat_parameters TEXT
                )
            ''')
            
            conn.commit()
    
    def collect_user_feedback(self, feedback: UserFeedback):
        """ユーザーフィードバック収集"""
        # バッファに追加
        self.feedback_buffer.append(feedback)
        
        # データベースに保存
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO feedbacks (
                    timestamp, session_id, input_text, generated_text,
                    user_rating, feedback_type, quality_metrics, nkat_parameters,
                    comments, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feedback.timestamp,
                feedback.session_id,
                feedback.input_text,
                feedback.generated_text,
                feedback.user_rating,
                feedback.feedback_type,
                json.dumps(feedback.quality_metrics),
                json.dumps(feedback.nkat_parameters),
                feedback.comments,
                feedback.user_id
            ))
            conn.commit()
        
        # 統計更新
        self._update_feedback_stats(feedback)
        
        logging.info(f"フィードバック収集: 評価={feedback.user_rating}/5, タイプ={feedback.feedback_type}")
    
    def collect_generation_metrics(self, metrics: GenerationMetrics):
        """生成メトリクス収集"""
        # バッファに追加
        self.metrics_buffer.append(metrics)
        
        # データベースに保存
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO metrics (
                    timestamp, session_id, diversity_score, contradiction_rate,
                    style_consistency, processing_time, memory_usage, nkat_parameters
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp,
                metrics.session_id,
                metrics.diversity_score,
                metrics.contradiction_rate,
                metrics.style_consistency,
                metrics.processing_time,
                metrics.memory_usage,
                json.dumps(metrics.nkat_parameters)
            ))
            conn.commit()
    
    def _update_feedback_stats(self, feedback: UserFeedback):
        """フィードバック統計更新"""
        self.stats['total_feedbacks'] += 1
        
        if feedback.user_rating >= 4:
            self.stats['positive_feedbacks'] += 1
        elif feedback.user_rating <= 2:
            self.stats['negative_feedbacks'] += 1
        
        # 平均評価更新
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT AVG(user_rating) FROM feedbacks')
            result = cursor.fetchone()
            self.stats['average_rating'] = result[0] if result[0] else 0.0
    
    def _auto_collection_loop(self):
        """自動収集ループ"""
        while True:
            try:
                time.sleep(self.collection_interval)
                self._periodic_collection()
            except Exception as e:
                logging.error(f"自動収集エラー: {e}")
    
    def _periodic_collection(self):
        """定期収集処理"""
        # システムメトリクス収集
        system_metrics = self._collect_system_metrics()
        
        # パフォーマンス分析
        performance_analysis = self._analyze_performance()
        
        logging.info(f"定期収集完了: システム={len(system_metrics)}, 解析={len(performance_analysis)}")
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス収集"""
        try:
            import psutil
            
            return {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'timestamp': time.time()
            }
        except ImportError:
            return {'timestamp': time.time(), 'error': 'psutil not available'}
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """パフォーマンス分析"""
        if len(self.metrics_buffer) < 10:
            return {}
        
        recent_metrics = list(self.metrics_buffer)[-20:]
        
        return {
            'avg_diversity': np.mean([m.diversity_score for m in recent_metrics]),
            'avg_contradiction_rate': np.mean([m.contradiction_rate for m in recent_metrics]),
            'avg_processing_time': np.mean([m.processing_time for m in recent_metrics]),
            'trend_diversity': self._calculate_trend([m.diversity_score for m in recent_metrics]),
            'trend_contradiction': self._calculate_trend([m.contradiction_rate for m in recent_metrics])
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """トレンド計算"""
        if len(values) < 2:
            return "unknown"
        
        first_half = np.mean(values[:len(values)//2])
        second_half = np.mean(values[len(values)//2:])
        
        if second_half > first_half * 1.05:
            return "improving"
        elif second_half < first_half * 0.95:
            return "declining"
        else:
            return "stable"
    
    def get_feedback_summary(self, days: int = 7) -> Dict[str, Any]:
        """フィードバック要約取得"""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 期間内のフィードバック
            cursor.execute('''
                SELECT user_rating, feedback_type, quality_metrics, nkat_parameters
                FROM feedbacks WHERE timestamp > ?
            ''', (cutoff_time,))
            
            recent_feedbacks = cursor.fetchall()
        
        if not recent_feedbacks:
            return {"message": f"過去{days}日間のフィードバックがありません"}
        
        # 統計計算
        ratings = [fb[0] for fb in recent_feedbacks]
        avg_rating = np.mean(ratings)
        
        type_counts = defaultdict(int)
        for fb in recent_feedbacks:
            type_counts[fb[1]] += 1
        
        return {
            'period_days': days,
            'total_feedbacks': len(recent_feedbacks),
            'average_rating': avg_rating,
            'rating_distribution': {i: ratings.count(i) for i in range(1, 6)},
            'feedback_types': dict(type_counts),
            'satisfaction_rate': sum(1 for r in ratings if r >= 4) / len(ratings) * 100
        }

class LoRATrainer:
    """LoRA微調整トレーナー"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('lora_training_enabled', True)
        self.training_schedule = config.get('training_schedule', 'weekly')
        self.batch_size = config.get('lora_batch_size', 8)
        self.learning_rate = config.get('lora_learning_rate', 1e-5)
        self.rank = config.get('lora_rank', 16)
        
        # 訓練データパス
        self.training_data_dir = config.get('training_data_dir', 'data/training')
        os.makedirs(self.training_data_dir, exist_ok=True)
        
        # 訓練統計
        self.training_stats = {
            'total_trainings': 0,
            'successful_trainings': 0,
            'last_training_time': 0,
            'average_training_time': 0,
            'performance_improvements': []
        }
        
        logging.info(f"LoRAトレーナー初期化: スケジュール={self.training_schedule}")
    
    def prepare_training_data(self, feedback_collector: FeedbackCollector) -> bool:
        """訓練データ準備"""
        if not self.enabled:
            return False
        
        # 高評価フィードバックを訓練データとして使用
        positive_feedbacks = self._get_positive_feedbacks(feedback_collector)
        
        if len(positive_feedbacks) < 10:
            logging.warning("十分な高評価フィードバックがありません（最小10件必要）")
            return False
        
        # 訓練データファイル生成
        training_file = os.path.join(self.training_data_dir, f"training_{int(time.time())}.jsonl")
        
        with open(training_file, 'w', encoding='utf-8') as f:
            for feedback in positive_feedbacks:
                training_sample = {
                    'prompt': feedback[2],  # input_text
                    'completion': feedback[3],  # generated_text
                    'rating': feedback[4],  # user_rating
                    'quality_metrics': json.loads(feedback[5]),
                    'nkat_parameters': json.loads(feedback[6])
                }
                f.write(json.dumps(training_sample, ensure_ascii=False) + '\n')
        
        logging.info(f"訓練データ準備完了: {len(positive_feedbacks)}件 → {training_file}")
        return True
    
    def _get_positive_feedbacks(self, feedback_collector: FeedbackCollector) -> List[Tuple]:
        """高評価フィードバック取得"""
        cutoff_time = time.time() - (7 * 24 * 3600)  # 過去1週間
        
        with sqlite3.connect(feedback_collector.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM feedbacks 
                WHERE timestamp > ? AND user_rating >= 4
                ORDER BY user_rating DESC, timestamp DESC
                LIMIT 100
            ''', (cutoff_time,))
            
            return cursor.fetchall()
    
    def execute_training(self, feedback_collector: FeedbackCollector) -> bool:
        """LoRA訓練実行"""
        if not self.enabled:
            return False
        
        start_time = time.time()
        
        try:
            # 訓練データ準備
            if not self.prepare_training_data(feedback_collector):
                return False
            
            # 実際の訓練実行（模擬）
            success = self._run_lora_training()
            
            # 統計更新
            training_time = time.time() - start_time
            self._update_training_stats(success, training_time)
            
            if success:
                logging.info(f"LoRA訓練完了: {training_time:.1f}秒")
            else:
                logging.error("LoRA訓練失敗")
            
            return success
            
        except Exception as e:
            logging.error(f"LoRA訓練エラー: {e}")
            return False
    
    def _run_lora_training(self) -> bool:
        """実際のLoRA訓練実行（模擬実装）"""
        # 実際の実装では、ここでLoRAライブラリを使用
        # 例: peft, transformers, torch等
        
        print("🔄 LoRA微調整を開始...")
        
        # 模擬訓練プロセス
        for epoch in tqdm(range(3), desc="Training Epochs"):
            time.sleep(1)  # 実際の訓練時間を模擬
            
            # 模擬損失計算
            mock_loss = 1.0 - (epoch * 0.3)
            print(f"  Epoch {epoch+1}: Loss = {mock_loss:.3f}")
        
        print("✅ LoRA微調整完了")
        return True
    
    def _update_training_stats(self, success: bool, training_time: float):
        """訓練統計更新"""
        self.training_stats['total_trainings'] += 1
        self.training_stats['last_training_time'] = time.time()
        
        if success:
            self.training_stats['successful_trainings'] += 1
        
        # 平均訓練時間更新
        if self.training_stats['total_trainings'] == 1:
            self.training_stats['average_training_time'] = training_time
        else:
            current_avg = self.training_stats['average_training_time']
            new_avg = (current_avg + training_time) / 2
            self.training_stats['average_training_time'] = new_avg
    
    def get_training_report(self) -> Dict[str, Any]:
        """訓練レポート取得"""
        success_rate = 0
        if self.training_stats['total_trainings'] > 0:
            success_rate = self.training_stats['successful_trainings'] / self.training_stats['total_trainings'] * 100
        
        return {
            'enabled': self.enabled,
            'training_schedule': self.training_schedule,
            'statistics': self.training_stats,
            'success_rate': success_rate,
            'last_training': datetime.fromtimestamp(self.training_stats['last_training_time']).isoformat() if self.training_stats['last_training_time'] > 0 else "未実施",
            'configuration': {
                'batch_size': self.batch_size,
                'learning_rate': self.learning_rate,
                'rank': self.rank
            }
        }

class MetricsTracker:
    """メトリクス追跡器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tracking_enabled = config.get('metrics_tracking_enabled', True)
        self.ci_integration = config.get('ci_integration_enabled', False)
        self.alert_thresholds = config.get('alert_thresholds', {
            'diversity_min': 0.30,
            'contradiction_max': 0.10,
            'processing_time_max': 5.0
        })
        
        # メトリクス履歴
        self.metrics_history = deque(maxlen=1000)
        self.alerts = deque(maxlen=50)
        
        # CI統合設定
        self.ci_webhook = config.get('ci_webhook_url')
        self.ci_report_interval = config.get('ci_report_interval', 3600)  # 1時間
        
        logging.info("メトリクス追跡器初期化完了")
    
    def track_metrics(self, metrics: Dict[str, Any]):
        """メトリクス追跡"""
        if not self.tracking_enabled:
            return
        
        timestamp = time.time()
        metrics_entry = {
            'timestamp': timestamp,
            'metrics': metrics.copy()
        }
        
        self.metrics_history.append(metrics_entry)
        
        # アラートチェック
        self._check_alerts(metrics, timestamp)
        
        # CI統合
        if self.ci_integration:
            self._send_ci_metrics(metrics_entry)
    
    def _check_alerts(self, metrics: Dict[str, Any], timestamp: float):
        """アラートチェック"""
        alerts_triggered = []
        
        # 多様性チェック
        if 'diversity_score' in metrics:
            if metrics['diversity_score'] < self.alert_thresholds['diversity_min']:
                alerts_triggered.append({
                    'type': 'diversity_low',
                    'value': metrics['diversity_score'],
                    'threshold': self.alert_thresholds['diversity_min'],
                    'message': f"語彙多様性が低下: {metrics['diversity_score']:.2f} < {self.alert_thresholds['diversity_min']:.2f}"
                })
        
        # 矛盾率チェック
        if 'contradiction_rate' in metrics:
            if metrics['contradiction_rate'] > self.alert_thresholds['contradiction_max']:
                alerts_triggered.append({
                    'type': 'contradiction_high',
                    'value': metrics['contradiction_rate'],
                    'threshold': self.alert_thresholds['contradiction_max'],
                    'message': f"矛盾率が上昇: {metrics['contradiction_rate']:.2f} > {self.alert_thresholds['contradiction_max']:.2f}"
                })
        
        # 処理時間チェック
        if 'processing_time' in metrics:
            if metrics['processing_time'] > self.alert_thresholds['processing_time_max']:
                alerts_triggered.append({
                    'type': 'processing_slow',
                    'value': metrics['processing_time'],
                    'threshold': self.alert_thresholds['processing_time_max'],
                    'message': f"処理時間が長い: {metrics['processing_time']:.2f}s > {self.alert_thresholds['processing_time_max']:.2f}s"
                })
        
        # アラート記録
        for alert in alerts_triggered:
            alert['timestamp'] = timestamp
            self.alerts.append(alert)
            logging.warning(f"🚨 メトリクスアラート: {alert['message']}")
    
    def _send_ci_metrics(self, metrics_entry: Dict[str, Any]):
        """CI統合メトリクス送信"""
        try:
            if self.ci_webhook:
                import requests
                
                payload = {
                    'timestamp': metrics_entry['timestamp'],
                    'metrics': metrics_entry['metrics'],
                    'system': 'EasyNovelAssistant-NKAT'
                }
                
                response = requests.post(self.ci_webhook, json=payload, timeout=10)
                if response.status_code == 200:
                    logging.debug("CI メトリクス送信成功")
                else:
                    logging.warning(f"CI メトリクス送信失敗: {response.status_code}")
        except Exception as e:
            logging.error(f"CI統合エラー: {e}")
    
    def get_metrics_report(self, hours: int = 24) -> Dict[str, Any]:
        """メトリクスレポート取得"""
        cutoff_time = time.time() - (hours * 3600)
        
        recent_metrics = [
            entry for entry in self.metrics_history
            if entry['timestamp'] > cutoff_time
        ]
        
        if not recent_metrics:
            return {"message": f"過去{hours}時間のメトリクスがありません"}
        
        # 統計計算
        diversity_scores = [m['metrics'].get('diversity_score', 0) for m in recent_metrics]
        contradiction_rates = [m['metrics'].get('contradiction_rate', 0) for m in recent_metrics]
        processing_times = [m['metrics'].get('processing_time', 0) for m in recent_metrics]
        
        # アラート統計
        recent_alerts = [
            alert for alert in self.alerts
            if alert['timestamp'] > cutoff_time
        ]
        
        return {
            'period_hours': hours,
            'total_samples': len(recent_metrics),
            'diversity_stats': {
                'average': np.mean(diversity_scores) if diversity_scores else 0,
                'min': min(diversity_scores) if diversity_scores else 0,
                'max': max(diversity_scores) if diversity_scores else 0,
                'trend': self._calculate_trend(diversity_scores)
            },
            'contradiction_stats': {
                'average': np.mean(contradiction_rates) if contradiction_rates else 0,
                'min': min(contradiction_rates) if contradiction_rates else 0,
                'max': max(contradiction_rates) if contradiction_rates else 0,
                'trend': self._calculate_trend(contradiction_rates)
            },
            'performance_stats': {
                'average_processing_time': np.mean(processing_times) if processing_times else 0,
                'min_processing_time': min(processing_times) if processing_times else 0,
                'max_processing_time': max(processing_times) if processing_times else 0
            },
            'alerts': {
                'total': len(recent_alerts),
                'by_type': {alert_type: sum(1 for a in recent_alerts if a['type'] == alert_type) 
                           for alert_type in set(a['type'] for a in recent_alerts)},
                'recent': list(recent_alerts)[-5:]  # 最新5件
            },
            'alert_thresholds': self.alert_thresholds
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """トレンド計算"""
        if len(values) < 2:
            return "unknown"
        
        first_half = np.mean(values[:len(values)//2])
        second_half = np.mean(values[len(values)//2:])
        
        if second_half > first_half * 1.05:
            return "improving"
        elif second_half < first_half * 0.95:
            return "declining"
        else:
            return "stable"

class ContinuousLearningSystem:
    """継続学習システムメインクラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('continuous_learning_enabled', True)
        
        # 各コンポーネント初期化
        self.feedback_collector = FeedbackCollector(config)
        self.lora_trainer = LoRATrainer(config)
        self.metrics_tracker = MetricsTracker(config)
        
        # 週次スケジューラ
        self.weekly_scheduler = threading.Thread(target=self._weekly_schedule, daemon=True)
        if self.enabled:
            self.weekly_scheduler.start()
        
        logging.info("継続学習システム初期化完了")
    
    def record_interaction(self, prompt: str, generated_text: str, 
                          user_feedback: Optional[Dict[str, Any]] = None,
                          metrics: Optional[Dict[str, Any]] = None,
                          session_id: str = "default"):
        """ユーザーインタラクション記録"""
        if not self.enabled:
            return
        
        timestamp = time.time()
        
        # ユーザーフィードバック記録
        if user_feedback:
            feedback = UserFeedback(
                timestamp=timestamp,
                session_id=session_id,
                input_text=prompt,
                generated_text=generated_text,
                user_rating=user_feedback.get('rating', 3),
                feedback_type=user_feedback.get('type', 'neutral'),
                quality_metrics=user_feedback.get('quality_metrics', {}),
                nkat_parameters=user_feedback.get('nkat_parameters', {}),
                comments=user_feedback.get('comments'),
                user_id=user_feedback.get('user_id')
            )
            self.feedback_collector.collect_user_feedback(feedback)
        
        # メトリクス記録
        if metrics:
            generation_metrics = GenerationMetrics(
                timestamp=timestamp,
                session_id=session_id,
                diversity_score=metrics.get('diversity_score', 0.0),
                contradiction_rate=metrics.get('contradiction_rate', 0.0),
                style_consistency=metrics.get('style_consistency', 0.0),
                processing_time=metrics.get('processing_time', 0.0),
                memory_usage=metrics.get('memory_usage', 0.0),
                nkat_parameters=metrics.get('nkat_parameters', {})
            )
            self.feedback_collector.collect_generation_metrics(generation_metrics)
            self.metrics_tracker.track_metrics(metrics)
    
    def _weekly_schedule(self):
        """週次スケジュール実行"""
        while self.enabled:
            try:
                # 1週間待機
                time.sleep(7 * 24 * 3600)
                
                logging.info("🗓️ 週次学習タスク開始")
                
                # LoRA微調整実行
                if self.lora_trainer.execute_training(self.feedback_collector):
                    logging.info("✅ 週次LoRA微調整完了")
                else:
                    logging.warning("⚠️ 週次LoRA微調整スキップ")
                
                # レポート生成
                self._generate_weekly_report()
                
            except Exception as e:
                logging.error(f"週次スケジュールエラー: {e}")
    
    def _generate_weekly_report(self):
        """週次レポート生成"""
        try:
            report = {
                'timestamp': time.time(),
                'week': datetime.now().strftime('%Y-W%U'),
                'feedback_summary': self.feedback_collector.get_feedback_summary(7),
                'training_report': self.lora_trainer.get_training_report(),
                'metrics_report': self.metrics_tracker.get_metrics_report(24 * 7)
            }
            
            # レポート保存
            os.makedirs('reports', exist_ok=True)
            report_file = f"reports/weekly_report_{int(time.time())}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logging.info(f"📊 週次レポート生成: {report_file}")
            
        except Exception as e:
            logging.error(f"週次レポート生成エラー: {e}")
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """総合レポート取得"""
        return {
            'system_status': {
                'enabled': self.enabled,
                'components': {
                    'feedback_collector': True,
                    'lora_trainer': self.lora_trainer.enabled,
                    'metrics_tracker': self.metrics_tracker.tracking_enabled
                }
            },
            'feedback_summary': self.feedback_collector.get_feedback_summary(7),
            'training_status': self.lora_trainer.get_training_report(),
            'metrics_overview': self.metrics_tracker.get_metrics_report(24),
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """改善提案生成"""
        recommendations = []
        
        # フィードバック分析に基づく提案
        feedback_summary = self.feedback_collector.get_feedback_summary(7)
        if feedback_summary.get('satisfaction_rate', 0) < 70:
            recommendations.append("ユーザー満足度向上: パラメータ調整を検討")
        
        # メトリクス分析に基づく提案
        metrics_report = self.metrics_tracker.get_metrics_report(24)
        if metrics_report.get('diversity_stats', {}).get('average', 0) < 0.30:
            recommendations.append("語彙多様性向上: γ値を下げる検討")
        
        if metrics_report.get('contradiction_stats', {}).get('average', 0) > 0.10:
            recommendations.append("矛盾率削減: 品質ガード強化を検討")
        
        if not recommendations:
            recommendations.append("システムは良好に動作しています")
        
        return recommendations

# 使用例とテスト
def test_continuous_learning():
    """継続学習システムのテスト"""
    config = {
        'continuous_learning_enabled': True,
        'feedback_db_path': 'test_feedback.db',
        'lora_training_enabled': True,
        'metrics_tracking_enabled': True
    }
    
    system = ContinuousLearningSystem(config)
    
    # テストインタラクション記録
    print("🧪 継続学習システムテスト開始")
    
    for i in range(5):
        system.record_interaction(
            prompt=f"テストプロンプト{i+1}",
            generated_text=f"生成されたテキスト{i+1}",
            user_feedback={
                'rating': 4 if i % 2 == 0 else 3,
                'type': 'like' if i % 2 == 0 else 'neutral',
                'quality_metrics': {'diversity': 0.3 + i*0.1},
                'nkat_parameters': {'theta_rank': 6, 'theta_gamma': 0.98}
            },
            metrics={
                'diversity_score': 0.3 + i*0.05,
                'contradiction_rate': 0.1 - i*0.02,
                'processing_time': 2.5 + i*0.5
            }
        )
    
    # レポート生成
    report = system.get_comprehensive_report()
    print("📊 総合レポート:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_continuous_learning() 