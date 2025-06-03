"""
Integration modules for EasyNovelAssistant

このモジュールは、外部システムとの統合コンポーネントを提供します。
"""

from .kobold_cpp import KoboldCpp
from .style_bert_vits2 import StyleBertVits2
from .movie_maker import MovieMaker

__all__ = [
    'KoboldCpp',
    'StyleBertVits2',
    'MovieMaker'
] 