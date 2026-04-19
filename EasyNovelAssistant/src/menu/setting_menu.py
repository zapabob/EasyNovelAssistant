import tkinter as tk
import tkinter.font as font
from tkinter import simpledialog


class SettingMenu:

    def __init__(self, form, ctx):
        self.form = form
        self.ctx = ctx

        self.menu = tk.Menu(form.win, tearoff=False)
        self.form.menu_bar.add_cascade(label="設定", menu=self.menu)
        self.menu.configure(postcommand=self._on_menu_open)

    def _on_menu_open(self):
        self.menu.delete(0, tk.END)

        cmd = lambda: self._set_name("char_name", "キャラ名")
        self.menu.add_command(label=f'キャラ名: {self.ctx["char_name"]}', command=cmd)

        cmd = lambda: self._set_name("user_name", "ユーザー名")
        self.menu.add_command(label=f'ユーザー名: {self.ctx["user_name"]}', command=cmd)

        self.menu.add_separator()

        self.backend_var = tk.StringVar(value=self.ctx.kobold_cpp.backend)
        backend_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(
            label=f"LLMバックエンド: {self.ctx.kobold_cpp.display_backend_name()}",
            menu=backend_menu,
        )
        backend_menu.add_radiobutton(
            label="KoboldCpp",
            variable=self.backend_var,
            value="koboldcpp",
            command=lambda: self._set_backend("koboldcpp"),
        )
        backend_menu.add_radiobutton(
            label="Hypura",
            variable=self.backend_var,
            value="hypura",
            command=lambda: self._set_backend("hypura"),
        )

        hypura_path = self.ctx["hypura_path"] or "(PATH を使用)"
        self.menu.add_command(
            label=f"Hypura 実行ファイル: {hypura_path}",
            command=self._set_hypura_path,
        )

        self.menu.add_separator()

        def _set_font(f):
            self.ctx["text_area_font"] = f
            self.form.input_area.apply_text_setting()
            self.form.gen_area.apply_text_setting()
            self.form.output_area.apply_text_setting()

        font_menu = tk.Menu(self.menu, tearoff=False)

        self.menu.add_cascade(label=f'フォント（↑↓キー利用可）: {self.ctx["text_area_font"]}', menu=font_menu)
        for font_family in font.families():
            check_var = tk.BooleanVar(value=self.ctx["text_area_font"] == font_family)

            font_menu.add_checkbutton(
                label=font_family, variable=check_var, command=lambda f=font_family, _=check_var: _set_font(f)
            )

        def _set_font_size(fons_size):
            self.ctx["text_area_font_size"] = fons_size
            self.form.input_area.apply_text_setting()
            self.form.gen_area.apply_text_setting()
            self.form.output_area.apply_text_setting()

        font_size_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label=f'フォントサイズ: {self.ctx["text_area_font_size"]}', menu=font_size_menu)

        font_sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
        for font_size in font_sizes:
            check_var = tk.BooleanVar(value=self.ctx["text_area_font_size"] == font_size)

            font_size_menu.add_checkbutton(
                label=font_size, variable=check_var, command=lambda fs=font_size, _=check_var: _set_font_size(fs)
            )

        self.menu.add_separator()

        def _set_invert_color():
            fg = self.ctx["foreground_color"]
            self.ctx["foreground_color"] = self.ctx["select_background_color"]
            self.ctx["select_background_color"] = fg
            sel_fg = self.ctx["select_foreground_color"]
            self.ctx["select_foreground_color"] = self.ctx["background_color"]
            self.ctx["background_color"] = sel_fg
            self.form.input_area.apply_text_setting()
            self.form.gen_area.apply_text_setting()
            self.form.output_area.apply_text_setting()

        self.menu.add_command(label="テーマカラーの反転", command=_set_invert_color)

    def _set_name(self, who, who_label):
        name = self.ctx[who]

        name = simpledialog.askstring(
            f"{who_label}設定",
            f"サンプルなどで使用する{who_label}を入力してください。",
            initialvalue=name,
            parent=self.form.win,
        )
        if name is None:
            return
        elif name != "":
            self.ctx[who] = name

    def _set_backend(self, backend):
        self.ctx.kobold_cpp.set_backend(backend)
        self.form.update_title()

    def _set_hypura_path(self):
        current = self.ctx["hypura_path"] or ""
        hypura_path = simpledialog.askstring(
            "Hypura 実行ファイル設定",
            "Hypura 実行ファイルのパスを入力してください。\n空欄にすると PATH 上の hypura を探します。",
            initialvalue=current,
            parent=self.form.win,
        )
        if hypura_path is None:
            return

        self.ctx["hypura_path"] = hypura_path.strip()
        self.form.update_title()
