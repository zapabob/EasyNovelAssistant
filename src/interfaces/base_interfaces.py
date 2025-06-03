# -*- coding: utf-8 -*-
"""
EasyNovelAssistant モジュールインターフェース定義
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class EasyNovelModule(ABC):
    """すべてのモジュールの基底クラス"""
    
    def __init__(self, context):
        self.ctx = context
        self.logger = self._setup_logging()
    
    @abstractmethod
    def initialize(self) -> bool:
        """モジュールの初期化"""
        pass
    
    @abstractmethod
    def update(self):
        """モジュールの更新処理"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """モジュールのクリーンアップ"""
        pass
    
    def _setup_logging(self):
        """ログ設定（サブクラスでオーバーライド可能）"""
        import logging
        return logging.getLogger(self.__class__.__name__)


class TextGenerator(EasyNovelModule):
    """テキスト生成インターフェース"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """テキスト生成"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """モデル情報取得"""
        pass


class UIComponent(EasyNovelModule):
    """UIコンポーネントインターフェース"""
    
    @abstractmethod
    def render(self):
        """UIレンダリング"""
        pass
    
    @abstractmethod
    def handle_event(self, event: Any):
        """イベント処理"""
        pass


class OptimizationEngine(EasyNovelModule):
    """最適化エンジンインターフェース"""
    
    @abstractmethod
    def optimize(self, target: str, **params) -> Dict[str, Any]:
        """最適化実行"""
        pass
    
    @abstractmethod
    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計取得"""
        pass
