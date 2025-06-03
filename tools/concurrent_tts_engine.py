# -*- coding: utf-8 -*-
"""
並行TTS（テキスト音声同時生成）エンジン v3.0
EasyNovelAssistant統合版 - テキスト生成と音声合成の完全同時実行
"""

import asyncio
import time
import threading
import queue
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Style-BERT-VITS2の統合
    style_bert_path = os.path.join(current_dir, "Style-Bert-VITS2")
    if os.path.exists(style_bert_path):
        sys.path.insert(0, style_bert_path)
        from style_bert_vits2.tts_model import TTSModel
        from style_bert_vits2.constants import Languages
        TTS_AVAILABLE = True
    else:
        TTS_AVAILABLE = False
        print("⚠️ Style-BERT-VITS2 パス見つからず")
except ImportError as e:
    TTS_AVAILABLE = False
    print(f"⚠️ Style-BERT-VITS2 インポート失敗: {e}")


class ProcessingStatus(Enum):
    """処理ステータス"""
    PENDING = "pending"
    TEXT_GENERATING = "text_generating"
    VOICE_GENERATING = "voice_generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GenerationRequest:
    """生成リクエスト"""
    request_id: str
    prompt: str
    settings: Dict[str, Any]
    text_callback: Optional[Callable[[str], None]] = None
    voice_callback: Optional[Callable[[str], None]] = None  # wav_path
    completion_callback: Optional[Callable[["GenerationResult"], None]] = None


@dataclass
class GenerationResult:
    """生成結果"""
    request_id: str
    generated_text: str
    voice_path: Optional[str]
    text_generation_time: float
    voice_generation_time: float
    total_time: float
    status: ProcessingStatus
    error_message: Optional[str] = None


class ConcurrentTTSEngine:
    """並行TTS（テキスト音声同時生成）エンジン"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.is_running = False
        
        # 処理キューと統計
        self.request_queue = asyncio.Queue()
        self.active_requests: Dict[str, GenerationRequest] = {}
        self.completed_requests: List[GenerationResult] = []
        
        # 統計情報
        self.stats = {
            'total_requests': 0,
            'completed_requests': 0,
            'failed_requests': 0,
            'average_text_time': 0.0,
            'average_voice_time': 0.0,
            'average_total_time': 0.0,
            'concurrent_efficiency': 0.0  # 同時実行効率
        }
        
        # TTS初期化
        self.tts_model = None
        if TTS_AVAILABLE:
            self._initialize_tts()
        
        # ワーカータスク
        self.text_worker_task = None
        self.voice_worker_task = None
        self.coordinator_task = None
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            'max_concurrent_requests': 3,
            'text_generation_timeout': 30.0,
            'voice_generation_timeout': 20.0,
            'enable_voice_generation': True,
            'voice_model_path': None,
            'voice_speaker_id': 0,
            'voice_style': 'Neutral',
            'output_dir': './output/concurrent_tts',
            'enable_metrics': True,
            'enable_streaming': False  # ストリーミング生成
        }
    
    def _initialize_tts(self):
        """TTS初期化"""
        try:
            if self.config.get('voice_model_path') and os.path.exists(self.config['voice_model_path']):
                self.tts_model = TTSModel(
                    model_path=self.config['voice_model_path'],
                    config_path=self.config['voice_model_path'].replace('.safetensors', '.json'),
                    device='cuda' if torch.cuda.is_available() else 'cpu'
                )
                print("✅ Style-BERT-VITS2 TTS初期化成功")
            else:
                print("⚠️ TTSモデルパス未設定 - 音声生成は利用不可")
        except Exception as e:
            print(f"❌ TTS初期化失敗: {e}")
            self.tts_model = None
    
    async def start(self):
        """エンジン開始"""
        if self.is_running:
            print("⚠️ エンジンは既に実行中です")
            return
        
        self.is_running = True
        os.makedirs(self.config['output_dir'], exist_ok=True)
        
        print("🚀 並行TTSエンジン開始")
        print(f"   最大同時リクエスト: {self.config['max_concurrent_requests']}")
        print(f"   音声生成: {'有効' if self.config['enable_voice_generation'] and self.tts_model else '無効'}")
        
        # ワーカータスク開始
        self.text_worker_task = asyncio.create_task(self._text_generation_worker())
        if self.config['enable_voice_generation'] and self.tts_model:
            self.voice_worker_task = asyncio.create_task(self._voice_generation_worker())
        self.coordinator_task = asyncio.create_task(self._request_coordinator())
    
    async def stop(self):
        """エンジン停止"""
        if not self.is_running:
            return
        
        self.is_running = False
        print("🛑 並行TTSエンジン停止中...")
        
        # ワーカータスクの停止
        if self.text_worker_task:
            self.text_worker_task.cancel()
        if self.voice_worker_task:
            self.voice_worker_task.cancel()
        if self.coordinator_task:
            self.coordinator_task.cancel()
        
        print("✅ 並行TTSエンジン停止完了")
    
    async def generate_async(self, 
                           prompt: str, 
                           settings: Optional[Dict[str, Any]] = None,
                           text_callback: Optional[Callable[[str], None]] = None,
                           voice_callback: Optional[Callable[[str], None]] = None,
                           completion_callback: Optional[Callable[[GenerationResult], None]] = None) -> str:
        """非同期生成（リクエストIDを返す）"""
        
        request_id = f"req_{int(time.time() * 1000)}_{len(self.active_requests)}"
        request = GenerationRequest(
            request_id=request_id,
            prompt=prompt,
            settings=settings or {},
            text_callback=text_callback,
            voice_callback=voice_callback,
            completion_callback=completion_callback
        )
        
        await self.request_queue.put(request)
        self.active_requests[request_id] = request
        self.stats['total_requests'] += 1
        
        print(f"📥 生成リクエスト受信: {request_id}")
        print(f"   プロンプト長: {len(prompt)} 文字")
        
        return request_id
    
    async def _request_coordinator(self):
        """リクエスト調整（キューの管理）"""
        while self.is_running:
            try:
                # アクティブリクエスト数の制限
                if len(self.active_requests) >= self.config['max_concurrent_requests']:
                    await asyncio.sleep(0.1)
                    continue
                
                # 新しいリクエストを処理開始
                try:
                    request = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)
                    print(f"🎯 リクエスト処理開始: {request.request_id}")
                    
                    # テキスト生成と音声生成を並行実行
                    await self._process_request_concurrent(request)
                    
                except asyncio.TimeoutError:
                    continue
                
            except Exception as e:
                print(f"❌ リクエスト調整エラー: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_request_concurrent(self, request: GenerationRequest):
        """リクエストの並行処理"""
        start_time = time.time()
        
        try:
            # テキスト生成と音声生成を同時開始
            text_task = asyncio.create_task(self._generate_text(request))
            
            if self.config['enable_voice_generation'] and self.tts_model:
                voice_task = asyncio.create_task(self._generate_voice_when_ready(request, text_task))
                # 両方の完了を待機
                text_result, voice_result = await asyncio.gather(text_task, voice_task, return_exceptions=True)
            else:
                # テキストのみ
                text_result = await text_task
                voice_result = (None, 0.0)
            
            # 結果の処理
            if isinstance(text_result, Exception):
                raise text_result
            if isinstance(voice_result, Exception):
                print(f"⚠️ 音声生成エラー（テキストは成功）: {voice_result}")
                voice_result = (None, 0.0)
            
            generated_text, text_time = text_result
            voice_path, voice_time = voice_result
            
            total_time = time.time() - start_time
            
            # 同時実行効率の計算
            sequential_time = text_time + voice_time
            concurrent_efficiency = (sequential_time / total_time) if total_time > 0 else 1.0
            
            # 結果の作成
            result = GenerationResult(
                request_id=request.request_id,
                generated_text=generated_text,
                voice_path=voice_path,
                text_generation_time=text_time,
                voice_generation_time=voice_time,
                total_time=total_time,
                status=ProcessingStatus.COMPLETED
            )
            
            # コールバック実行
            if request.completion_callback:
                request.completion_callback(result)
            
            # 統計更新
            self._update_statistics(result, concurrent_efficiency)
            
            print(f"✅ リクエスト完了: {request.request_id}")
            print(f"   テキスト: {text_time:.2f}秒, 音声: {voice_time:.2f}秒, 総時間: {total_time:.2f}秒")
            print(f"   同時実行効率: {concurrent_efficiency:.1%}")
            
        except Exception as e:
            # エラー結果
            result = GenerationResult(
                request_id=request.request_id,
                generated_text="",
                voice_path=None,
                text_generation_time=0.0,
                voice_generation_time=0.0,
                total_time=time.time() - start_time,
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
            
            if request.completion_callback:
                request.completion_callback(result)
            
            self.stats['failed_requests'] += 1
            print(f"❌ リクエスト失敗: {request.request_id} - {e}")
        
        finally:
            # クリーンアップ
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]
            self.completed_requests.append(result)
    
    async def _generate_text(self, request: GenerationRequest) -> Tuple[str, float]:
        """テキスト生成（ダミー実装 - 実際のLLMエンジンと置き換え）"""
        start_time = time.time()
        
        try:
            # ダミーテキスト生成（実際はKoboldCpp、統合システムv3等を使用）
            prompt = request.prompt
            settings = request.settings
            
            # 模擬生成時間（実際のLLM処理時間）
            generation_time = min(5.0, len(prompt) * 0.01)  # 文字数に比例
            await asyncio.sleep(generation_time)
            
            # ダミーテキスト生成
            generated_text = f"これは『{prompt}』に対する生成された小説の内容です。キャラクターが感情豊かに会話を繰り広げ、物語が展開していきます。"
            
            # コールバック実行
            if request.text_callback:
                request.text_callback(generated_text)
            
            generation_time = time.time() - start_time
            print(f"📝 テキスト生成完了: {request.request_id} ({generation_time:.2f}秒)")
            
            return generated_text, generation_time
            
        except Exception as e:
            print(f"❌ テキスト生成エラー: {request.request_id} - {e}")
            raise
    
    async def _generate_voice_when_ready(self, request: GenerationRequest, text_task: asyncio.Task) -> Tuple[Optional[str], float]:
        """テキスト完了時に音声生成開始"""
        try:
            # テキスト生成の完了を待機
            generated_text, _ = await text_task
            
            # 音声生成実行
            return await self._generate_voice(request, generated_text)
            
        except Exception as e:
            print(f"❌ 音声生成待機エラー: {request.request_id} - {e}")
            return None, 0.0
    
    async def _generate_voice(self, request: GenerationRequest, text: str) -> Tuple[Optional[str], float]:
        """音声生成"""
        if not self.tts_model:
            return None, 0.0
        
        start_time = time.time()
        
        try:
            # 音声ファイル名生成
            timestamp = int(time.time() * 1000)
            output_filename = f"{request.request_id}_{timestamp}.wav"
            output_path = os.path.join(self.config['output_dir'], output_filename)
            
            # Style-BERT-VITS2での音声生成（非同期）
            def _sync_voice_generation():
                try:
                    sample_rate, audio_data = self.tts_model.infer(
                        text=text[:200],  # 長すぎる場合は切り詰め
                        language=Languages.JP,
                        speaker_id=self.config.get('voice_speaker_id', 0),
                        style=self.config.get('voice_style', 'Neutral'),
                        style_weight=1.0
                    )
                    
                    # WAVファイル保存
                    import soundfile as sf
                    sf.write(output_path, audio_data, sample_rate)
                    
                    return output_path
                except Exception as e:
                    print(f"❌ 音声合成エラー: {e}")
                    return None
            
            # 同期処理を非同期で実行
            loop = asyncio.get_event_loop()
            voice_path = await loop.run_in_executor(None, _sync_voice_generation)
            
            generation_time = time.time() - start_time
            
            if voice_path:
                # コールバック実行
                if request.voice_callback:
                    request.voice_callback(voice_path)
                
                print(f"🎵 音声生成完了: {request.request_id} ({generation_time:.2f}秒)")
                return voice_path, generation_time
            else:
                print(f"❌ 音声生成失敗: {request.request_id}")
                return None, generation_time
                
        except Exception as e:
            print(f"❌ 音声生成エラー: {request.request_id} - {e}")
            return None, time.time() - start_time
    
    async def _text_generation_worker(self):
        """テキスト生成ワーカー（予約）"""
        while self.is_running:
            await asyncio.sleep(0.1)
    
    async def _voice_generation_worker(self):
        """音声生成ワーカー（予約）"""
        while self.is_running:
            await asyncio.sleep(0.1)
    
    def _update_statistics(self, result: GenerationResult, concurrent_efficiency: float):
        """統計更新"""
        self.stats['completed_requests'] += 1
        
        # 平均時間の更新
        n = self.stats['completed_requests']
        self.stats['average_text_time'] = (
            self.stats['average_text_time'] * (n - 1) + result.text_generation_time
        ) / n
        self.stats['average_voice_time'] = (
            self.stats['average_voice_time'] * (n - 1) + result.voice_generation_time
        ) / n
        self.stats['average_total_time'] = (
            self.stats['average_total_time'] * (n - 1) + result.total_time
        ) / n
        self.stats['concurrent_efficiency'] = (
            self.stats['concurrent_efficiency'] * (n - 1) + concurrent_efficiency
        ) / n
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            **self.stats,
            'active_requests': len(self.active_requests),
            'queue_size': self.request_queue.qsize(),
            'success_rate': (
                self.stats['completed_requests'] / max(1, self.stats['total_requests'])
            ) * 100,
            'average_concurrent_speedup': self.stats['concurrent_efficiency'] * 100
        }
    
    def get_request_status(self, request_id: str) -> Optional[ProcessingStatus]:
        """リクエスト状態取得"""
        if request_id in self.active_requests:
            return ProcessingStatus.TEXT_GENERATING  # 簡略化
        
        for result in self.completed_requests:
            if result.request_id == request_id:
                return result.status
        
        return None


# デモ・テスト関数
async def demo_concurrent_tts():
    """並行TTSエンジンのデモ"""
    print("🧪 並行TTS（テキスト音声同時生成）エンジン デモ")
    print("=" * 60)
    
    # エンジン設定
    config = {
        'max_concurrent_requests': 2,
        'enable_voice_generation': TTS_AVAILABLE,
        'output_dir': './output/concurrent_tts_demo',
        'enable_metrics': True
    }
    
    engine = ConcurrentTTSEngine(config)
    
    # コールバック関数
    def on_text_generated(text: str):
        print(f"📝 テキスト受信: {text[:50]}...")
    
    def on_voice_generated(voice_path: str):
        print(f"🎵 音声ファイル生成: {voice_path}")
    
    def on_completion(result: GenerationResult):
        print(f"🎉 完了通知: {result.request_id}")
        print(f"   ステータス: {result.status.value}")
        print(f"   総時間: {result.total_time:.2f}秒")
    
    try:
        # エンジン開始
        await engine.start()
        
        # テストリクエスト
        test_prompts = [
            "魔法学校の新入生が初めて魔法を使う物語",
            "宇宙船の中で起こる謎の事件",
            "古い書店で見つけた不思議な本の話"
        ]
        
        # 複数リクエストの同時送信
        request_ids = []
        for i, prompt in enumerate(test_prompts):
            request_id = await engine.generate_async(
                prompt=prompt,
                settings={'temperature': 0.8, 'max_tokens': 200},
                text_callback=on_text_generated,
                voice_callback=on_voice_generated,
                completion_callback=on_completion
            )
            request_ids.append(request_id)
            print(f"✅ リクエスト{i+1}送信: {request_id}")
        
        # 処理完了まで待機
        print("\n⏳ 処理完了まで待機中...")
        start_time = time.time()
        
        while len(engine.active_requests) > 0:
            await asyncio.sleep(0.5)
            
            # 統計表示
            stats = engine.get_statistics()
            print(f"📊 進行状況: アクティブ {stats['active_requests']}, "
                  f"完了 {stats['completed_requests']}/{stats['total_requests']}")
            
            # タイムアウト処理
            if time.time() - start_time > 30.0:
                print("⏱️ タイムアウト - デモ終了")
                break
        
        # 最終統計
        final_stats = engine.get_statistics()
        print("\n📊 最終統計:")
        print(f"   成功率: {final_stats['success_rate']:.1f}%")
        print(f"   平均テキスト時間: {final_stats['average_text_time']:.2f}秒")
        print(f"   平均音声時間: {final_stats['average_voice_time']:.2f}秒")
        print(f"   平均総時間: {final_stats['average_total_time']:.2f}秒")
        print(f"   同時実行効率: {final_stats['average_concurrent_speedup']:.1f}%")
        
        print("\n🎯 並行TTS効果:")
        sequential_time = final_stats['average_text_time'] + final_stats['average_voice_time']
        concurrent_time = final_stats['average_total_time']
        speedup = (sequential_time / concurrent_time) if concurrent_time > 0 else 1.0
        print(f"   順次実行予想時間: {sequential_time:.2f}秒")
        print(f"   並行実行実時間: {concurrent_time:.2f}秒")
        print(f"   速度向上: {speedup:.1f}x")
        
    finally:
        await engine.stop()


if __name__ == "__main__":
    # デモ実行
    asyncio.run(demo_concurrent_tts()) 