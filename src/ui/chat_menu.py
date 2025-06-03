import tkinter as tk
from tkinter import ttk, messagebox


class ChatMenu:
    def __init__(self, form, ctx):
        self.form = form
        self.ctx = ctx
        self.menu = tk.Menu(form.win, tearoff=False)
        self.form.menu_bar.add_cascade(label="チャット", menu=self.menu)
        self.menu.configure(postcommand=self.on_menu_open)

    def on_menu_open(self):
        self.menu.delete(0, tk.END)
        
        def toggle_chat_mode(*args):
            self.ctx["chat_mode"] = self.chat_mode_var.get()
            if self.ctx["chat_mode"]:
                # ChatModeインスタンスがない場合は作成
                if not hasattr(self.ctx, 'chat_mode'):
                    from chat_mode import ChatMode
                    self.ctx.chat_mode = ChatMode(self.ctx)
                self.form.switch_to_chat_mode()
            else:
                self.form.switch_to_novel_mode()

        self.chat_mode_var = tk.BooleanVar(value=self.ctx.get("chat_mode", False))
        self.chat_mode_var.trace_add("write", toggle_chat_mode)
        self.menu.add_checkbutton(label="チャットモード", variable=self.chat_mode_var)

        # セパレータ
        self.menu.add_separator()

        # メモリ設定
        memory_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label="会話履歴の記憶数", menu=memory_menu)

        def set_chat_memory(count):
            self.ctx["chat_memory_count"] = count

        memory_counts = [3, 5, 10, 15, 20]
        current_memory = self.ctx.get("chat_memory_count", 5)

        for count in memory_counts:
            check_var = tk.BooleanVar(value=current_memory == count)
            memory_menu.add_checkbutton(
                label=f"直近{count}件",
                variable=check_var,
                command=lambda c=count, _=check_var: set_chat_memory(c)
            )

        # キャラクター設定
        self.menu.add_command(label="キャラクター設定...", command=self.edit_character_settings)

        # 履歴のクリア
        self.menu.add_command(label="会話履歴をクリア", command=self.clear_chat_history)

    def edit_character_settings(self):
        dialog = CharacterSettingsDialog(self.form.win, self.ctx)
        dialog.grab_set()  # モーダルダイアログにする
        self.form.win.wait_window(dialog)

    def clear_chat_history(self):
        if messagebox.askyesno("確認", "会話履歴をクリアしますか？"):
            if hasattr(self.ctx, 'chat_mode'):
                self.ctx.chat_mode.history = []
                self.form.output_area.clear()


class CharacterSettingsDialog(tk.Toplevel):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self.title("キャラクター設定")
        self.geometry("500x600")

        # メインフレーム
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # キャラクター名設定
        name_frame = ttk.LabelFrame(main_frame, text="キャラクター名", padding=5)
        name_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.char_name = ttk.Entry(name_frame)
        self.char_name.insert(0, ctx.get("char_name", "アシスタント"))
        self.char_name.pack(fill=tk.X, padx=5, pady=5)

        # ユーザー名設定
        user_frame = ttk.LabelFrame(main_frame, text="ユーザー名", padding=5)
        user_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.user_name = ttk.Entry(user_frame)
        self.user_name.insert(0, ctx.get("user_name", "ユーザー"))
        self.user_name.pack(fill=tk.X, padx=5, pady=5)

        # キャラクター設定
        settings_frame = ttk.LabelFrame(main_frame, text="キャラクター設定", padding=5)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.settings_text = tk.Text(settings_frame, height=15)
        self.settings_text.insert("1.0", ctx.get("char_settings", self._get_default_settings()))
        self.settings_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ボタンフレーム
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="保存", command=self.save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="キャンセル", command=self.destroy).pack(side=tk.RIGHT)

    def _get_default_settings(self):
        return """キャラクター設定の例:

• 性格: フレンドリーで親切
• 話し方: 丁寧だが親しみやすい
• 感情表現: 適度に感情を示す
• 専門知識: 幅広い分野の知識を持つ
• 応答スタイル: 簡潔かつ的確
"""

    def save_settings(self):
        self.ctx["char_name"] = self.char_name.get()
        self.ctx["user_name"] = self.user_name.get()
        self.ctx["char_settings"] = self.settings_text.get("1.0", tk.END).strip()
        self.destroy()