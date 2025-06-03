# -*- coding: utf-8 -*-
"""
反復抑制システムv3 リアルタイム制御パネル
GUI統合版 - ユーザーが直感的に反復制御を調整できるインターフェース
"""

import tkinter as tk
import tkinter.ttk as ttk
from typing import Dict, Callable, Optional


class RepetitionControlPanel:
    """反復抑制システムv3のリアルタイム制御パネル"""
    
    def __init__(self, parent, ctx, on_settings_changed: Optional[Callable] = None):
        self.ctx = ctx
        self.on_settings_changed = on_settings_changed
        
        # メインフレーム
        self.frame = ttk.LabelFrame(parent, text="🔄 反復抑制制御 v3", padding="5")
        
        # 設定値の初期化
        self.init_variables()
        
        # GUI要素の構築
        self.build_gui()
        
        # 初期設定の適用
        self.load_current_settings()
    
    def init_variables(self):
        """Tkinter変数の初期化"""
        # 基本設定
        self.similarity_threshold_var = tk.DoubleVar(value=0.35)  # v3推奨値
        self.max_distance_var = tk.IntVar(value=50)
        self.min_compress_rate_var = tk.DoubleVar(value=0.03)
        
        # v3新機能
        self.ngram_block_size_var = tk.IntVar(value=3)
        self.drp_base_var = tk.DoubleVar(value=1.10)
        self.drp_alpha_var = tk.DoubleVar(value=0.5)
        
        # トグル設定
        self.enable_4gram_var = tk.BooleanVar(value=True)
        self.enable_drp_var = tk.BooleanVar(value=True)
        self.enable_mecab_var = tk.BooleanVar(value=False)
        self.enable_rhetorical_var = tk.BooleanVar(value=False)  # 90%設定では無効
        self.enable_latin_number_var = tk.BooleanVar(value=True)
        self.aggressive_mode_var = tk.BooleanVar(value=True)
        
        # 統計表示用
        self.current_success_rate_var = tk.StringVar(value="--.--%")
        self.session_attempts_var = tk.StringVar(value="0")
        self.last_compression_rate_var = tk.StringVar(value="--.--%")
    
    def build_gui(self):
        """GUI要素の構築"""
        # === 基本設定セクション ===
        basic_frame = ttk.LabelFrame(self.frame, text="基本設定", padding="3")
        basic_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=2)
        
        # 類似度閾値
        ttk.Label(basic_frame, text="類似度閾値:").grid(row=0, column=0, sticky="w")
        similarity_scale = ttk.Scale(
            basic_frame, 
            from_=0.1, to=0.8, 
            variable=self.similarity_threshold_var,
            command=self._on_similarity_changed
        )
        similarity_scale.grid(row=0, column=1, sticky="ew", padx=5)
        self.similarity_label = ttk.Label(basic_frame, text="0.35")
        self.similarity_label.grid(row=0, column=2, sticky="w")
        
        # 最大検出距離
        ttk.Label(basic_frame, text="検出距離:").grid(row=1, column=0, sticky="w")
        distance_scale = ttk.Scale(
            basic_frame,
            from_=10, to=100,
            variable=self.max_distance_var,
            command=self._on_distance_changed
        )
        distance_scale.grid(row=1, column=1, sticky="ew", padx=5)
        self.distance_label = ttk.Label(basic_frame, text="50")
        self.distance_label.grid(row=1, column=2, sticky="w")
        
        # 最小圧縮率
        ttk.Label(basic_frame, text="圧縮基準:").grid(row=2, column=0, sticky="w")
        compress_scale = ttk.Scale(
            basic_frame,
            from_=0.01, to=0.10,
            variable=self.min_compress_rate_var,
            command=self._on_compress_changed
        )
        compress_scale.grid(row=2, column=1, sticky="ew", padx=5)
        self.compress_label = ttk.Label(basic_frame, text="3.0%")
        self.compress_label.grid(row=2, column=2, sticky="w")
        
        basic_frame.columnconfigure(1, weight=1)
        
        # === v3機能セクション ===
        v3_frame = ttk.LabelFrame(self.frame, text="v3強化機能", padding="3")
        v3_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=2)
        
        # n-gramブロック
        ttk.Label(v3_frame, text="n-gramサイズ:").grid(row=0, column=0, sticky="w")
        ngram_scale = ttk.Scale(
            v3_frame,
            from_=2, to=5,
            variable=self.ngram_block_size_var,
            command=self._on_ngram_changed
        )
        ngram_scale.grid(row=0, column=1, sticky="ew", padx=5)
        self.ngram_label = ttk.Label(v3_frame, text="3")
        self.ngram_label.grid(row=0, column=2, sticky="w")
        
        # DRP設定
        ttk.Label(v3_frame, text="DRP基準:").grid(row=1, column=0, sticky="w")
        drp_base_scale = ttk.Scale(
            v3_frame,
            from_=1.0, to=1.5,
            variable=self.drp_base_var,
            command=self._on_drp_base_changed
        )
        drp_base_scale.grid(row=1, column=1, sticky="ew", padx=5)
        self.drp_base_label = ttk.Label(v3_frame, text="1.10")
        self.drp_base_label.grid(row=1, column=2, sticky="w")
        
        ttk.Label(v3_frame, text="DRPアルファ:").grid(row=2, column=0, sticky="w")
        drp_alpha_scale = ttk.Scale(
            v3_frame,
            from_=0.1, to=1.0,
            variable=self.drp_alpha_var,
            command=self._on_drp_alpha_changed
        )
        drp_alpha_scale.grid(row=2, column=1, sticky="ew", padx=5)
        self.drp_alpha_label = ttk.Label(v3_frame, text="0.5")
        self.drp_alpha_label.grid(row=2, column=2, sticky="w")
        
        v3_frame.columnconfigure(1, weight=1)
        
        # === トグル設定セクション ===
        toggle_frame = ttk.LabelFrame(self.frame, text="機能切替", padding="3")
        toggle_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=2)
        
        # チェックボックス群
        toggles = [
            (self.enable_4gram_var, "4-gramブロック", 0, 0),
            (self.enable_drp_var, "DRP有効化", 0, 1),
            (self.aggressive_mode_var, "アグレッシブモード", 1, 0),
            (self.enable_latin_number_var, "連番検知", 1, 1),
            (self.enable_mecab_var, "MeCab正規化", 2, 0),
            (self.enable_rhetorical_var, "修辞的保護", 2, 1)
        ]
        
        for var, text, row, col in toggles:
            checkbox = ttk.Checkbutton(
                toggle_frame, 
                text=text, 
                variable=var,
                command=self._on_toggle_changed
            )
            checkbox.grid(row=row, column=col, sticky="w", padx=5, pady=1)
        
        # === 統計表示セクション ===
        stats_frame = ttk.LabelFrame(self.frame, text="リアルタイム統計", padding="3")
        stats_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=2)
        
        ttk.Label(stats_frame, text="成功率:").grid(row=0, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.current_success_rate_var).grid(row=0, column=1, sticky="w")
        
        ttk.Label(stats_frame, text="実行回数:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        ttk.Label(stats_frame, textvariable=self.session_attempts_var).grid(row=0, column=3, sticky="w")
        
        ttk.Label(stats_frame, text="最終圧縮率:").grid(row=1, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.last_compression_rate_var).grid(row=1, column=1, sticky="w")
        
        # === 操作ボタンセクション ===
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=2)
        
        ttk.Button(
            button_frame, 
            text="設定リセット", 
            command=self.reset_to_defaults
        ).grid(row=0, column=0, padx=2)
        
        ttk.Button(
            button_frame, 
            text="90%推奨設定", 
            command=self.apply_90_percent_config
        ).grid(row=0, column=1, padx=2)
        
        ttk.Button(
            button_frame, 
            text="現在設定を保存", 
            command=self.save_current_settings
        ).grid(row=0, column=2, padx=2)
        
        # フレーム全体の重み調整
        self.frame.columnconfigure(0, weight=1)
    
    def _on_similarity_changed(self, value):
        """類似度閾値変更時のコールバック"""
        val = float(value)
        self.similarity_label.config(text=f"{val:.2f}")
        self._notify_settings_changed()
    
    def _on_distance_changed(self, value):
        """検出距離変更時のコールバック"""
        val = int(float(value))
        self.distance_label.config(text=str(val))
        self._notify_settings_changed()
    
    def _on_compress_changed(self, value):
        """圧縮率変更時のコールバック"""
        val = float(value)
        self.compress_label.config(text=f"{val:.1%}")
        self._notify_settings_changed()
    
    def _on_ngram_changed(self, value):
        """n-gramサイズ変更時のコールバック"""
        val = int(float(value))
        self.ngram_label.config(text=str(val))
        self._notify_settings_changed()
    
    def _on_drp_base_changed(self, value):
        """DRP基準値変更時のコールバック"""
        val = float(value)
        self.drp_base_label.config(text=f"{val:.2f}")
        self._notify_settings_changed()
    
    def _on_drp_alpha_changed(self, value):
        """DRPアルファ値変更時のコールバック"""
        val = float(value)
        self.drp_alpha_label.config(text=f"{val:.1f}")
        self._notify_settings_changed()
    
    def _on_toggle_changed(self):
        """トグル設定変更時のコールバック"""
        self._notify_settings_changed()
    
    def _notify_settings_changed(self):
        """設定変更通知"""
        if self.on_settings_changed:
            settings = self.get_current_settings()
            self.on_settings_changed(settings)
    
    def get_current_settings(self) -> Dict:
        """現在の設定値を取得"""
        return {
            'similarity_threshold': self.similarity_threshold_var.get(),
            'max_distance': self.max_distance_var.get(),
            'min_compress_rate': self.min_compress_rate_var.get(),
            'ngram_block_size': self.ngram_block_size_var.get(),
            'enable_4gram_blocking': self.enable_4gram_var.get(),
            'drp_base': self.drp_base_var.get(),
            'drp_alpha': self.drp_alpha_var.get(),
            'enable_drp': self.enable_drp_var.get(),
            'enable_mecab_normalization': self.enable_mecab_var.get(),
            'enable_rhetorical_protection': self.enable_rhetorical_var.get(),
            'enable_latin_number_detection': self.enable_latin_number_var.get(),
            'enable_aggressive_mode': self.aggressive_mode_var.get()
        }
    
    def apply_settings(self, settings: Dict):
        """設定値を適用"""
        self.similarity_threshold_var.set(settings.get('similarity_threshold', 0.35))
        self.max_distance_var.set(settings.get('max_distance', 50))
        self.min_compress_rate_var.set(settings.get('min_compress_rate', 0.03))
        self.ngram_block_size_var.set(settings.get('ngram_block_size', 3))
        self.drp_base_var.set(settings.get('drp_base', 1.10))
        self.drp_alpha_var.set(settings.get('drp_alpha', 0.5))
        
        self.enable_4gram_var.set(settings.get('enable_4gram_blocking', True))
        self.enable_drp_var.set(settings.get('enable_drp', True))
        self.enable_mecab_var.set(settings.get('enable_mecab_normalization', False))
        self.enable_rhetorical_var.set(settings.get('enable_rhetorical_protection', False))
        self.enable_latin_number_var.set(settings.get('enable_latin_number_detection', True))
        self.aggressive_mode_var.set(settings.get('enable_aggressive_mode', True))
        
        # ラベル更新
        self._update_all_labels()
    
    def _update_all_labels(self):
        """全ラベルの更新"""
        self.similarity_label.config(text=f"{self.similarity_threshold_var.get():.2f}")
        self.distance_label.config(text=str(self.max_distance_var.get()))
        self.compress_label.config(text=f"{self.min_compress_rate_var.get():.1%}")
        self.ngram_label.config(text=str(self.ngram_block_size_var.get()))
        self.drp_base_label.config(text=f"{self.drp_base_var.get():.2f}")
        self.drp_alpha_label.config(text=f"{self.drp_alpha_var.get():.1f}")
    
    def reset_to_defaults(self):
        """デフォルト設定にリセット"""
        default_settings = {
            'similarity_threshold': 0.50,
            'max_distance': 30,
            'min_compress_rate': 0.05,
            'ngram_block_size': 4,
            'drp_base': 1.05,
            'drp_alpha': 0.4,
            'enable_4gram_blocking': False,
            'enable_drp': False,
            'enable_mecab_normalization': False,
            'enable_rhetorical_protection': True,
            'enable_latin_number_detection': False,
            'enable_aggressive_mode': False
        }
        self.apply_settings(default_settings)
        self._notify_settings_changed()
    
    def apply_90_percent_config(self):
        """90%成功率達成設定を適用"""
        optimal_settings = {
            'similarity_threshold': 0.35,  # 実証済み最適値
            'max_distance': 50,
            'min_compress_rate': 0.03,
            'ngram_block_size': 3,
            'drp_base': 1.10,
            'drp_alpha': 0.5,
            'enable_4gram_blocking': True,
            'enable_drp': True,
            'enable_mecab_normalization': False,
            'enable_rhetorical_protection': False,  # 90%設定では無効
            'enable_latin_number_detection': True,
            'enable_aggressive_mode': True
        }
        self.apply_settings(optimal_settings)
        self._notify_settings_changed()
    
    def load_current_settings(self):
        """現在のシステム設定を読み込み"""
        if hasattr(self.ctx, 'repetition_suppressor') and self.ctx.repetition_suppressor:
            suppressor = self.ctx.repetition_suppressor
            current_config = getattr(suppressor, 'config', {})
            
            if current_config:
                self.apply_settings(current_config)
    
    def save_current_settings(self):
        """現在の設定をコンテキストに保存"""
        settings = self.get_current_settings()
        
        # コンテキストに保存
        for key, value in settings.items():
            self.ctx[f"repetition_{key}"] = value
        
        # 反復抑制システムの設定更新
        if hasattr(self.ctx, 'repetition_suppressor') and self.ctx.repetition_suppressor:
            self.ctx.repetition_suppressor.update_config(settings)
        
        print("🔄 反復抑制設定を保存しました")
    
    def update_statistics(self, success_rate: float = None, attempts: int = None, compression_rate: float = None):
        """統計情報の更新"""
        if success_rate is not None:
            self.current_success_rate_var.set(f"{success_rate:.1%}")
        
        if attempts is not None:
            self.session_attempts_var.set(str(attempts))
        
        if compression_rate is not None:
            self.last_compression_rate_var.set(f"{compression_rate:.1%}")
    
    def pack(self, **kwargs):
        """パネルの配置"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """パネルのグリッド配置"""
        self.frame.grid(**kwargs) 