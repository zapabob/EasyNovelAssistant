# -*- coding: utf-8 -*-
"""
Core双方向バインディング機能テスト
GUI環境に依存しない機能確認
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from ui.bidirectional_binding import BindableProperty, ENASettingsModel, BidirectionalBinder
import time

def test_core_binding():
    """Core双方向バインディング機能テスト"""
    print('🧪 Core バインディング機能テスト')
    print('=' * 40)

    # 1. BindableProperty基本テスト
    print('\n1. BindableProperty テスト:')
    prop = BindableProperty(42, int)
    print(f'初期値: {prop.value}')

    # 変更監視テスト
    changed_values = []
    prop.subscribe(lambda v: changed_values.append(v))

    prop.value = 100
    print(f'変更後: {prop.value}')
    print(f'通知履歴: {changed_values}')

    # 2. ENASettingsModel テスト
    print('\n2. ENASettingsModel テスト:')
    model = ENASettingsModel()
    print(f'デフォルト similarity_threshold: {model.get_value("similarity_threshold")}')
    print(f'デフォルト enable_4gram: {model.get_value("enable_4gram")}')

    model.set_value('similarity_threshold', 0.7)
    model.set_value('enable_4gram', False)
    print(f'更新後 similarity_threshold: {model.get_value("similarity_threshold")}')
    print(f'更新後 enable_4gram: {model.get_value("enable_4gram")}')

    # 3. 設定辞書テスト
    print('\n3. 設定辞書変換テスト:')
    settings_dict = model.to_dict()
    print(f'辞書変換: {list(settings_dict.keys())[:5]}...')

    new_settings = {'similarity_threshold': 0.9, 'max_distance': 80}
    model.load_from_dict(new_settings)
    print(f'辞書読み込み後 similarity_threshold: {model.get_value("similarity_threshold")}')

    # 4. プロパティ間バインディングテスト
    print('\n4. プロパティ間バインディング テスト:')
    from ui.bidirectional_binding import DataModel
    
    source_model = DataModel()
    target_model = DataModel()
    
    source_model.add_property('source_value', 100, int)
    target_model.add_property('target_value', 0, int)
    
    # 双方向バインディング設定
    source_prop = source_model.get_property('source_value')
    target_prop = target_model.get_property('target_value')
    
    # 手動双方向リンク
    source_prop.subscribe(lambda val: setattr(target_prop, 'value', val))
    target_prop.subscribe(lambda val: setattr(source_prop, 'value', val))
    
    print(f'初期状態 source: {source_model.get_value("source_value")}, target: {target_model.get_value("target_value")}')
    
    source_model.set_value('source_value', 200)
    print(f'source変更後 source: {source_model.get_value("source_value")}, target: {target_model.get_value("target_value")}')
    
    target_model.set_value('target_value', 300)
    print(f'target変更後 source: {source_model.get_value("source_value")}, target: {target_model.get_value("target_value")}')

    print('\n✅ Core双方向バインディング テスト完了!')
    print('   🟠 GUI ↔ Core 双方向バインド Core部分準備OK')
    
    return True

if __name__ == "__main__":
    test_core_binding() 