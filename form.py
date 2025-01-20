import tkinter as tk
import tkinter.ttk as ttk
from tkinterdnd2 import DND_FILES, TkinterDnD

from const import Const
from gen_area import GenArea
from input_area import InputArea
from menu.file_menu import FileMenu
from menu.gen_menu import GenMenu
from menu.help_menu import HelpMenu
from menu.model_menu import ModelMenu
from menu.sample_menu import SampleMenu
from menu.setting_menu import SettingMenu
from menu.speech_menu import SpeechMenu
from menu.tool_menu import ToolMenu
from menu.chat_menu import ChatMenu
from output_area import OutputArea


class Form:
    WIN_MIN_W = 640
    WIN_MIN_H = 480

    def __init__(self, ctx):
        self.ctx = ctx

        self.win = TkinterDnD.Tk()
        self.win.drop_target_register(DND_FILES)
        self.win.title("EasyNovelAssistant")
        self.win.minsize(self.WIN_MIN_W, self.WIN_MIN_H)
        win_geom = f'{self.ctx["win_width"]}x{self.ctx["win_height"]}'
        if self.ctx["win_x"] != 0 or self.ctx["win_y"] != 0:
            win_geom += f'+{ctx["win_x"]}+{self.ctx["win_y"]}'
        self.win.geometry(win_geom)
        self.win.protocol("WM_DELETE_WINDOW", self.ctx.finalize)
        self.win.dnd_bind("<<Drop>>", lambda e: self.file_menu.dnd_file(e))

        self.menu_bar = tk.Menu(self.win)
        self.win.config(menu=self.menu_bar)

        self.file_menu = FileMenu(self, ctx)
        self.model_menu = ModelMenu(self, ctx)
        self.gen_menu = GenMenu(self, ctx)
        self.speech_menu = SpeechMenu(self, ctx)
        self.setting_menu = SettingMenu(self, ctx)
        self.sample_menu = SampleMenu(self, ctx)
        self.tool_menu = ToolMenu(self, ctx)
        self.help_menu = HelpMenu(self, ctx)
        self.chat_menu = ChatMenu(self, ctx)

        self.pane_h = tk.PanedWindow(self.win, orient=tk.HORIZONTAL, sashpad=2)

        self.input_area = InputArea(self.pane_h, ctx)

        self.pane_v = tk.PanedWindow(self.pane_h, orient=tk.VERTICAL, sashpad=2)
        self.pane_h.add(self.pane_v, width=ctx["pane_v_width"], minsize=Const.AREA_MIN_SIZE, stretch="always")

        self.output_area = OutputArea(self.pane_v, ctx)
        self.gen_area = GenArea(self.pane_v, ctx)

        self.pane_h.pack(fill=tk.BOTH, expand=True)

        # チャットモード関連の初期化
        self.ctx.setdefault("chat_mode", False)
        self.ctx.setdefault("chat_memory_count", 5)
        self.ctx.setdefault("char_settings", "")

        if self.ctx.get("chat_mode", False):
            from chat_mode import ChatMode
            if not hasattr(self.ctx, 'chat_mode'):
                self.ctx.chat_mode = ChatMode(self.ctx)

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

    def switch_to_chat_mode(self):
        """チャットモードに切り替え"""
        # ChatModeインスタンスの確認と生成
        if not hasattr(self.ctx, 'chat_mode'):
            from chat_mode import ChatMode
            self.ctx.chat_mode = ChatMode(self.ctx)
        
        # 入力エリアのスタイル変更
        self.input_area.set_chat_style()
        # 生成エリアのクリア
        self.gen_area.clear()
        # 出力エリアのクリア
        self.output_area.clear()
        # タイトル更新
        self.win.title(f"EasyNovelAssistant - Chat with {self.ctx['char_name']}")
        
    def switch_to_novel_mode(self):
        """ノベルモードに切り替え"""
        # 入力エリアのスタイル戻し
        self.input_area.set_novel_style()
        # 生成エリアのクリア
        self.gen_area.clear()
        # 出力エリアのクリア
        self.output_area.clear()
        # タイトル更新
        self.update_title()

    def process_chat_input(self, text):
        """チャット入力の処理"""
        if not text.strip():
            return
        
        # ChatModeインスタンスの確認と生成
        if not hasattr(self.ctx, 'chat_mode'):
            from chat_mode import ChatMode
            self.ctx.chat_mode = ChatMode(self.ctx)
        
        # ユーザーの入力を履歴に追加
        self.ctx.chat_mode.add_message('user', text)
        
        # 入力欄をクリア
        self.input_area.clear_current()
        
        # 会話履歴を更新
        chat_history = self.ctx.chat_mode.get_formatted_history()
        self.output_area.set_text(chat_history)
        
        # 生成用のプロンプトを作成
        prompt = self.ctx.chat_mode.format_chat_prompt(text)
        
        # 生成を開始
        if not self.ctx.generator.enabled:
            self.gen_menu._enable()
        
        # プロンプトを設定
        self.ctx.generator.set_prompt(prompt)