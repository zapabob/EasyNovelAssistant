import tkinter as tk
from tkinter import simpledialog

from image_manager import HUGGING_FACE, IMAGE_PROVIDER_LABELS, STABLE_DIFFUSION_WEBUI, normalize_image_provider


class ImageMenu:
    def __init__(self, form, ctx):
        self.form = form
        self.ctx = ctx

        self.menu = tk.Menu(form.win, tearoff=False)
        self.form.menu_bar.add_cascade(label="画像生成", menu=self.menu)
        self.menu.configure(postcommand=self._on_menu_open)

    def _on_menu_open(self):
        self.menu.delete(0, tk.END)

        self.menu.add_command(label="入力欄から画像生成", command=self._generate_from_input)
        self.menu.add_command(label="直近の生成文から画像生成", command=self._generate_from_recent)
        self.menu.add_command(label="保留中の文章で画像生成", command=self.ctx.image.flush)
        self.menu.add_command(label="画像生成を中断", command=self.ctx.image.abort)

        self.menu.add_separator()

        def set_auto_image_generation(*args):
            self.ctx["auto_image_generation"] = self.auto_image_generation_var.get()

        self.auto_image_generation_var = tk.BooleanVar(value=self.ctx["auto_image_generation"])
        self.auto_image_generation_var.trace_add("write", set_auto_image_generation)
        self.menu.add_checkbutton(label="自動画像生成", variable=self.auto_image_generation_var)

        self._add_provider_menu()

        self.menu.add_separator()

        self.menu.add_command(
            label=f'画像生成サーバーURL: {self.ctx["image_generation_base_url"]}',
            command=lambda: self._set_string("image_generation_base_url", "画像生成サーバーURL"),
        )
        self.menu.add_command(
            label=f'Hugging Faceモデル: {self.ctx["huggingface_image_model"]}',
            command=lambda: self._set_string("huggingface_image_model", "Hugging Faceモデル"),
        )
        self.menu.add_command(
            label="Hugging FaceエンドポイントURL",
            command=lambda: self._set_string("huggingface_image_endpoint_url", "Hugging FaceエンドポイントURL"),
        )
        self.menu.add_command(
            label=f'Hugging Faceトークン環境変数: {self.ctx["huggingface_image_token_env"]}',
            command=lambda: self._set_string("huggingface_image_token_env", "Hugging Faceトークン環境変数"),
        )

        self.menu.add_separator()

        self.menu.add_command(
            label="画像プロンプトテンプレート",
            command=lambda: self._set_string("image_generation_prompt_template", "画像プロンプトテンプレート"),
        )
        self.menu.add_command(
            label="ネガティブプロンプト",
            command=lambda: self._set_string("image_generation_negative_prompt", "ネガティブプロンプト"),
        )

        self._add_number_menu("幅", "image_generation_width", [512, 768, 896, 1024, 1152, 1280])
        self._add_number_menu("高さ", "image_generation_height", [512, 768, 896, 1024, 1152, 1280])
        self._add_number_menu("ステップ数", "image_generation_steps", [10, 15, 20, 25, 30, 40])
        self._add_float_menu("CFG Scale", "image_generation_cfg_scale", [4.0, 5.0, 6.0, 7.0, 8.0, 10.0])

        self.menu.add_command(
            label=f'サンプラー: {self.ctx["image_generation_sampler"] or "(未指定)"}',
            command=lambda: self._set_string("image_generation_sampler", "サンプラー"),
        )
        self.menu.add_command(
            label=f'シード: {self.ctx["image_generation_seed"]}',
            command=lambda: self._set_int("image_generation_seed", "シード"),
        )

        self.menu.add_separator()

        self._add_number_menu("自動生成する行数", "auto_image_generation_lines", [1, 2, 3, 4, 6, 8, 10])
        self._add_number_menu("自動生成する最小文字数", "auto_image_generation_min_chars", [80, 160, 240, 400, 600])
        self._add_number_menu("画像用の直近文字数", "image_generation_context_chars", [300, 500, 800, 1000, 1500, 2000])
        self._add_number_menu("最大画像生成キュー", "max_image_generation_queue", [1, 2, 3, 4])
        self._add_number_menu("画像生成タイムアウト秒", "image_generation_timeout", [30, 60, 120, 180, 300])

    def _add_provider_menu(self):
        provider = normalize_image_provider(self.ctx["image_generation_provider"])
        self.ctx["image_generation_provider"] = provider

        self.provider_var = tk.StringVar(value=provider)
        provider_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label=f"画像生成プロバイダー: {IMAGE_PROVIDER_LABELS[provider]}", menu=provider_menu)

        provider_menu.add_radiobutton(
            label=IMAGE_PROVIDER_LABELS[STABLE_DIFFUSION_WEBUI],
            variable=self.provider_var,
            value=STABLE_DIFFUSION_WEBUI,
            command=lambda: self._set_provider(STABLE_DIFFUSION_WEBUI),
        )
        provider_menu.add_radiobutton(
            label=IMAGE_PROVIDER_LABELS[HUGGING_FACE],
            variable=self.provider_var,
            value=HUGGING_FACE,
            command=lambda: self._set_provider(HUGGING_FACE),
        )

    def _add_number_menu(self, label, key, values):
        number_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label=f"{label}: {self.ctx[key]}", menu=number_menu)
        for value in values:
            check_var = tk.BooleanVar(value=self.ctx[key] == value)
            number_menu.add_checkbutton(
                label=value,
                variable=check_var,
                command=lambda v=value, _=check_var: self._set_value(key, v),
            )
        number_menu.add_separator()
        number_menu.add_command(label="数値を入力", command=lambda: self._set_int(key, label))

    def _add_float_menu(self, label, key, values):
        float_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label=f"{label}: {self.ctx[key]}", menu=float_menu)
        for value in values:
            check_var = tk.BooleanVar(value=self.ctx[key] == value)
            float_menu.add_checkbutton(
                label=value,
                variable=check_var,
                command=lambda v=value, _=check_var: self._set_value(key, v),
            )
        float_menu.add_separator()
        float_menu.add_command(label="数値を入力", command=lambda: self._set_float(key, label))

    def _generate_from_input(self):
        self.ctx.image.generate(self.ctx.form.input_area.get_comment_removed_text(), force=True)

    def _generate_from_recent(self):
        text = self.ctx.generator.gen_area_text or self.ctx.form.input_area.get_comment_removed_text()
        self.ctx.image.generate(text, force=True)

    def _set_provider(self, provider):
        self.ctx["image_generation_provider"] = normalize_image_provider(provider)

    def _set_value(self, key, value):
        self.ctx[key] = value

    def _set_string(self, key, title):
        current = self.ctx[key] or ""
        value = simpledialog.askstring(
            title,
            f"{title}を入力してください。",
            initialvalue=current,
            parent=self.form.win,
        )
        if value is None:
            return
        self.ctx[key] = value.strip()

    def _set_int(self, key, title):
        value = simpledialog.askinteger(
            title,
            f"{title}を入力してください。",
            initialvalue=self.ctx[key],
            parent=self.form.win,
        )
        if value is not None:
            self.ctx[key] = value

    def _set_float(self, key, title):
        value = simpledialog.askfloat(
            title,
            f"{title}を入力してください。",
            initialvalue=self.ctx[key],
            parent=self.form.win,
        )
        if value is not None:
            self.ctx[key] = value
