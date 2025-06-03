"""
EasyNovelAssistant Application Package

このパッケージは、EasyNovelAssistantのメインアプリケーションロジックを含んでいます。

Modules:
    core: コアロジック（context, const, path）
    ui: ユーザーインターフェース（form, input_area, output_area, gen_area）
    integrations: 外部システム連携（kobold_cpp, style_bert_vits2, movie_maker）
    utils: ユーティリティ（generator, gguf_manager, job_queue, gguf_addon_system）
    dialogs: ダイアログ（model_add_dialog, integration_control_panel）
"""

__version__ = "3.0.4"
__author__ = "EasyNovelAssistant Development Team"

# 互換性のためのメインモジュール再エクスポート
from .core.context import Context
from .core.const import Const
from .core.path import Path

__all__ = [
    'Context',
    'Const', 
    'Path'
] 