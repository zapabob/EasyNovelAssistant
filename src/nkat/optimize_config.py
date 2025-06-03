# -*- coding: utf-8 -*-
"""
RTX 3080環境でのCUDA最適化設定管理
CUDA 12.4対応KoboldCppの最適化パラメータを自動設定
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path


class RTX3080Optimizer:
    """RTX 3080専用の最適化設定クラス"""
    
    # RTX 3080の仕様
    VRAM_SIZE_GB = 10
    CUDA_CORES = 8704
    RT_CORES = 68
    TENSOR_CORES = 272
    
    # 推奨設定値
    RECOMMENDED_GPU_LAYERS = {
        "7B": 33,      # 7Bモデル用
        "8B": 35,      # 8Bモデル用  
        "13B": 25,     # 13Bモデル用
        "34B": 15,     # 34Bモデル用（部分的GPU利用）
        "70B": 8       # 70Bモデル用（最小限GPU利用）
    }
    
    # 量子化別メモリ効率
    QUANTIZATION_MEMORY = {
        "Q4_K_M": {"efficiency": 0.85, "quality": 0.95},
        "Q4_K_S": {"efficiency": 0.90, "quality": 0.92},
        "Q5_K_M": {"efficiency": 0.75, "quality": 0.98},
        "Q8_0": {"efficiency": 0.60, "quality": 0.99},
        "fp16": {"efficiency": 0.40, "quality": 1.0}
    }
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self):
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def save_config(self):
        """最適化された設定を保存"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
            
    def detect_gpu_capabilities(self):
        """GPU能力を自動検出"""
        try:
            # nvidia-smiを使用してGPU情報を取得
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                gpu_info = result.stdout.strip().split(', ')
                if len(gpu_info) >= 3:
                    gpu_name = gpu_info[0]
                    vram_mb = int(gpu_info[1])
                    driver_version = gpu_info[2]
                    
                    return {
                        "gpu_name": gpu_name,
                        "vram_gb": vram_mb / 1024,
                        "driver_version": driver_version,
                        "is_rtx_3080": "RTX 3080" in gpu_name
                    }
        except Exception as e:
            print(f"GPU検出エラー: {e}")
            
        return {"gpu_name": "Unknown", "vram_gb": 8, "driver_version": "Unknown", "is_rtx_3080": False}
        
    def estimate_model_size(self, model_name):
        """モデル名からサイズと量子化を推定"""
        model_name_lower = model_name.lower()
        
        # モデルサイズ推定
        if "7b" in model_name_lower:
            size = "7B"
        elif "8b" in model_name_lower:
            size = "8B"
        elif "13b" in model_name_lower:
            size = "13B"
        elif "34b" in model_name_lower or "35b" in model_name_lower:
            size = "34B"
        elif "70b" in model_name_lower:
            size = "70B"
        else:
            size = "8B"  # デフォルト
            
        # 量子化タイプ推定
        quantization = "Q4_K_M"  # デフォルト
        for quant_type in self.QUANTIZATION_MEMORY.keys():
            if quant_type.lower() in model_name_lower:
                quantization = quant_type
                break
                
        return size, quantization
        
    def optimize_for_rtx3080(self, model_name=None):
        """RTX 3080向けの最適化設定を生成"""
        gpu_info = self.detect_gpu_capabilities()
        
        if model_name is None:
            model_name = self.config.get("llm_name", "unknown")
            
        model_size, quantization = self.estimate_model_size(model_name)
        
        # GPU層数の最適化
        recommended_layers = self.RECOMMENDED_GPU_LAYERS.get(model_size, 25)
        
        # VRAMメモリ効率を考慮した調整
        memory_efficiency = self.QUANTIZATION_MEMORY.get(quantization, {"efficiency": 0.8})["efficiency"]
        adjusted_layers = int(recommended_layers * memory_efficiency)
        
        # RTX 3080固有の最適化
        if gpu_info["is_rtx_3080"]:
            adjusted_layers = min(adjusted_layers + 5, 65)  # RTX 3080ボーナス
            
        # 最適化設定
        optimized_config = {
            "llm_gpu_layer": adjusted_layers,
            "koboldcpp_arg": "--usecublas --gpulayers-split --noblas --nommap",
            "llm_context_size": min(8192, 16384),  # 安定性重視
            "temperature": 0.6,
            "top_p": 0.92,
            "top_k": 100,
            "rep_pen": 1.1,
            "rep_pen_range": 320,
            "tfs": 1.0,
            "batch_size": 512,
            "threads": min(8, os.cpu_count()),  # 物理コア数に調整
        }
        
        # 設定を更新
        self.config.update(optimized_config)
        
        return {
            "model_info": {
                "name": model_name,
                "size": model_size,
                "quantization": quantization
            },
            "gpu_info": gpu_info,
            "optimized_settings": optimized_config,
            "expected_performance": self._estimate_performance(model_size, quantization, adjusted_layers)
        }
        
    def _estimate_performance(self, model_size, quantization, gpu_layers):
        """性能予測"""
        base_tokens_per_sec = {
            "7B": 45, "8B": 40, "13B": 25, "34B": 12, "70B": 6
        }
        
        base_speed = base_tokens_per_sec.get(model_size, 30)
        quant_multiplier = self.QUANTIZATION_MEMORY.get(quantization, {"efficiency": 0.8})["efficiency"]
        gpu_multiplier = min(gpu_layers / 30, 1.5)  # GPU利用率による高速化
        
        estimated_tokens_per_sec = base_speed * quant_multiplier * gpu_multiplier
        
        return {
            "estimated_tokens_per_sec": round(estimated_tokens_per_sec, 1),
            "gpu_utilization": f"{min(gpu_layers / 40 * 100, 100):.0f}%",
            "memory_efficiency": f"{quant_multiplier * 100:.0f}%"
        }
        
    def create_optimized_launch_script(self, model_name):
        """最適化されたKoboldCpp起動スクリプトを生成"""
        optimization_result = self.optimize_for_rtx3080(model_name)
        settings = optimization_result["optimized_settings"]
        
        script_content = f"""@echo off
chcp 65001 > NUL
echo RTX 3080最適化設定でKoboldCppを起動中...
echo モデル: {model_name}
echo GPU層数: {settings['llm_gpu_layer']}
echo 予想性能: {optimization_result['expected_performance']['estimated_tokens_per_sec']} tokens/sec

pushd %~dp0\\KoboldCpp

koboldcpp.exe {settings['koboldcpp_arg']} --gpulayers {settings['llm_gpu_layer']} --contextsize {settings['llm_context_size']} --threads {settings['threads']} "{model_name}"

if %errorlevel% neq 0 ( 
    echo エラーが発生しました。設定を確認してください。
    pause 
    popd 
    exit /b 1 
)
popd
"""
        
        script_path = f"Run-Optimized-RTX3080-{model_name.replace('.gguf', '')}.bat"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        return script_path
        
    def monitor_performance(self):
        """リアルタイム性能監視"""
        try:
            # GPU使用率監視
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                gpu_util, mem_used, mem_total, temp = result.stdout.strip().split(', ')
                
                return {
                    "gpu_utilization": f"{gpu_util}%",
                    "memory_usage": f"{mem_used}/{mem_total} MB",
                    "memory_percent": f"{int(mem_used)/int(mem_total)*100:.1f}%",
                    "temperature": f"{temp}°C",
                    "status": "optimal" if int(gpu_util) > 80 and int(temp) < 80 else "suboptimal"
                }
        except Exception as e:
            print(f"性能監視エラー: {e}")
            
        return {"status": "monitoring_failed"}


if __name__ == "__main__":
    optimizer = RTX3080Optimizer()
    
    # 使用例
    if len(sys.argv) > 1:
        model_name = sys.argv[1]
        result = optimizer.optimize_for_rtx3080(model_name)
        
        print("=== RTX 3080 最適化結果 ===")
        print(f"モデル: {result['model_info']['name']}")
        print(f"サイズ: {result['model_info']['size']}")
        print(f"量子化: {result['model_info']['quantization']}")
        print(f"推奨GPU層数: {result['optimized_settings']['llm_gpu_layer']}")
        print(f"予想性能: {result['expected_performance']['estimated_tokens_per_sec']} tokens/sec")
        print(f"GPU利用率: {result['expected_performance']['gpu_utilization']}")
        
        # 設定保存
        optimizer.save_config()
        
        # 最適化スクリプト生成
        script_path = optimizer.create_optimized_launch_script(model_name)
        print(f"最適化起動スクリプト作成: {script_path}")
        
    else:
        print("使用法: python optimize_config.py <model_name.gguf>") 