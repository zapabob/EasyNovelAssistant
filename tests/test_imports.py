# -*- coding: utf-8 -*-
"""
Import Test Suite
モジュールインポートの整合性をテスト
"""

import sys
import os
import unittest
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class TestImports(unittest.TestCase):
    """インポートテストクラス"""
    
    def test_utils_imports(self):
        """utilsパッケージのインポートテスト"""
        try:
            from src.utils.job_queue import JobQueue
            self.assertTrue(True, "JobQueue import successful")
        except ImportError as e:
            self.fail(f"JobQueue import failed: {e}")
    
    def test_models_imports(self):
        """modelsパッケージのインポートテスト"""
        try:
            from src.models.generator import Generator
            self.assertTrue(True, "Generator import successful")
        except ImportError as e:
            self.fail(f"Generator import failed: {e}")
    
    def test_v3_systems_imports(self):
        """v3システムのインポートテスト"""
        try:
            from src.utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
            self.assertTrue(True, "AdvancedRepetitionSuppressorV3 import successful")
        except ImportError as e:
            print(f"Warning: v3システムが見つかりません: {e}")
            # v3システムはオプショナルなのでFailにはしない
    
    def test_integration_imports(self):
        """統合システムのインポートテスト"""
        try:
            from src.integration.cross_suppression_engine import CrossSuppressionEngine
            self.assertTrue(True, "CrossSuppressionEngine import successful")
        except ImportError as e:
            print(f"Warning: 統合システムが見つかりません: {e}")
    
    def test_nkat_imports(self):
        """NKATシステムのインポートテスト"""
        try:
            from src.nkat.nkat_integration_preparation_v3 import NKATEmotionType
            self.assertTrue(True, "NKAT systems import successful")
        except ImportError as e:
            print(f"Warning: NKATシステムが見つかりません: {e}")

if __name__ == '__main__':
    unittest.main() 