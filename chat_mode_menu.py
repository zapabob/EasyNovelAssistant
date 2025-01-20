import tkinter as tk
from tkinter import ttk

class ChatMenu:
    def __init__(self, form, ctx):
        self.form = form
        self.ctx = ctx
        self.menu = tk.Menu(form.win, tearoff=False)
        self.form.menu_bar.add_cascade(label="モード", menu=self.menu)
        self.menu.configure(postcommand=self.on_menu_open)

    def on_menu_open(self):
        self.menu.delete(0, tk.END)
        
        # モード切り替えメニュー
        def toggle_chat_mode(*args):
            self.ctx["chat_mode"] = self.chat_mode_var.get()
            if self.ctx["chat_mode"]:
                self.form.switch_to_chat_mode()
            else:
                self.form.switch_to_novel_mode()

        self.chat_mode_var = tk.BooleanVar(value=self.ctx.get("chat_mode", False))
        self.chat_mode_var.trace_add("write", toggle_chat_mode)
        self.menu.add_checkbutton(label="チャットモード", variable=self.chat_mode_var)

        # チャットモード時の設定
        if self.ctx.get("chat_mode", False):
            self.menu.add_separator()
            
            # メモリ設定
            memory_menu = tk.Menu(self.menu, tearoff=False)
            self.menu.add_cascade(label="会話履歴の記憶数", menu=memory_menu)
            
            def set_chat_memory(count):
                self.ctx["chat_memory_count"] = count
            
            memory_counts = [3, 5, 10, 15, 20]
            current_memory = self.ctx.get("chat_memory_count", 5)
            
            for count in memory_counts:
                memory_menu.add_radiobutton(
                    label=f"直近{count}件",
                    value=count,
                    variable=tk.IntVar(value=current_memory),
                    command=lambda c=count: set_chat_memory(c)
                )

            # システムメッセージの編集
            self.menu.add_command(
                label="キャラクター設定の編集...",
                command=self.edit_character_settings
            )

    def edit_character_settings(self):
        dialog = CharacterSettingsDialog(self.form.win, self.ctx)
        self.form.win.wait_window(dialog)

class CharacterSettingsDialog(tk.Toplevel):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self.title("キャラクター設定")
        
        # 設定入力エリア
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="キャラクター名:").pack(anchor=tk.W)
        self.char_name = ttk.Entry(frame, width=40)
        self.char_name.insert(0, ctx["char_name"])
        self.char_name.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="ユーザー名:").pack(anchor=tk.W)
        self.user_name = ttk.Entry(frame, width=40)
        self.user_name.insert(0, ctx["user_name"])
        self.user_name.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="キャラクター設定:").pack(anchor=tk.W)
        self.char_settings = tk.Text(frame, height=10, width=50)
        self.char_settings.insert("1.0", ctx.get("char_settings", ""))
        self.char_settings.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # ボタン
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="保存", command=self.save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="キャンセル", command=self.destroy).pack(side=tk.RIGHT)
        
        self.grab_set()
    
    def save_settings(self):
        self.ctx["char_name"] = self.char_name.get()
        self.ctx["user_name"] = self.user_name.get()
        self.ctx["char_settings"] = self.char_settings.get("1.0", tk.END).strip()
        self.destroy()