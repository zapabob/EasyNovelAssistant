import tkinter as tk
from tkinter import simpledialog, messagebox
from components.model_add_dialog import ModelAddDialog
from utils.path import Path
import os


class ModelMenu:
    SEPALATER_NAMES = [
        "LightChatAssistant-4x7B-IQ4_XS",
    ]

    def __init__(self, form, ctx):
        self.form = form
        self.ctx = ctx

        self.menu = tk.Menu(form.win, tearoff=False)
        form.menu_bar.add_cascade(label="モデル", menu=self.menu)
        self.menu.configure(postcommand=self.on_menu_open)

    def on_menu_open(self):
        self.menu.delete(0, tk.END)
        
        # モデル追加メニュー項目を最上部に配置
        self.menu.add_command(label="GGUFモデルを追加", command=self.add_model)
        self.menu.add_separator()

        # コンテキストサイズメニュー
        self._add_context_size_menu()
        self.menu.add_separator()

        # モデル一覧メニュー
        self._add_models_menu()

    def _add_context_size_menu(self):
        def context_label(context_size):
            llm_name = self.ctx.get("llm_name")
            if llm_name and llm_name in self.ctx.llm:
                llm = self.ctx.llm[llm_name]
                if isinstance(llm, dict) and "context_size" in llm:
                    model_ctx_size = llm["context_size"]
                    if context_size > model_ctx_size:
                        return f"C{model_ctx_size // 1024}K: {context_size} > {model_ctx_size}({llm_name})"
            return f"C{context_size // 1024}K: {context_size}"

        context_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(
            label=f'コンテキストサイズ上限（増やすと VRAM 消費増）: {context_label(self.ctx.get("llm_context_size", 4096))})',
            menu=context_menu
        )

        def set_context_size(size):
            self.ctx["llm_context_size"] = size

        sizes = [2048, 4096, 8192, 16384, 32768, 65536, 131072]
        current_size = self.ctx.get("llm_context_size", 4096)
        for size in sizes:
            check_var = tk.BooleanVar(value=current_size == size)
            context_menu.add_checkbutton(
                label=context_label(size),
                variable=check_var,
                command=lambda s=size: set_context_size(s)
            )

    def _add_models_menu(self):
        categories = {}

        for llm_name in self.ctx.llm:
            llm = self.ctx.llm[llm_name]
            if not isinstance(llm, dict):
                continue
            
            if "context_size" not in llm:
                continue
            
            model_menu = tk.Menu(self.menu, tearoff=False)
            
            name = llm_name
            context_size = min(
                llm["context_size"], 
                self.ctx.get("llm_context_size", 4096)
            ) // 1024

            # カテゴリ分け
            if "/" in llm_name:
                category, name = llm_name.split("/")
                if category not in categories:
                    categories[category] = tk.Menu(self.menu, tearoff=False)
                    self.menu.add_cascade(label=category, menu=categories[category])
                categories[category].add_cascade(
                    label=f"{name} C{context_size}K", 
                    menu=model_menu
                )
            else:
                self.menu.add_cascade(
                    label=f"{llm_name} C{context_size}K", 
                    menu=model_menu
                )

            # セパレータの追加
            for sep_name in self.SEPALATER_NAMES:
                if sep_name in name:
                    self.menu.add_separator()

            # モデルファイルの存在確認とメニュー項目の追加
            llm_path = os.path.join(Path.kobold_cpp, llm["file_name"])
            if not os.path.exists(llm_path):
                model_menu.add_command(
                    label="ダウンロード",
                    command=lambda n=llm_name: self._download_model(n)
                )
                continue

            # GPUレイヤー設定
            max_gpu_layer = llm["max_gpu_layer"]
            for gpu_layer in self.ctx.get("llm_gpu_layers", [0, 33]):
                if gpu_layer > max_gpu_layer:
                    model_menu.add_command(
                        label=f"L{max_gpu_layer}",
                        command=lambda n=llm_name, g=max_gpu_layer: self.select_model(n, g)
                    )
                    break
                else:
                    model_menu.add_command(
                        label=f"L{gpu_layer}",
                        command=lambda n=llm_name, g=gpu_layer: self.select_model(n, g)
                    )

    def select_model(self, llm_name, gpu_layer):
        """モデルを選択して起動"""
        try:
            self.ctx["llm_name"] = llm_name
            self.ctx["llm_gpu_layer"] = gpu_layer
            result = self.ctx.kobold_cpp.launch_server()
            if result is not None:
                messagebox.showerror("エラー", result, parent=self.form.win)
        except Exception as e:
            messagebox.showerror("エラー", f"モデルの起動中にエラーが発生しました:\n{str(e)}", parent=self.form.win)

    def add_model(self):
        """GGUFモデルを追加"""
        try:
            dialog = ModelAddDialog(self.form)
            dialog.grab_set()
            self.form.wait_window(dialog)
            # メニューを更新
            self.on_menu_open()
        except Exception as e:
            messagebox.showerror("エラー", f"モデル追加中にエラーが発生しました:\n{str(e)}", parent=self.form.win)

    def _download_model(self, llm_name):
        """モデルをダウンロード"""
        try:
            result = self.ctx.kobold_cpp.download_model(llm_name)
            if result:
                messagebox.showerror("エラー", result, parent=self.form.win)
            else:
                messagebox.showinfo("成功", f"{llm_name}のダウンロードが完了しました", parent=self.form.win)
                self.on_menu_open()
        except Exception as e:
            messagebox.showerror("エラー", f"ダウンロード中にエラーが発生しました:\n{str(e)}", parent=self.form.win)
