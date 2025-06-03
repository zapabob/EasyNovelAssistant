#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyNovelAssistant - Enhanced CLI Launcher with NKAT Integration
NKAT表現拡張システム対応版CLIランチャー
"""

import argparse
import json
import os
import sys
from pathlib import Path

def load_config(config_path: str = "config.json") -> dict:
    """設定ファイルの読み込み（UTF-8 BOM対応）"""
    try:
        # BOM付きファイルに対応
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        print(f"⚠️  設定ファイルの読み込みエラー: {e}")
        print(f"🔧 デフォルト設定で起動します")
        return {}

def save_config(config: dict, config_path: str = "config.json"):
    """設定ファイルの保存（UTF-8）"""
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def setup_nkat_config(args) -> dict:
    """NKAT設定の構成"""
    nkat_config = {
        "nkat_enabled": args.nkat,
        "theta_rank": args.theta_rank,
        "theta_gamma": args.theta_gamma,
        "expression_boost_level": args.boost_level,
        "advanced_mode": args.advanced_mode,
        "quality_guard_enabled": args.quality_guard,
        "auto_correction_threshold": args.correction_threshold,
        "diversity_target": args.diversity_target,
        "style_flexibility": args.style_flexibility
    }
    return nkat_config

def main():
    parser = argparse.ArgumentParser(
        description="EasyNovelAssistant Enhanced Launcher with NKAT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 標準起動
  python run_ena.py

  # NKAT表現拡張モード
  python run_ena.py --nkat on --boost-level 75

  # 高性能モード（RTX3080推奨）
  python run_ena.py --nkat on --theta-rank 8 --theta-gamma 0.95 --advanced-mode

  # カスタム設定
  python run_ena.py --model models/Qwen3-8B-ERP-NKAT.gguf \\
                    --nkat on --theta-rank 6 --theta-gamma 0.98 \\
                    --temperature 0.82 --top_p 0.90 --boost-level 80
        """
    )

    # 基本設定
    parser.add_argument('--model', type=str, 
                       help='使用するモデルファイルのパス')
    parser.add_argument('--config', type=str, default='config.json',
                       help='設定ファイルのパス (default: config.json)')

    # NKAT設定
    nkat_group = parser.add_argument_group('NKAT Expression Enhancement')
    nkat_group.add_argument('--nkat', type=str, choices=['on', 'off'], default='off',
                           help='NKAT表現拡張システムの有効/無効 (default: off)')
    nkat_group.add_argument('--theta-rank', type=int, default=6,
                           help='θランク: 表現幅パラメータ (default: 6, 推奨: 4-8)')
    nkat_group.add_argument('--theta-gamma', type=float, default=0.98,
                           help='θガンマ: 安定性パラメータ (default: 0.98, 範囲: 0.8-1.0)')
    nkat_group.add_argument('--boost-level', type=int, default=70, 
                           help='表現ブーストレベル %% (default: 70, 範囲: 0-100)')
    nkat_group.add_argument('--advanced-mode', action='store_true',
                           help='高度NKAT処理モードを有効化')

    # 生成パラメータ
    gen_group = parser.add_argument_group('Generation Parameters')
    gen_group.add_argument('--temperature', type=float, default=0.8,
                          help='Temperature (default: 0.8)')
    gen_group.add_argument('--top_p', type=float, default=0.9,
                          help='Top-p (default: 0.9)')
    gen_group.add_argument('--top_k', type=int, default=40,
                          help='Top-k (default: 40)')
    gen_group.add_argument('--max_tokens', type=int, default=1024,
                          help='最大生成トークン数 (default: 1024)')

    # 品質ガード設定
    quality_group = parser.add_argument_group('Quality Guard')
    quality_group.add_argument('--quality-guard', action='store_true',
                              help='品質ガード機能を有効化')
    quality_group.add_argument('--correction-threshold', type=float, default=0.03,
                              help='自動補正閾値 (default: 0.03 = 3%%)')
    quality_group.add_argument('--diversity-target', type=float, default=0.35,
                              help='語彙多様性目標値 (default: 0.35 = 35%%)')
    quality_group.add_argument('--style-flexibility', type=float, default=0.8,
                              help='文体柔軟性 (default: 0.8)')

    # システム設定
    sys_group = parser.add_argument_group('System Settings')
    sys_group.add_argument('--gpu', action='store_true',
                          help='GPU（CUDA）を使用')
    sys_group.add_argument('--threads', type=int, default=4,
                          help='CPUスレッド数 (default: 4)')
    sys_group.add_argument('--verbose', action='store_true',
                          help='詳細ログを出力')
    sys_group.add_argument('--debug', action='store_true',
                          help='デバッグモードで起動')

    args = parser.parse_args()

    # 設定ファイル読み込み
    config = load_config(args.config)

    # コマンドライン引数で設定を上書き
    if args.model:
        config['model_path'] = args.model
    
    config.update({
        'temperature': args.temperature,
        'top_p': args.top_p,
        'top_k': args.top_k,
        'max_tokens': args.max_tokens,
        'use_gpu': args.gpu,
        'num_threads': args.threads,
        'verbose_logging': args.verbose,
        'debug_mode': args.debug
    })

    # NKAT設定の適用
    if args.nkat == 'on':
        nkat_config = setup_nkat_config(args)
        config.update(nkat_config)
        
        print(f"🚀 NKAT表現拡張システム有効化")
        print(f"   ├─ θランク: {args.theta_rank}")
        print(f"   ├─ θガンマ: {args.theta_gamma}")
        print(f"   ├─ 表現ブースト: {args.boost_level}%")
        print(f"   ├─ 高度モード: {'有効' if args.advanced_mode else '無効'}")
        print(f"   └─ 品質ガード: {'有効' if args.quality_guard else '無効'}")
        
        # 性能予測表示
        estimated_vram = args.theta_rank * 0.8 + 2.5  # GB
        diversity_estimate = 29.6 + (args.boost_level - 70) * 0.1
        
        print(f"\n📊 予想性能:")
        print(f"   ├─ VRAM使用量: ~{estimated_vram:.1f}GB")
        print(f"   ├─ 語彙多様性: ~{diversity_estimate:.1f}%")
        print(f"   └─ 文体変化度: +{250 + args.boost_level * 2}%")
        
        # RTX3080最適化設定の適用
        if args.gpu and args.theta_rank >= 6:
            config.update({
                'rtx3080_optimization': True,
                'cuda_memory_fraction': 0.9,
                'mixed_precision': True,
                'gradient_checkpointing': True
            })
            print(f"\n⚡ RTX3080最適化設定を適用しました")

    # 設定保存
    save_config(config, args.config)
    
    print(f"\n🎯 起動設定: {args.config}")
    print(f"📁 モデルパス: {config.get('model_path', '未設定')}")
    
    # EasyNovelAssistantの起動
    try:
        # メインアプリケーションをインポートして起動
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from easy_novel_assistant import EasyNovelAssistant
        
        print(f"\n🚀 EasyNovelAssistant を起動しています...")
        app = EasyNovelAssistant()
        
        # NKAT設定が有効な場合、初期化を確認
        if config.get('nkat_enabled'):
            print(f"🧠 NKAT表現拡張システムを初期化中...")
            # 簡易システムチェック
            import importlib.util
            nkat_spec = importlib.util.find_spec('enhanced_nkat_expression_engine')
            if nkat_spec is None:
                print(f"⚠️  NKAT エンジンが見つかりません。標準モードで起動します。")
                config['nkat_enabled'] = False
        
        app.run_with_config(config)
        
    except ImportError as e:
        print(f"\n❌ モジュールインポートエラー: {e}")
        print(f"🔧 必要なモジュールがインストールされているか確認してください")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n👋 ユーザーによって停止されました")
    except Exception as e:
        print(f"\n❌ 起動エラー: {e}")
        print(f"🔧 設定を確認して再試行してください")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 