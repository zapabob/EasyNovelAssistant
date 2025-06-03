# -*- coding: utf-8 -*-
"""
EasyNovelAssistant 双方向データバインディングシステム
tkpf / qt-python-mvc アーキテクチャを参考にした統合GUI制御

特徴:
- View ↔ Model双方向同期 
- リアルタイム変更監視
- コールバック通知システム
- 型安全な値変換
"""

import tkinter as tk
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic, get_type_hints
from abc import ABC, abstractmethod
import threading
import time
from collections import defaultdict

T = TypeVar('T')


class BindableProperty(Generic[T]):
    """バインド可能プロパティ - WPF DependencyProperty風"""
    
    def __init__(self, initial_value: T, property_type: type = None):
        self._value = initial_value
        self._type = property_type or type(initial_value)
        self._observers: List[Callable[[T], None]] = []
        self._lock = threading.RLock()
    
    @property
    def value(self) -> T:
        with self._lock:
            return self._value
    
    @value.setter
    def value(self, new_value: T) -> None:
        with self._lock:
            # 型変換
            converted_value = self._convert_value(new_value)
            
            # 値が変わった場合のみ通知
            if converted_value != self._value:
                old_value = self._value
                self._value = converted_value
                self._notify_observers(converted_value, old_value)
    
    def _convert_value(self, value: Any) -> T:
        """型変換処理"""
        try:
            if self._type == bool:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif self._type == int:
                return int(float(value))  # 小数点付き文字列対応
            elif self._type == float:
                return float(value)
            elif self._type == str:
                return str(value)
            else:
                return self._type(value)
        except (ValueError, TypeError):
            return self._value  # 変換失敗時は現在値を維持
    
    def _notify_observers(self, new_value: T, old_value: T) -> None:
        """オブザーバーへの通知"""
        for observer in self._observers[:]:  # コピーして安全に反復
            try:
                observer(new_value)
            except Exception as e:
                print(f"⚠️ Observer notification error: {e}")
    
    def subscribe(self, observer: Callable[[T], None]) -> None:
        """オブザーバー登録"""
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)
    
    def unsubscribe(self, observer: Callable[[T], None]) -> None:
        """オブザーバー削除"""
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)


class TkinterWidgetAdapter:
    """Tkinter ウィジェット アダプター"""
    
    # ウィジェット別の設定情報
    WIDGET_CONFIGS = {
        tk.Scale: {
            'get_method': 'get',
            'set_method': 'set',
            'change_event': ['<ButtonRelease-1>', '<Button-1>', '<B1-Motion>'],
            'value_type': float
        },
        tk.ttk.Scale: {
            'get_method': 'get', 
            'set_method': 'set',
            'change_event': ['<ButtonRelease-1>', '<Button-1>', '<B1-Motion>'],
            'value_type': float
        },
        tk.Checkbutton: {
            'variable_property': True,
            'value_type': bool
        },
        tk.ttk.Checkbutton: {
            'variable_property': True,
            'value_type': bool
        },
        tk.Entry: {
            'variable_property': True,
            'value_type': str
        },
        tk.ttk.Entry: {
            'variable_property': True,
            'value_type': str
        },
        tk.Spinbox: {
            'variable_property': True,
            'value_type': int
        },
        tk.ttk.Spinbox: {
            'variable_property': True,
            'value_type': int
        }
    }
    
    @classmethod
    def create_binding(cls, widget, property_obj: BindableProperty, 
                      initial_sync: bool = True) -> 'TkinterBinding':
        """ウィジェット用バインディング作成"""
        widget_type = type(widget)
        config = cls.WIDGET_CONFIGS.get(widget_type, {})
        
        if 'variable_property' in config:
            return VariableBasedBinding(widget, property_obj, config, initial_sync)
        else:
            return MethodBasedBinding(widget, property_obj, config, initial_sync)


class TkinterBinding:
    """Tkinter バインディング基底クラス"""
    
    def __init__(self, widget, property_obj: BindableProperty, config: Dict, initial_sync: bool):
        self.widget = widget
        self.property_obj = property_obj
        self.config = config
        self._updating = False  # 循環参照防止
        
        # Model → View の購読
        property_obj.subscribe(self._on_model_changed)
        
        # 初期同期
        if initial_sync:
            self._sync_view_to_model()
    
    @abstractmethod
    def _sync_view_to_model(self) -> None:
        """Model → View 同期"""
        pass
    
    @abstractmethod
    def _sync_model_to_view(self) -> None:
        """View → Model 同期"""
        pass
    
    def _on_model_changed(self, new_value: Any) -> None:
        """モデル値変更時のコールバック"""
        if not self._updating:
            self._updating = True
            try:
                self._sync_view_to_model()
            finally:
                self._updating = False
    
    def destroy(self) -> None:
        """バインディング解除"""
        self.property_obj.unsubscribe(self._on_model_changed)


class VariableBasedBinding(TkinterBinding):
    """tk.Variable を使用するウィジェット用バインディング"""
    
    def __init__(self, widget, property_obj: BindableProperty, config: Dict, initial_sync: bool):
        # 先に設定を保存
        self.config = config
        
        # 対応する tk.Variable の作成/取得
        self.tk_var = self._get_or_create_variable(property_obj)
        
        # View → Model の監視
        self.tk_var.trace_add('write', self._on_view_changed)
        
        # ウィジェットにVariable設定
        variable_option = self._get_variable_option(widget)
        widget.configure(**{variable_option: self.tk_var})
        
        # 親クラスの初期化（tk_var設定後に実行）
        super().__init__(widget, property_obj, config, initial_sync)
    
    def _get_variable_option(self, widget) -> str:
        """ウィジェットのVariable設定オプション名を取得"""
        if hasattr(widget, 'configure'):
            # 一般的なVariableオプション名を試す
            for option in ['textvariable', 'variable']:
                try:
                    # まず現在の設定を確認
                    current_config = widget.configure(option)
                    return option
                except tk.TclError:
                    continue
        return 'variable'  # デフォルト
    
    def _get_or_create_variable(self, property_obj) -> tk.Variable:
        """適切な tk.Variable を作成"""
        value_type = self.config.get('value_type', str)
        
        if value_type == bool:
            return tk.BooleanVar(value=property_obj.value)
        elif value_type == int:
            return tk.IntVar(value=property_obj.value)
        elif value_type == float:
            return tk.DoubleVar(value=property_obj.value)
        else:
            return tk.StringVar(value=str(property_obj.value))
    
    def _sync_view_to_model(self) -> None:
        """Model → View 同期"""
        self.tk_var.set(self.property_obj.value)
    
    def _sync_model_to_view(self) -> None:
        """View → Model 同期"""
        self.property_obj.value = self.tk_var.get()
    
    def _on_view_changed(self, *args) -> None:
        """View値変更時のコールバック"""
        if not self._updating:
            self._updating = True
            try:
                self._sync_model_to_view()
            finally:
                self._updating = False


class MethodBasedBinding(TkinterBinding):
    """get/set メソッドを使用するウィジェット用バインディング"""
    
    def __init__(self, widget, property_obj: BindableProperty, config: Dict, initial_sync: bool):
        super().__init__(widget, property_obj, config, initial_sync)
        
        # View → Model の監視（複数のイベントに対応）
        change_events = config.get('change_event', '<ButtonRelease-1>')
        if isinstance(change_events, str):
            change_events = [change_events]
        
        for event in change_events:
            widget.bind(event, self._on_view_changed)
        
        # Scaleの場合は追加でcommandも設定
        if hasattr(widget, 'configure') and 'Scale' in str(type(widget)):
            widget.configure(command=self._on_scale_changed)
    
    def _sync_view_to_model(self) -> None:
        """Model → View 同期"""
        set_method = self.config.get('set_method', 'set')
        if hasattr(self.widget, set_method):
            getattr(self.widget, set_method)(self.property_obj.value)
    
    def _sync_model_to_view(self) -> None:
        """View → Model 同期"""
        get_method = self.config.get('get_method', 'get')
        if hasattr(self.widget, get_method):
            value = getattr(self.widget, get_method)()
            self.property_obj.value = value
    
    def _on_view_changed(self, event=None) -> None:
        """View値変更時のコールバック"""
        if not self._updating:
            self._updating = True
            try:
                self._sync_model_to_view()
            finally:
                self._updating = False
    
    def _on_scale_changed(self, value) -> None:
        """Scaleのcommandコールバック"""
        if not self._updating:
            self._updating = True
            try:
                self._sync_model_to_view()
            finally:
                self._updating = False


class DataModel:
    """データモデル基底クラス - WPF ViewModel風"""
    
    def __init__(self):
        self._properties: Dict[str, BindableProperty] = {}
    
    def add_property(self, name: str, initial_value: Any, property_type: type = None) -> BindableProperty:
        """バインド可能プロパティの追加"""
        prop = BindableProperty(initial_value, property_type)
        self._properties[name] = prop
        return prop
    
    def get_property(self, name: str) -> Optional[BindableProperty]:
        """プロパティ取得"""
        return self._properties.get(name)
    
    def set_value(self, name: str, value: Any) -> None:
        """プロパティ値設定"""
        if name in self._properties:
            self._properties[name].value = value
    
    def get_value(self, name: str) -> Any:
        """プロパティ値取得"""
        return self._properties[name].value if name in self._properties else None


class BidirectionalBinder:
    """双方向バインダー - メインクラス"""
    
    def __init__(self):
        self.bindings: List[TkinterBinding] = []
    
    def bind_widget(self, widget, model: DataModel, property_name: str, 
                   initial_sync: bool = True) -> 'BidirectionalBinder':
        """ウィジェットとモデルプロパティをバインド"""
        property_obj = model.get_property(property_name)
        if property_obj is None:
            raise ValueError(f"Property '{property_name}' not found in model")
        
        binding = TkinterWidgetAdapter.create_binding(widget, property_obj, initial_sync)
        self.bindings.append(binding)
        
        return self
    
    def bind_property_to_property(self, source_model: DataModel, source_prop: str,
                                 target_model: DataModel, target_prop: str) -> 'BidirectionalBinder':
        """プロパティ間の双方向バインド"""
        source_property = source_model.get_property(source_prop)
        target_property = target_model.get_property(target_prop)
        
        if not source_property or not target_property:
            raise ValueError("Source or target property not found")
        
        # 双方向リンク設定
        source_property.subscribe(lambda val: setattr(target_property, 'value', val))
        target_property.subscribe(lambda val: setattr(source_property, 'value', val))
        
        return self
    
    def destroy_all(self) -> None:
        """全バインディング解除"""
        for binding in self.bindings:
            binding.destroy()
        self.bindings.clear()


# =============================================================================
# EasyNovelAssistant 専用拡張
# =============================================================================

class ENASettingsModel(DataModel):
    """EasyNovelAssistant 設定モデル"""
    
    def __init__(self):
        super().__init__()
        
        # 反復抑制v3設定
        self.similarity_threshold = self.add_property('similarity_threshold', 0.35, float)
        self.max_distance = self.add_property('max_distance', 50, int)
        self.min_compress_rate = self.add_property('min_compress_rate', 0.03, float)
        self.ngram_block_size = self.add_property('ngram_block_size', 3, int)
        self.drp_base = self.add_property('drp_base', 1.10, float)
        self.drp_alpha = self.add_property('drp_alpha', 0.5, float)
        
        # トグル設定
        self.enable_4gram = self.add_property('enable_4gram', True, bool)
        self.enable_drp = self.add_property('enable_drp', True, bool)
        self.enable_mecab = self.add_property('enable_mecab', False, bool)
        self.enable_rhetorical = self.add_property('enable_rhetorical', False, bool)
        self.enable_latin_number = self.add_property('enable_latin_number', True, bool)
        self.aggressive_mode = self.add_property('aggressive_mode', True, bool)
        
        # 統計情報
        self.success_rate = self.add_property('success_rate', 0.0, float)
        self.session_attempts = self.add_property('session_attempts', 0, int)
        self.last_compression_rate = self.add_property('last_compression_rate', 0.0, float)
    
    def load_from_dict(self, settings_dict: Dict) -> None:
        """辞書から設定を読み込み"""
        for key, value in settings_dict.items():
            if key in self._properties:
                self.set_value(key, value)
    
    def to_dict(self) -> Dict:
        """設定を辞書に変換"""
        return {name: prop.value for name, prop in self._properties.items()}
    
    def apply_to_suppressor(self, suppressor) -> None:
        """反復抑制システムに設定を適用"""
        if hasattr(suppressor, 'update_config'):
            suppressor.update_config(self.to_dict())


def create_ena_bidirectional_system() -> tuple[ENASettingsModel, BidirectionalBinder]:
    """EasyNovelAssistant用双方向バインディングシステム作成"""
    model = ENASettingsModel()
    binder = BidirectionalBinder()
    return model, binder


# 使用例コード（コメント）
"""
# 使用例:
model, binder = create_ena_bidirectional_system()

# ウィジェットとバインド
binder.bind_widget(similarity_scale, model, 'similarity_threshold')
binder.bind_widget(distance_scale, model, 'max_distance')
binder.bind_widget(enable_drp_checkbox, model, 'enable_drp')

# コード側からの設定変更が自動的にGUIに反映される
model.set_value('similarity_threshold', 0.42)  # スライダーが自動更新！

# 設定変更監視
model.similarity_threshold.subscribe(lambda val: print(f"閾値変更: {val}"))
""" 