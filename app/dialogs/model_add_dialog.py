import json
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from app.core.path import Path

class ModelAddDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("LLMモデル追加")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # メインフレーム
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ファイル選択部分
        file_frame = ttk.LabelFrame(main_frame, text="GGUFファイル選択", padding="5")
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.file_path = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path, state='readonly', width=50)
        file_entry.pack(side=tk.LEFT, padx=5)
        
        browse_btn = ttk.Button(file_frame, text="参照...", command=self.browse_file)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # モデル設定部分
        settings_frame = ttk.LabelFrame(main_frame, text="モデル設定", padding="5")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # モデル名
        name_frame = ttk.Frame(settings_frame)
        name_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(name_frame, text="モデル名:").pack(side=tk.LEFT)
        self.model_name = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.model_name, width=40)
        name_entry.pack(side=tk.LEFT, padx=5)
        
        # GPUレイヤー数
        gpu_frame = ttk.Frame(settings_frame)
        gpu_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(gpu_frame, text="GPUレイヤー数:").pack(side=tk.LEFT)
        self.gpu_layers = tk.IntVar(value=33)
        gpu_spin = ttk.Spinbox(gpu_frame, from_=0, to=33, textvariable=self.gpu_layers, width=10)
        gpu_spin.pack(side=tk.LEFT, padx=5)
        
        # コンテキストサイズ
        context_frame = ttk.Frame(settings_frame)
        context_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(context_frame, text="コンテキストサイズ:").pack(side=tk.LEFT)
        self.context_size = tk.IntVar(value=4096)
        context_values = [2048, 4096, 8192, 16384, 32768]
        context_combo = ttk.Combobox(context_frame, textvariable=self.context_size, 
                                   values=context_values, width=15, state='readonly')
        context_combo.pack(side=tk.LEFT, padx=5)
        
        # 追加ボタン
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=15)
        add_btn = ttk.Button(btn_frame, text="モデルを追加", command=self.add_model)
        add_btn.pack(side=tk.RIGHT, padx=5)
        cancel_btn = ttk.Button(btn_frame, text="キャンセル", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        # ダイアログをモーダルに
        self.transient(parent)
        self.grab_set()
        
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="GGUFファイルを選択",
            filetypes=[("GGUFファイル", "*.gguf")],
            initialdir=Path.kobold_cpp
        )
        if file_path:
            self.file_path.set(file_path)
            # ファイル名をデフォルトのモデル名として設定
            if not self.model_name.get():
                base_name = os.path.basename(file_path)
                name_without_ext = os.path.splitext(base_name)[0]
                self.model_name.set(name_without_ext)
    
    def validate_inputs(self):
        if not self.file_path.get():
            messagebox.showerror("エラー", "GGUFファイルを選択してください。")
            return False
        
        if not self.model_name.get():
            messagebox.showerror("エラー", "モデル名を入力してください。")
            return False
        
        if not os.path.exists(self.file_path.get()):
            messagebox.showerror("エラー", "選択されたファイルが存在しません。")
            return False
        
        return True
    
    def add_model(self):
        if not self.validate_inputs():
            return
            
        try:
            # ファイルのコピー
            src_path = self.file_path.get()
            dst_path = os.path.join(Path.kobold_cpp, os.path.basename(src_path))
            
            if os.path.normpath(src_path) != os.path.normpath(dst_path):
                shutil.copy2(src_path, dst_path)
            
            # モデル情報の登録
            config_path = Path.llm
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
            
            model_info = {
                "file_name": os.path.basename(src_path),
                "max_gpu_layer": self.gpu_layers.get(),
                "context_size": self.context_size.get()
            }
            
            config[self.model_name.get()] = model_info
            
            with open(config_path, 'w', encoding='utf-8-sig') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("成功", "モデルが正常に追加されました。")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("エラー", f"モデルの追加に失敗しました:\n{str(e)}")