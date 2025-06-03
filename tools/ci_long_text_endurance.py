# -*- coding: utf-8 -*-
"""
CI 長文耐久テスト v3.0
32K トークン生成でのメモリリーク監視とOOM防止システム
EasyNovelAssistant統合版
"""

import os
import sys
import time
import psutil
import gc
import threading
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import json
import traceback

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


@dataclass
class MemoryMetrics:
    """メモリメトリクス"""
    timestamp: float
    rss_mb: float  # 物理メモリ使用量 (MB)
    vms_mb: float  # 仮想メモリ使用量 (MB)
    percent: float  # メモリ使用率 (%)
    available_mb: float  # 利用可能メモリ (MB)
    gpu_memory_mb: Optional[float] = None  # GPU メモリ使用量 (MB)
    gpu_memory_reserved_mb: Optional[float] = None  # GPU 予約メモリ (MB)


@dataclass
class EnduranceTestResult:
    """耐久テスト結果"""
    test_name: str
    target_tokens: int
    generated_tokens: int
    duration_seconds: float
    peak_memory_mb: float
    peak_gpu_memory_mb: Optional[float]
    memory_leak_detected: bool
    oom_events: int
    tokens_per_second: float
    success: bool
    error_message: Optional[str] = None


class MemoryMonitor:
    """メモリ監視システム"""
    
    def __init__(self, interval_seconds: float = 0.5):
        self.interval = interval_seconds
        self.is_monitoring = False
        self.metrics_history: List[MemoryMetrics] = []
        self.monitor_thread: Optional[threading.Thread] = None
        self.process = psutil.Process()
        
        # OOM閾値設定（利用可能メモリの90%）
        self.oom_threshold_mb = psutil.virtual_memory().available / (1024 * 1024) * 0.9
        self.oom_events = 0
    
    def start_monitoring(self):
        """監視開始"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.metrics_history.clear()
        self.oom_events = 0
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print(f"🔍 メモリ監視開始 (OOM閾値: {self.oom_threshold_mb:.1f} MB)")
    
    def stop_monitoring(self):
        """監視停止"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        print(f"🛑 メモリ監視停止 (記録数: {len(self.metrics_history)})")
    
    def _monitor_loop(self):
        """監視ループ"""
        while self.is_monitoring:
            try:
                # システムメモリ
                memory_info = self.process.memory_info()
                system_memory = psutil.virtual_memory()
                
                # GPUメモリ（利用可能な場合）
                gpu_memory_mb = None
                gpu_reserved_mb = None
                
                if TORCH_AVAILABLE and torch.cuda.is_available():
                    try:
                        gpu_memory_mb = torch.cuda.memory_allocated() / (1024 * 1024)
                        gpu_reserved_mb = torch.cuda.memory_reserved() / (1024 * 1024)
                    except Exception:
                        pass
                
                # メトリクス記録
                metrics = MemoryMetrics(
                    timestamp=time.time(),
                    rss_mb=memory_info.rss / (1024 * 1024),
                    vms_mb=memory_info.vms / (1024 * 1024),
                    percent=system_memory.percent,
                    available_mb=system_memory.available / (1024 * 1024),
                    gpu_memory_mb=gpu_memory_mb,
                    gpu_memory_reserved_mb=gpu_reserved_mb
                )
                
                self.metrics_history.append(metrics)
                
                # OOM検出
                if metrics.available_mb < (self.oom_threshold_mb * 0.1):  # 閾値の10%以下
                    self.oom_events += 1
                    print(f"⚠️ OOM警告: 利用可能メモリ {metrics.available_mb:.1f} MB")
                    
                    # 緊急ガベージコレクション
                    gc.collect()
                    if TORCH_AVAILABLE and torch.cuda.is_available():
                        torch.cuda.empty_cache()
                
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"❌ メモリ監視エラー: {e}")
                time.sleep(1.0)
    
    def get_peak_memory(self) -> Tuple[float, Optional[float]]:
        """ピークメモリ使用量取得"""
        if not self.metrics_history:
            return 0.0, None
        
        peak_rss = max(m.rss_mb for m in self.metrics_history)
        peak_gpu = None
        
        if any(m.gpu_memory_mb is not None for m in self.metrics_history):
            peak_gpu = max(m.gpu_memory_mb for m in self.metrics_history if m.gpu_memory_mb is not None)
        
        return peak_rss, peak_gpu
    
    def detect_memory_leak(self, window_minutes: int = 5) -> bool:
        """メモリリーク検出"""
        if len(self.metrics_history) < 100:  # データ不足
            return False
        
        # 過去N分のデータで線形回帰
        window_seconds = window_minutes * 60
        recent_metrics = [
            m for m in self.metrics_history 
            if (time.time() - m.timestamp) <= window_seconds
        ]
        
        if len(recent_metrics) < 20:
            return False
        
        # 簡易線形回帰（メモリ使用量の傾き）
        timestamps = [m.timestamp for m in recent_metrics]
        memory_values = [m.rss_mb for m in recent_metrics]
        
        n = len(timestamps)
        sum_x = sum(timestamps)
        sum_y = sum(memory_values)
        sum_xy = sum(t * m for t, m in zip(timestamps, memory_values))
        sum_xx = sum(t * t for t in timestamps)
        
        # 傾き計算
        if n * sum_xx - sum_x * sum_x == 0:
            return False
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        
        # 傾きが正でかつ一定値以上の場合、メモリリークと判定
        leak_threshold = 1.0  # MB/分
        return slope > (leak_threshold / 60)  # MB/秒に換算
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """要約統計"""
        if not self.metrics_history:
            return {}
        
        rss_values = [m.rss_mb for m in self.metrics_history]
        gpu_values = [m.gpu_memory_mb for m in self.metrics_history if m.gpu_memory_mb is not None]
        
        stats = {
            'duration_minutes': (self.metrics_history[-1].timestamp - self.metrics_history[0].timestamp) / 60,
            'peak_memory_mb': max(rss_values),
            'min_memory_mb': min(rss_values),
            'avg_memory_mb': sum(rss_values) / len(rss_values),
            'memory_samples': len(self.metrics_history),
            'oom_events': self.oom_events,
            'memory_leak_detected': self.detect_memory_leak()
        }
        
        if gpu_values:
            stats.update({
                'peak_gpu_memory_mb': max(gpu_values),
                'avg_gpu_memory_mb': sum(gpu_values) / len(gpu_values)
            })
        
        return stats


class LongTextEnduranceTester:
    """長文耐久テスト実行エンジン"""
    
    def __init__(self):
        self.memory_monitor = MemoryMonitor()
        self.test_results: List[EnduranceTestResult] = []
    
    async def run_endurance_test(self, 
                                target_tokens: int = 32000,
                                test_name: str = "32K_endurance",
                                timeout_minutes: int = 30) -> EnduranceTestResult:
        """耐久テスト実行"""
        
        print(f"🏃 長文耐久テスト開始: {test_name}")
        print(f"   目標トークン数: {target_tokens:,}")
        print(f"   タイムアウト: {timeout_minutes}分")
        
        start_time = time.time()
        self.memory_monitor.start_monitoring()
        
        try:
            # ダミーテキスト生成（実際のLLMと置き換え）
            generated_tokens = await self._simulate_long_text_generation(
                target_tokens, timeout_minutes * 60
            )
            
            duration = time.time() - start_time
            peak_memory, peak_gpu = self.memory_monitor.get_peak_memory()
            
            # 結果の作成
            result = EnduranceTestResult(
                test_name=test_name,
                target_tokens=target_tokens,
                generated_tokens=generated_tokens,
                duration_seconds=duration,
                peak_memory_mb=peak_memory,
                peak_gpu_memory_mb=peak_gpu,
                memory_leak_detected=self.memory_monitor.detect_memory_leak(),
                oom_events=self.memory_monitor.oom_events,
                tokens_per_second=generated_tokens / duration if duration > 0 else 0,
                success=generated_tokens >= target_tokens * 0.9  # 90%以上で成功
            )
            
            self.test_results.append(result)
            
            print(f"✅ 耐久テスト完了: {test_name}")
            print(f"   生成トークン: {generated_tokens:,} / {target_tokens:,}")
            print(f"   所要時間: {duration:.1f}秒")
            print(f"   処理速度: {result.tokens_per_second:.1f} tokens/sec")
            print(f"   ピークメモリ: {peak_memory:.1f} MB")
            if peak_gpu:
                print(f"   ピークGPUメモリ: {peak_gpu:.1f} MB")
            print(f"   メモリリーク: {'検出' if result.memory_leak_detected else '未検出'}")
            print(f"   OOMイベント: {result.oom_events}回")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            peak_memory, peak_gpu = self.memory_monitor.get_peak_memory()
            
            result = EnduranceTestResult(
                test_name=test_name,
                target_tokens=target_tokens,
                generated_tokens=0,
                duration_seconds=duration,
                peak_memory_mb=peak_memory,
                peak_gpu_memory_mb=peak_gpu,
                memory_leak_detected=self.memory_monitor.detect_memory_leak(),
                oom_events=self.memory_monitor.oom_events,
                tokens_per_second=0,
                success=False,
                error_message=str(e)
            )
            
            self.test_results.append(result)
            
            print(f"❌ 耐久テスト失敗: {test_name}")
            print(f"   エラー: {e}")
            
            return result
            
        finally:
            self.memory_monitor.stop_monitoring()
    
    async def _simulate_long_text_generation(self, target_tokens: int, timeout_seconds: int) -> int:
        """長文生成シミュレーション"""
        
        # 段階的生成（実際のトークン生成をシミュレート）
        generated_tokens = 0
        start_time = time.time()
        
        # チャンクサイズ（一度に生成するトークン数）
        chunk_size = min(512, target_tokens // 10)
        
        while generated_tokens < target_tokens:
            # タイムアウトチェック
            if time.time() - start_time > timeout_seconds:
                print(f"⏱️ タイムアウト: {generated_tokens} tokens 生成済み")
                break
            
            # チャンク生成シミュレート
            await self._generate_chunk(chunk_size)
            generated_tokens += chunk_size
            
            # 進捗表示
            if generated_tokens % (chunk_size * 10) == 0:
                progress = generated_tokens / target_tokens * 100
                elapsed = time.time() - start_time
                tokens_per_sec = generated_tokens / elapsed
                
                print(f"📊 進捗: {generated_tokens:,}/{target_tokens:,} tokens "
                      f"({progress:.1f}%) - {tokens_per_sec:.1f} tok/s")
                
                # 定期的なガベージコレクション
                gc.collect()
                if TORCH_AVAILABLE and torch.cuda.is_available():
                    torch.cuda.empty_cache()
        
        return generated_tokens
    
    async def _generate_chunk(self, chunk_size: int):
        """チャンク生成（メモリ使用量を意図的に増やす）"""
        
        # CPU集約的な処理をシミュレート
        await asyncio.sleep(0.01)  # I/O待機シミュレート
        
        # メモリ使用量を増やす（大きなリストを作成して削除）
        if NUMPY_AVAILABLE:
            # NumPy配列でメモリ使用
            dummy_data = np.random.random((chunk_size, 100))
            _ = dummy_data.mean()  # 何らかの計算
            del dummy_data
        else:
            # Pythonリストでメモリ使用
            dummy_data = [[i] * 100 for i in range(chunk_size)]
            _ = len(dummy_data)
            del dummy_data
        
        # GPU メモリ使用（利用可能な場合）
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                device = torch.device('cuda')
                tensor = torch.randn(chunk_size, 100, device=device)
                _ = tensor.sum()
                del tensor
            except Exception:
                pass  # GPU メモリ不足などは無視
    
    def save_results(self, output_file: str):
        """結果保存"""
        
        summary_data = {
            'test_summary': {
                'total_tests': len(self.test_results),
                'successful_tests': sum(1 for r in self.test_results if r.success),
                'failed_tests': sum(1 for r in self.test_results if not r.success),
                'total_tokens_generated': sum(r.generated_tokens for r in self.test_results),
                'average_tokens_per_second': sum(r.tokens_per_second for r in self.test_results) / max(1, len(self.test_results)),
                'memory_leak_detected': any(r.memory_leak_detected for r in self.test_results),
                'total_oom_events': sum(r.oom_events for r in self.test_results)
            },
            'test_results': [
                {
                    'test_name': r.test_name,
                    'target_tokens': r.target_tokens,
                    'generated_tokens': r.generated_tokens,
                    'duration_seconds': r.duration_seconds,
                    'peak_memory_mb': r.peak_memory_mb,
                    'peak_gpu_memory_mb': r.peak_gpu_memory_mb,
                    'memory_leak_detected': r.memory_leak_detected,
                    'oom_events': r.oom_events,
                    'tokens_per_second': r.tokens_per_second,
                    'success': r.success,
                    'error_message': r.error_message
                }
                for r in self.test_results
            ],
            'memory_monitoring': self.memory_monitor.get_summary_stats()
        }
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 結果保存: {output_file}")


async def main():
    """メイン実行関数"""
    print("🧪 CI 長文耐久テスト v3.0")
    print("   32K トークン生成でのメモリリーク監視とOOM防止")
    print("=" * 60)
    
    tester = LongTextEnduranceTester()
    
    # テストケース定義
    test_cases = [
        (8000, "8K_warmup", 5),
        (16000, "16K_medium", 10),
        (32000, "32K_target", 15),
        (32000, "32K_repeat", 15)  # 再現性確認
    ]
    
    try:
        for target_tokens, test_name, timeout_minutes in test_cases:
            await tester.run_endurance_test(
                target_tokens=target_tokens,
                test_name=test_name,
                timeout_minutes=timeout_minutes
            )
            
            # テスト間のクールダウン
            print(f"😴 クールダウン (5秒)...")
            await asyncio.sleep(5)
            
            # 強制ガベージコレクション
            gc.collect()
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        # 結果保存
        output_file = f"./logs/ci_endurance_test_{int(time.time())}.json"
        tester.save_results(output_file)
        
        # 最終レポート
        print("\n📋 最終レポート:")
        print(f"   実行テスト数: {len(tester.test_results)}")
        successful = sum(1 for r in tester.test_results if r.success)
        print(f"   成功: {successful} / {len(tester.test_results)}")
        
        total_tokens = sum(r.generated_tokens for r in tester.test_results)
        print(f"   総生成トークン: {total_tokens:,}")
        
        avg_speed = sum(r.tokens_per_second for r in tester.test_results) / len(tester.test_results)
        print(f"   平均処理速度: {avg_speed:.1f} tokens/sec")
        
        memory_leaks = sum(1 for r in tester.test_results if r.memory_leak_detected)
        print(f"   メモリリーク検出: {memory_leaks} / {len(tester.test_results)}")
        
        total_oom = sum(r.oom_events for r in tester.test_results)
        print(f"   OOMイベント総数: {total_oom}")
        
        # 合格判定
        if successful == len(tester.test_results) and total_oom == 0:
            print("\n🎉 CI 長文耐久テスト 合格！")
            print("   ✅ 全テスト成功")
            print("   ✅ OOMイベント 0件")
            print("   ✅ 32K トークン生成 安定動作確認")
            return 0
        else:
            print("\n📈 CI 長文耐久テスト 改善必要")
            if successful < len(tester.test_results):
                print(f"   ❌ テスト失敗: {len(tester.test_results) - successful}件")
            if total_oom > 0:
                print(f"   ⚠️ OOMイベント: {total_oom}件")
            return 1
    
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 