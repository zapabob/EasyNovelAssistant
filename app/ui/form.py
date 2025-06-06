﻿import tkinter as tk

from ..core.const import Const
from .gen_area import GenArea
from .input_area import InputArea
# Menu modules
from .menu.file_menu import FileMenu
# Note: Other menu modules will be added later
# from .menu.gen_menu import GenMenu
# from .menu.help_menu import HelpMenu
# from .menu.model_menu import ModelMenu
# from .menu.sample_menu import SampleMenu
# from .menu.setting_menu import SettingMenu
# from .menu.speech_menu import SpeechMenu
# from .menu.tool_menu import ToolMenu
from .output_area import OutputArea
from tkinterdnd2 import DND_FILES, TkinterDnD

# 統合システムv3制御パネル
try:
    from .integration_control_panel import IntegrationControlPanel
    INTEGRATION_PANEL_AVAILABLE = True
except ImportError:
    INTEGRATION_PANEL_AVAILABLE = False
    print("⚠️ 統合システム制御パネル読み込み失敗")


class Form:
    WIN_MIN_W = 640
    WIN_MIN_H = 480

    def __init__(self, ctx):
        self.ctx = ctx

        self.win = TkinterDnD.Tk()
        self.win.drop_target_register(DND_FILES)
        self.win.title("EasyNovelAssistant")
        self.win.minsize(self.WIN_MIN_W, self.WIN_MIN_H)
        
        # デフォルト値の設定
        win_width = self.ctx.get("win_width", 800)
        win_height = self.ctx.get("win_height", 600)
        win_x = self.ctx.get("win_x", 0)
        win_y = self.ctx.get("win_y", 0)
        
        win_geom = f'{win_width}x{win_height}'
        if win_x != 0 or win_y != 0:
            win_geom += f'+{win_x}+{win_y}'
        self.win.geometry(win_geom)
        self.win.protocol("WM_DELETE_WINDOW", self.ctx.finalize)
        self.win.dnd_bind("<<Drop>>", lambda e: self.file_menu.dnd_file(e))

        self.menu_bar = tk.Menu(self.win)
        self.win.config(menu=self.menu_bar)

        # Menu initialization
        self.file_menu = FileMenu(self, ctx)
        # Note: Other menu modules will be added later
        # self.model_menu = ModelMenu(self, ctx)
        # self.gen_menu = GenMenu(self, ctx)
        # self.speech_menu = SpeechMenu(self, ctx)
        # self.setting_menu = SettingMenu(self, ctx)
        # self.sample_menu = SampleMenu(self, ctx)
        # self.tool_menu = ToolMenu(self, ctx)
        # self.help_menu = HelpMenu(self, ctx)

        self.pane_h = tk.PanedWindow(self.win, orient=tk.HORIZONTAL, sashpad=2)

        self.input_area = InputArea(self.pane_h, ctx)

        self.pane_v = tk.PanedWindow(self.pane_h, orient=tk.VERTICAL, sashpad=2)
        pane_v_width = ctx.get("pane_v_width", 400)
        self.pane_h.add(self.pane_v, width=pane_v_width, minsize=Const.AREA_MIN_SIZE, stretch="always")

        self.output_area = OutputArea(self.pane_v, ctx)
        self.gen_area = GenArea(self.pane_v, ctx)

        # 統合システムv3制御パネルの追加
        if INTEGRATION_PANEL_AVAILABLE:
            self.integration_panel = IntegrationControlPanel(
                self.input_area.notebook,
                ctx,
                on_settings_changed=self._on_integration_settings_changed
            )
            # 新しいタブとして追加
            self.input_area.notebook.add(
                self.integration_panel.get_widget(),
                text="🚀 統合システムv3"
            )
            print("✅ 統合システムv3制御パネル追加完了")
        else:
            self.integration_panel = None

        self.pane_h.pack(fill=tk.BOTH, expand=True)

    def _on_integration_settings_changed(self, settings):
        """統合システムv3設定変更時のコールバック"""
        if hasattr(self.ctx, 'integration_config'):
            # 設定をコンテキストに反映
            self.ctx.integration_config.update(settings)
            
            # 統合システムに設定を適用
            if hasattr(self.ctx, 'repetition_suppressor') and self.ctx.repetition_suppressor:
                # 反復抑制v3に設定適用
                rep_config = settings.get('repetition_suppression', {})
                if rep_config.get('enabled', True):
                    self.ctx.repetition_suppressor.config.update({
                        'similarity_threshold': rep_config.get('similarity_threshold', 0.35),
                        'enable_aggressive_mode': rep_config.get('aggressive_mode', True)
                    })
            
            if hasattr(self.ctx, 'lora_coordinator') and self.ctx.lora_coordinator:
                # LoRA協調システムに設定適用
                lora_config = settings.get('lora_coordination', {})
                if lora_config.get('enabled', True):
                    # LoRA設定更新（実装依存）
                    pass
            
            print(f"🔄 統合システムv3設定更新: {len(settings)} 項目")

    def run(self):
        self.win.lift()
        self.win.mainloop()

    def update_title(self):
        title = "EasyNovelAssistant"
        if self.ctx.kobold_cpp.model_name is not None:
            title += f" - {self.ctx.kobold_cpp.model_name}"
        if self.ctx.generator.enabled:
            title += " [生成中]"
        file_path = self.ctx.form.input_area.get_file_path()
        if file_path is not None:
            title += f" - {file_path}"
        if (not self.ctx.generator.enabled) and (file_path is None):
            title += " - [生成] メニューの [生成を開始 (F3)] で生成を開始します。"
        self.win.title(title)

    def update_config(self):
        ctx = self.ctx
        ctx["win_width"] = self.win.winfo_width()
        ctx["win_height"] = self.win.winfo_height()
        ctx["win_x"] = self.win.winfo_x()
        ctx["win_y"] = self.win.winfo_y()

        input_area_width = self.input_area.notebook.winfo_width()
        if input_area_width != -1:
            ctx["input_area_width"] = input_area_width

        pane_v_width = self.pane_v.winfo_width()
        if pane_v_width != -1:
            ctx["pane_v_width"] = pane_v_width

        gen_area_height = self.gen_area.text_area.winfo_height()
        if gen_area_height != -1:
            ctx["gen_area_height"] = gen_area_height

        ctx["input_text"] = self.input_area.get_text()
