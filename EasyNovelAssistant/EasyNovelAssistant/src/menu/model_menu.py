import os
import json
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox

from path import Path


class ModelMenu:
    SEPALATER_NAMES = [
        "LightChatAssistant-4x7B-IQ4_XS",
    ]

    def __init__(self, form, ctx):
        self.form = form
        self.ctx = ctx

        self.menu = tk.Menu(form.win, tearoff=False)
        self.form.menu_bar.add_cascade(label="モデル", menu=self.menu)
        self.menu.configure(postcommand=self.on_menu_open)

    def on_menu_open(self):
        self.menu.delete(0, tk.END)

        def context_label(context_size):
            llm_name = self.ctx["llm_name"]
            model_ctx_size = self.ctx.llm[llm_name]["context_size"]
            if context_size > model_ctx_size:
                return f"C{model_ctx_size // 1024}K: {context_size} > {model_ctx_size}({llm_name})"
            return f"C{context_size // 1024}K: {context_size}"

        self.llm_context_size_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(
            label=f'コンテキストサイズ上限（増やすと VRAM 消費増）: {context_label(self.ctx["llm_context_size"])})',
            menu=self.llm_context_size_menu,
        )

        def set_llm_context_size(llm_context_size):
            self.ctx["llm_context_size"] = llm_context_size

        llm_context_sizes = [2048, 4096, 8192, 16384, 32768, 65536, 131072]
        for llm_context_size in llm_context_sizes:
            check_var = tk.BooleanVar(value=self.ctx["llm_context_size"] == llm_context_size)
            self.llm_context_size_menu.add_checkbutton(
                label=context_label(llm_context_size),
                variable=check_var,
                command=lambda v=llm_context_size, _=check_var: set_llm_context_size(v),
            )

        self.menu.add_separator()

        # GGUFファイル関連メニューを追加
        self.menu.add_command(
            label="GGUFファイルを直接選択...",
            command=self.select_gguf_file_directly
        )
        self.menu.add_command(
            label="GGUFファイルを追加...",
            command=self.add_gguf_file
        )
        self.menu.add_separator()

        self.menu.add_command(label="URLからモデル追加", command=self.add_model_from_url)
        self.menu.add_separator()

        categories = {}

        for llm_name in self.ctx.llm:
            llm = self.ctx.llm[llm_name]

            llm_menu = tk.Menu(self.menu, tearoff=False)
            name = llm_name
            context_size = min(llm["context_size"], self.ctx["llm_context_size"]) // 1024
            if "/" in llm_name:
                category, name = llm_name.split("/")
                if category not in categories:
                    categories[category] = tk.Menu(self.menu, tearoff=False)
                    self.menu.add_cascade(label=category, menu=categories[category])
                categories[category].add_cascade(label=f"{name} C{context_size}K", menu=llm_menu)
            else:
                self.menu.add_cascade(label=f"{llm_name} C{context_size}K", menu=llm_menu)

            for sep_name in self.SEPALATER_NAMES:
                if sep_name in name:
                    self.menu.add_separator()

            llm_path = os.path.join(Path.kobold_cpp, llm["file_name"])
            if not os.path.exists(llm_path):
                llm_menu.add_command(
                    label="ダウンロード（完了まで応答なし、コマンドプロンプトに状況表示）",
                    command=lambda ln=llm_name: self.ctx.kobold_cpp.download_model(ln),
                )
                continue

            max_gpu_layer = llm["max_gpu_layer"]
            for gpu_layer in self.ctx["llm_gpu_layers"]:
                if gpu_layer > max_gpu_layer:
                    llm_menu.add_command(
                        label=f"L{max_gpu_layer}",
                        command=lambda ln=llm_name, gl=max_gpu_layer: self.select_model(ln, gl),
                    )
                    break
                else:
                    llm_menu.add_command(
                        label=f"L{gpu_layer}", command=lambda ln=llm_name, gl=gpu_layer: self.select_model(ln, gl)
                    )

    def select_model(self, llm_name, gpu_layer):
        self.ctx["llm_name"] = llm_name
        self.ctx["llm_gpu_layer"] = gpu_layer
        result = self.ctx.kobold_cpp.launch_server()
        if result is not None:
            print(result)
            messagebox.showerror("エラー", result, parent=self.form.win)

    def select_gguf_file_directly(self):
        """GGUFファイルを直接選択して即座に使用する機能"""
        try:
            # ファイル選択ダイアログを開く
            file_path = filedialog.askopenfilename(
                title="使用するGGUFファイルを選択",
                filetypes=[
                    ("GGUF files", "*.gguf"),
                    ("All files", "*.*")
                ],
                parent=self.form.win
            )
            
            if not file_path:
                return  # キャンセルされた場合
            
            # ファイルが存在するかチェック
            if not os.path.exists(file_path):
                messagebox.showerror("エラー", "選択されたファイルが存在しません。", parent=self.form.win)
                return
            
            # ファイル名を取得
            file_name = os.path.basename(file_path)
            model_name = os.path.splitext(file_name)[0]
            
            # GPU層数の入力ダイアログ（簡易版）
            gpu_layers = simpledialog.askinteger(
                "GPU層数設定",
                f"GPU層数を入力してください:\n\nファイル: {file_name}\n\n7Bモデル: 33\n13Bモデル: 41\n70Bモデル: 65",
                initialvalue=33,
                minvalue=0,
                maxvalue=100,
                parent=self.form.win
            )
            
            if gpu_layers is None:
                return  # キャンセルされた場合
            
            # KoboldCppディレクトリにファイルをコピー（必要な場合のみ）
            target_path = os.path.join(Path.kobold_cpp, file_name)
            
            if target_path != file_path:
                import shutil
                try:
                    shutil.copy2(file_path, target_path)
                    print(f"ファイルをコピーしました: {file_path} -> {target_path}")
                except Exception as e:
                    # コピーに失敗した場合は元のパスを使用
                    target_path = file_path
                    print(f"ファイルコピーに失敗、元のパスを使用: {file_path}")
            
            # 一時的なモデル設定を作成（llm.jsonには保存しない）
            temp_model_name = f"[直接選択] {model_name}"
            model_config = {
                "max_gpu_layer": gpu_layers,
                "context_size": 4096,  # デフォルト値
                "urls": [f"file://{target_path}"],
                "file_name": file_name,
                "local_file": True,
                "temporary": True  # 一時的なモデルであることを示すフラグ
            }
            
            # コンテキストに一時的に追加
            self.ctx.llm[temp_model_name] = model_config
            
            # 直接モデルを選択して起動
            self.ctx["llm_name"] = temp_model_name
            self.ctx["llm_gpu_layer"] = gpu_layers
            
            result = self.ctx.kobold_cpp.launch_server()
            if result is not None:
                print(result)
                messagebox.showerror("エラー", result, parent=self.form.win)
            else:
                messagebox.showinfo(
                    "完了",
                    f"GGUFファイルを直接選択しました:\n\nファイル: {file_name}\nGPU層数: {gpu_layers}\n\nモデルサーバーを起動中...",
                    parent=self.form.win
                )
                print(f"GGUFファイルを直接選択: {file_name}")
                
        except Exception as e:
            messagebox.showerror("エラー", f"GGUFファイルの選択中にエラーが発生しました:\n{str(e)}", parent=self.form.win)
            print(f"GGUF直接選択エラー: {str(e)}")

    def add_gguf_file(self):
        """GGUFファイルを追加する機能"""
        try:
            # ファイル選択ダイアログを開く
            file_path = filedialog.askopenfilename(
                title="GGUFファイルを選択",
                filetypes=[
                    ("GGUF files", "*.gguf"),
                    ("All files", "*.*")
                ],
                parent=self.form.win
            )
            
            if not file_path:
                return  # キャンセルされた場合
            
            # ファイルが存在するかチェック
            if not os.path.exists(file_path):
                messagebox.showerror("エラー", "選択されたファイルが存在しません。", parent=self.form.win)
                return
            
            # ファイル名を取得
            file_name = os.path.basename(file_path)
            model_name = os.path.splitext(file_name)[0]
            
            # モデル名の入力ダイアログ
            display_name = simpledialog.askstring(
                "モデル名入力",
                f"モデルの表示名を入力してください:\n\nファイル: {file_name}",
                initialvalue=model_name,
                parent=self.form.win
            )
            
            if not display_name:
                return  # キャンセルされた場合
            
            # 既存のモデル名と重複チェック
            if display_name in self.ctx.llm:
                if not messagebox.askyesno(
                    "確認", 
                    f"モデル名 '{display_name}' は既に存在します。\n上書きしますか？",
                    parent=self.form.win
                ):
                    return
            
            # GPU層数の入力ダイアログ
            gpu_layers = simpledialog.askinteger(
                "GPU層数設定",
                "GPU層数を入力してください:\n\n7Bモデル: 33\n13Bモデル: 41\n70Bモデル: 65\n\n不明な場合は33を推奨",
                initialvalue=33,
                minvalue=0,
                maxvalue=100,
                parent=self.form.win
            )
            
            if gpu_layers is None:
                return  # キャンセルされた場合
            
            # コンテキストサイズの入力ダイアログ
            context_size = simpledialog.askinteger(
                "コンテキストサイズ設定",
                "コンテキストサイズを入力してください:\n\n一般的な値:\n2048, 4096, 8192, 16384, 32768\n\n不明な場合は4096を推奨",
                initialvalue=4096,
                minvalue=512,
                maxvalue=131072,
                parent=self.form.win
            )
            
            if context_size is None:
                return  # キャンセルされた場合
            
            # KoboldCppディレクトリにファイルをコピー
            target_path = os.path.join(Path.kobold_cpp, file_name)
            
            # 既存ファイルがある場合の確認
            if os.path.exists(target_path) and target_path != file_path:
                if not messagebox.askyesno(
                    "確認",
                    f"KoboldCppディレクトリに同名のファイルが既に存在します。\n上書きしますか？\n\n{target_path}",
                    parent=self.form.win
                ):
                    return
            
            # ファイルをコピー（同じ場所にある場合はコピー不要）
            if target_path != file_path:
                import shutil
                try:
                    shutil.copy2(file_path, target_path)
                    print(f"ファイルをコピーしました: {file_path} -> {target_path}")
                except Exception as e:
                    messagebox.showerror("エラー", f"ファイルのコピーに失敗しました:\n{str(e)}", parent=self.form.win)
                    return
            
            # モデル設定を作成
            model_config = {
                "max_gpu_layer": gpu_layers,
                "context_size": context_size,
                "urls": [f"file://{target_path}"],  # ローカルファイルの場合
                "file_name": file_name,
                "local_file": True  # ローカルファイルであることを示すフラグ
            }
            
            # llm.jsonを読み込み
            llm_data = {}
            if os.path.exists(Path.llm):
                try:
                    with open(Path.llm, "r", encoding="utf-8-sig") as f:
                        llm_data = json.load(f)
                except json.JSONDecodeError:
                    llm_data = {}
            
            # 新しいモデルを追加
            llm_data[display_name] = model_config
            
            # llm.jsonに保存
            try:
                with open(Path.llm, "w", encoding="utf-8-sig") as f:
                    json.dump(llm_data, f, indent=4, ensure_ascii=False)
                
                # コンテキストのllm辞書を更新
                self.ctx.llm[display_name] = model_config
                
                messagebox.showinfo(
                    "完了",
                    f"GGUFモデルを追加しました:\n\n名前: {display_name}\nファイル: {file_name}\nGPU層数: {gpu_layers}\nコンテキストサイズ: {context_size}",
                    parent=self.form.win
                )
                
                print(f"GGUFモデルを追加: {display_name}")
                
            except Exception as e:
                messagebox.showerror("エラー", f"設定の保存に失敗しました:\n{str(e)}", parent=self.form.win)
                
        except Exception as e:
            messagebox.showerror("エラー", f"GGUFファイルの追加中にエラーが発生しました:\n{str(e)}", parent=self.form.win)
            print(f"GGUFファイル追加エラー: {str(e)}")

    def add_model_from_url(self):
        url = simpledialog.askstring(
            "モデルURL入力",
            "HuggingFace の GGUF ファイル URL を入力してください。",
            parent=self.form.win,
        )
        if not url:
            return
        name = simpledialog.askstring("モデル名入力", "メニューに表示するモデル名を入力してください。", parent=self.form.win)
        if not name:
            name = url.split("/")[-1]
        result = self.ctx.kobold_cpp.download_url(url)
        if result is not None:
            print(result)
            messagebox.showerror("エラー", result, parent=self.form.win)
            return

        info_url = url.split("/resolve/")[0]
        file_name = url.split("/")[-1]
        llm_data = {
            "max_gpu_layer": 33,
            "context_size": 4096,
            "urls": [url],
        }
        self.ctx.llm[name] = llm_data

        # update llm.json
        try:
            user_llm = {}
            if os.path.exists(Path.llm):
                with open(Path.llm, "r", encoding="utf-8-sig") as f:
                    user_llm = json.load(f)
        except Exception:
            user_llm = {}
        user_llm[name] = llm_data
        with open(Path.llm, "w", encoding="utf-8-sig") as f:
            json.dump(user_llm, f, indent=4, ensure_ascii=False)

        # update internal info for immediate use
        llm_data["name"] = name.split("/")[-1].split(" ")[-1]
        llm_data["file_names"] = [file_name]
        llm_data["file_name"] = file_name
        llm_data["info_url"] = info_url

