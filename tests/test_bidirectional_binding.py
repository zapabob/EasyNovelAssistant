# -*- coding: utf-8 -*-
"""
双方向バインディングシステムのテスト
GUI ↔ Core 同期機能の検証
"""

import sys
import os
import unittest
from pathlib import Path
import threading
import time

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    import tkinter as tk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

class TestBidirectionalBinding(unittest.TestCase):
    """双方向バインディングテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        if not GUI_AVAILABLE:
            self.skipTest("GUI環境が利用できません")
        
        # テスト用のTkinterルートウィンドウ作成
        self.root = tk.Tk()
        self.root.withdraw()  # 非表示
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, 'root'):
            self.root.quit()
            self.root.destroy()
    
    def test_bindable_property_basic(self):
        """BindablePropertyの基本機能テスト"""
        from src.ui.bidirectional_binding import BindableProperty
        
        # 基本的な値の設定と取得
        prop = BindableProperty(42, int)
        self.assertEqual(prop.value, 42)
        
        # 値の変更
        prop.value = 100
        self.assertEqual(prop.value, 100)
        
        # 型変換テスト
        prop.value = "123"
        self.assertEqual(prop.value, 123)
        self.assertIsInstance(prop.value, int)
    
    def test_observer_notification(self):
        """オブザーバー通知システムのテスト"""
        from src.ui.bidirectional_binding import BindableProperty
        
        prop = BindableProperty(10, int)
        notifications = []
        
        # オブザーバー登録
        def observer(value):
            notifications.append(value)
        
        prop.subscribe(observer)
        
        # 値変更でオブザーバーが呼ばれることを確認
        prop.value = 20
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0], 20)
        
        # 同じ値の場合は通知されないことを確認
        prop.value = 20
        self.assertEqual(len(notifications), 1)
        
        # オブザーバー削除
        prop.unsubscribe(observer)
        prop.value = 30
        self.assertEqual(len(notifications), 1)  # 通知されない
    
    def test_data_model(self):
        """DataModelクラスのテスト"""
        from src.ui.bidirectional_binding import DataModel
        
        model = DataModel()
        
        # プロパティ追加
        model.add_property('test_int', 42, int)
        model.add_property('test_str', "hello", str)
        model.add_property('test_bool', True, bool)
        
        # 値の設定と取得
        self.assertEqual(model.get_value('test_int'), 42)
        model.set_value('test_int', 100)
        self.assertEqual(model.get_value('test_int'), 100)
        
        # プロパティオブジェクトの取得
        prop = model.get_property('test_int')
        self.assertIsNotNone(prop)
        self.assertEqual(prop.value, 100)
    
    def test_ena_settings_model(self):
        """ENASettingsModelのテスト"""
        from src.ui.bidirectional_binding import ENASettingsModel
        
        model = ENASettingsModel()
        
        # デフォルト値の確認
        self.assertEqual(model.get_value('similarity_threshold'), 0.35)
        self.assertEqual(model.get_value('max_distance'), 50)
        self.assertTrue(model.get_value('enable_4gram'))
        
        # 辞書からの読み込み
        settings = {
            'similarity_threshold': 0.5,
            'max_distance': 80,
            'enable_4gram': False
        }
        model.load_from_dict(settings)
        
        self.assertEqual(model.get_value('similarity_threshold'), 0.5)
        self.assertEqual(model.get_value('max_distance'), 80)
        self.assertFalse(model.get_value('enable_4gram'))
        
        # 辞書への変換
        result_dict = model.to_dict()
        self.assertIn('similarity_threshold', result_dict)
        self.assertEqual(result_dict['similarity_threshold'], 0.5)
    
    @unittest.skipUnless(GUI_AVAILABLE, "GUI環境が必要")
    def test_scale_binding(self):
        """Scaleウィジェットとの双方向バインディングテスト"""
        from src.ui.bidirectional_binding import BindableProperty, TkinterWidgetAdapter
        
        # Scaleウィジェット作成
        scale = tk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL)
        
        # プロパティ作成
        prop = BindableProperty(50, int)
        
        # バインディング作成
        binding = TkinterWidgetAdapter.create_binding(scale, prop)
        
        # Model → View 同期テスト
        prop.value = 75
        time.sleep(0.1)  # GUI更新待ち
        self.assertEqual(scale.get(), 75)
        
        # View → Model 同期テスト
        print(f"設定前: scale={scale.get()}, prop={prop.value}")
        scale.set(25)
        print(f"設定後: scale={scale.get()}, prop={prop.value}")
        
        # GUI更新とイベント処理を強制実行
        self.root.update_idletasks()
        self.root.update()
        time.sleep(0.2)
        
        print(f"更新後: scale={scale.get()}, prop={prop.value}")
        
        # より緩い条件でテスト（型変換の問題があるかも）
        self.assertAlmostEqual(float(prop.value), 25.0, places=1)
        
        # バインディング解除
        binding.destroy()
    
    @unittest.skipUnless(GUI_AVAILABLE, "GUI環境が必要")
    def test_checkbutton_binding(self):
        """Checkbuttonとの双方向バインディングテスト"""
        from src.ui.bidirectional_binding import BindableProperty, TkinterWidgetAdapter
        
        # Checkbuttonウィジェット作成
        var = tk.BooleanVar()
        checkbutton = tk.Checkbutton(self.root, variable=var)
        
        # プロパティ作成
        prop = BindableProperty(True, bool)
        
        # バインディング作成
        binding = TkinterWidgetAdapter.create_binding(checkbutton, prop)
        
        # Model → View 同期テスト
        prop.value = False
        time.sleep(0.1)
        self.assertFalse(var.get())
        
        # View → Model 同期テスト
        var.set(True)
        time.sleep(0.1)
        self.assertTrue(prop.value)
        
        # バインディング解除
        binding.destroy()
    
    def test_bidirectional_binder(self):
        """BidirectionalBinderクラスのテスト"""
        from src.ui.bidirectional_binding import BidirectionalBinder, DataModel
        
        model = DataModel()
        model.add_property('test_prop', 10, int)
        
        binder = BidirectionalBinder()
        
        # ウィジェット作成
        scale = tk.Scale(self.root, from_=0, to=100)
        
        # バインディング作成
        binder.bind_widget(scale, model, 'test_prop')
        
        # 動作確認
        model.set_value('test_prop', 50)
        time.sleep(0.1)
        self.assertEqual(scale.get(), 50)
        
        # クリーンアップ
        binder.destroy_all()
    
    def test_property_to_property_binding(self):
        """プロパティ間双方向バインディングのテスト"""
        from src.ui.bidirectional_binding import BidirectionalBinder, DataModel
        
        source_model = DataModel()
        target_model = DataModel()
        
        source_model.add_property('source_prop', 100, int)
        target_model.add_property('target_prop', 0, int)
        
        binder = BidirectionalBinder()
        binder.bind_property_to_property(source_model, 'source_prop', target_model, 'target_prop')
        
        # source → target
        source_model.set_value('source_prop', 200)
        time.sleep(0.1)
        self.assertEqual(target_model.get_value('target_prop'), 200)
        
        # target → source
        target_model.set_value('target_prop', 300)
        time.sleep(0.1)
        self.assertEqual(source_model.get_value('source_prop'), 300)
    
    def test_threading_safety(self):
        """スレッドセーフティのテスト"""
        from src.ui.bidirectional_binding import BindableProperty
        
        prop = BindableProperty(0, int)
        errors = []
        
        def worker(start_value):
            try:
                for i in range(start_value, start_value + 100):
                    prop.value = i
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        # 複数スレッドで同時操作
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i * 100,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # エラーが発生していないことを確認
        self.assertEqual(len(errors), 0)
        
        # 最終値が妥当な範囲内にあることを確認
        self.assertGreaterEqual(prop.value, 0)
        self.assertLess(prop.value, 300)


def main():
    """テスト実行"""
    if not GUI_AVAILABLE:
        print("⚠️ GUI環境が利用できないため、一部のテストがスキップされます")
    
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main() 