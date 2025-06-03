# -*- coding: utf-8 -*-
import json
import os
import subprocess
import webbrowser
from sys import platform

import requests
from path import Path


class KoboldCpp:
    BAT_TEMPLATE = r"""@echo off
chcp 65001 > NUL
pushd %~dp0
set CURL_CMD=C:\Windows\System32\curl.exe -k

@REM 7B: 33, 35B: 41, 70B: 65
set GPU_LAYERS=0

@REM 2048, 4096, 8192, 16384, 32768, 65536, 131072
set CONTEXT_SIZE={context_size}

{curl_cmd}
koboldcpp.exe --gpulayers %GPU_LAYERS% {option} --contextsize %CONTEXT_SIZE% {file_name}
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )
popd
"""

    CURL_TEMPLATE = """if not exist {file_name} (
    start "" {info_url}
    %CURL_CMD% -LO {url}
)
"""

    def __init__(self, ctx):
        self.ctx = ctx
        self.base_url = f'http://{ctx["koboldcpp_host"]}:{ctx["koboldcpp_port"]}'
        self.model_url = f"{self.base_url}/api/v1/model"
        self.generate_url = f"{self.base_url}/api/v1/generate"
        self.check_url = f"{self.base_url}/api/extra/generate/check"
        self.abort_url = f"{self.base_url}/api/extra/abort"

        self.model_name = None

        for llm_name in ctx.llm:
            llm = ctx.llm[llm_name]
            name = llm_name
            if "/" in llm_name:
                _, name = llm_name.split("/")
            if " " in name:
                name = name.split(" ")[-1]
            llm["name"] = name

            # ローカルでの新規追加モデルの場合
            if "file_name" in llm and not "urls" in llm:
                llm["urls"] = []
                llm["info_url"] = ""
                continue

            # 既存の配布モデルの場合
            llm["file_names"] = []
            for url in llm["urls"]:
                llm["file_names"].append(url.split("/")[-1])
            llm["file_name"] = llm["file_names"][0]
            # urls[0]の "/resolve/main/" より前を取得
            llm["info_url"] = llm["urls"][0].split("/resolve/main/")[0]

            context_size = min(llm["context_size"], ctx["llm_context_size"])
            bat_file = os.path.join(Path.kobold_cpp, f'Run-{llm["name"]}-C{context_size // 1024}K-L0.bat')

            curl_cmd = ""
            for url in llm["urls"]:
                curl_cmd += self.CURL_TEMPLATE.format(url=url, file_name=url.split("/")[-1], info_url=llm["info_url"])
            bat_text = self.BAT_TEMPLATE.format(
                curl_cmd=curl_cmd,
                option=ctx["koboldcpp_arg"],
                context_size=context_size,
                file_name=llm["file_name"],
            )
            with open(bat_file, "w", encoding="utf-8") as f:
                f.write(bat_text)
    def get_model(self):
        try:
            response = requests.get(self.model_url, timeout=self.ctx["koboldcpp_command_timeout"])
            if response.status_code == 200:
                self.model_name = response.json()["result"].split("/")[-1]
                return self.model_name
        except Exception as e:
            pass
        self.model_name = None
        return self.model_name

    def get_instruct_sequence(self):
        if self.model_name is not None:
            for sequence in self.ctx.llm_sequence.values():
                for model_name in sequence["model_names"]:
                    if model_name in self.model_name:
                        return sequence["instruct"]
        return None

    def get_stop_sequence(self):
        if self.model_name is not None:
            for sequence in self.ctx.llm_sequence.values():
                for model_name in sequence["model_names"]:
                    if model_name in self.model_name:
                        return sequence["stop"]
        return []

    def download_model(self, llm_name):
        llm = self.ctx.llm[llm_name]
        
        # ローカル追加モデルの場合（urlsが空の場合）
        if not llm.get("urls") or not llm.get("info_url"):
            return f"{llm_name} はローカルモデルのため、ダウンロードできません。\nモデルファイルを手動で配置してください。"
        
        webbrowser.open(llm["info_url"])
        for url in llm["urls"]:
            curl_cmd = f"curl -k -LO {url}"
            if subprocess.run(curl_cmd, shell=True, cwd=Path.kobold_cpp).returncode != 0:
                return f"{llm_name} のダウンロードに失敗しました。\n{curl_cmd}"
        return None

    def launch_server(self):
        loaded_model = self.get_model()
        if loaded_model is not None:
            return f"{loaded_model} がすでにロード済みです。\nモデルサーバーのコマンドプロンプトを閉じてからロードしてください。"

        if self.ctx["llm_name"] not in self.ctx.llm:
            self.ctx["llm_name"] = "[元祖] LightChatAssistant-TypeB-2x7B-IQ4_XS"
            self.ctx["llm_gpu_layer"] = 0

        llm_name = self.ctx["llm_name"]
        gpu_layer = self.ctx["llm_gpu_layer"]

        llm = self.ctx.llm[llm_name]
        llm_path = os.path.join(Path.kobold_cpp, llm["file_name"])

        if not os.path.exists(llm_path):
            result = self.download_model(llm_name)
            if result is not None:
                return result

        if not os.path.exists(llm_path):
            return f"{llm_path} がありません。"

        # モデルファイルの基本的な整合性チェック
        try:
            file_size = os.path.getsize(llm_path)
            if file_size < 1024 * 1024:  # 1MB未満の場合は明らかに破損
                return f"モデルファイル {llm['file_name']} が破損している可能性があります。\nファイルサイズが異常に小さいです ({file_size} bytes)。\nファイルを削除して再ダウンロードしてください。"
            
            # ファイルが.crdownloadで終わる場合（未完了ダウンロード）
            if llm_path.endswith('.crdownload'):
                return f"モデルファイル {llm['file_name']} のダウンロードが未完了です。\nダウンロードを完了してからお試しください。"
                
        except Exception as e:
            return f"モデルファイル {llm['file_name']} の確認中にエラーが発生しました: {str(e)}"

        context_size = min(llm["context_size"], self.ctx["llm_context_size"])
        command_args = f'{self.ctx["koboldcpp_arg"]} --gpulayers {gpu_layer} --contextsize {context_size} "{llm_path}"'
        
        print(f"KoboldCpp起動コマンド: {command_args}")
        
        if platform == "win32":
            try:
                # シンプルで確実な方法
                cmd = f'start "{llm_name} L{gpu_layer}" cmd /k "cd /d \"{Path.kobold_cpp}\" && \"{Path.kobold_cpp_win}\" {command_args}"'
                subprocess.run(cmd, shell=True)
                print(f"KoboldCppサーバーを起動しました: {llm_name}")
            except Exception as e:
                return f"KoboldCppサーバーの起動に失敗しました: {str(e)}"
        else:
            try:
                subprocess.Popen(f'"{Path.kobold_cpp_linux}" {command_args}', cwd=Path.kobold_cpp, shell=True)
                print(f"KoboldCppサーバーを起動しました: {llm_name}")
            except Exception as e:
                return f"KoboldCppサーバーの起動に失敗しました: {str(e)}"
        return None

    def generate(self, text):
        ctx = self.ctx

        if self.ctx["llm_name"] not in self.ctx.llm:
            self.ctx["llm_name"] = "[元祖] LightChatAssistant-TypeB-2x7B-IQ4_XS"
            self.ctx["llm_gpu_layer"] = 0

        llm_name = ctx["llm_name"]
        llm = ctx.llm[llm_name]

        # api/extra/true_max_context_length なら立ち上げ済みサーバーに対応可能
        max_context_length = min(llm["context_size"], ctx["llm_context_size"])
        if ctx["max_length"] >= max_context_length:
            print(
                f'生成文の長さ ({ctx["max_length"]}) がコンテキストサイズ上限 ({max_context_length}) 以上なため、{max_context_length // 2} に短縮します。'
            )
            ctx["max_length"] = max_context_length // 2

        args = {
            "max_context_length": max_context_length,
            "max_length": ctx["max_length"],
            "prompt": text,
            "quiet": False,
            "stop_sequence": self.get_stop_sequence(),
            "rep_pen": ctx["rep_pen"],
            "rep_pen_range": ctx["rep_pen_range"],
            "rep_pen_slope": ctx["rep_pen_slope"],
            "temperature": ctx["temperature"],
            "tfs": ctx["tfs"],
            "top_a": ctx["top_a"],
            "top_k": ctx["top_k"],
            "top_p": ctx["top_p"],
            "typical": ctx["typical"],
            "min_p": ctx["min_p"],
            "sampler_order": ctx["sampler_order"],
        }
        print(f"KoboldCpp.generate({args})")
        try:
            response = requests.post(self.generate_url, json=args)
            if response.status_code == 200:
                if self.model_name is not None:
                    args["model_name"] = self.model_name
                args["result"] = response.json()["results"][0]["text"]
                print(f'KoboldCpp.generate(): {args["result"]}')
                with open(Path.generate_log, "a", encoding="utf-8-sig") as f:
                    json.dump(args, f, indent=4, ensure_ascii=False)
                    f.write("\n")
                return args["result"]
            print(f"[失敗] KoboldCpp.generate(): {response.text}")
        except Exception as e:
            print(f"[例外] KoboldCpp.generate(): {e}")
        return None

    def check(self):
        try:
            response = requests.get(self.check_url)
            if response.status_code == 200:
                return response.json()["results"][0]["text"]
            print(f"[失敗] KoboldCpp.check(): {response.text}")
        except Exception as e:
            pass  # print(f"[例外] KoboldCpp.check(): {e}") # 害が無さそう＆利用者が混乱しそう
        return None

    def abort(self):
        try:
            response = requests.post(self.abort_url, timeout=self.ctx["koboldcpp_command_timeout"])
            if response.status_code == 200:
                return response.json()["success"]
            print(f"[失敗] KoboldCpp.abort(): {response.text}")
        except Exception as e:
            print(f"[例外] KoboldCpp.abort(): {e}")
        return None

    def cleanup_corrupted_files(self):
        """破損したファイルや未完了ダウンロードファイルをクリーンアップ"""
        cleanup_count = 0
        
        # .crdownloadファイルを削除
        for file in os.listdir(Path.kobold_cpp):
            if file.endswith('.crdownload'):
                file_path = os.path.join(Path.kobold_cpp, file)
                try:
                    os.remove(file_path)
                    print(f"未完了ダウンロードファイルを削除しました: {file}")
                    cleanup_count += 1
                except Exception as e:
                    print(f"ファイル削除エラー: {file} - {str(e)}")
        
        # 異常に小さいggufファイルを削除
        for file in os.listdir(Path.kobold_cpp):
            if file.endswith('.gguf'):
                file_path = os.path.join(Path.kobold_cpp, file)
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size < 1024 * 1024:  # 1MB未満
                        os.remove(file_path)
                        print(f"破損したモデルファイルを削除しました: {file} ({file_size} bytes)")
                        cleanup_count += 1
                except Exception as e:
                    print(f"ファイル確認エラー: {file} - {str(e)}")
        
        return cleanup_count

    def verify_model_file(self, llm_name):
        """モデルファイルの整合性を確認"""
        if llm_name not in self.ctx.llm:
            return False, "指定されたモデルが見つかりません"
            
        llm = self.ctx.llm[llm_name]
        llm_path = os.path.join(Path.kobold_cpp, llm["file_name"])
        
        if not os.path.exists(llm_path):
            return False, "モデルファイルが存在しません"
            
        try:
            file_size = os.path.getsize(llm_path)
            if file_size < 1024 * 1024:  # 1MB未満
                return False, f"ファイルサイズが異常です ({file_size} bytes)"
                
            # ggufファイルの基本的なヘッダーチェック
            with open(llm_path, 'rb') as f:
                header = f.read(4)
                if header != b'GGUF':
                    return False, "GGUFファイルのヘッダーが正しくありません"
                    
            return True, "モデルファイルは正常です"
            
        except Exception as e:
            return False, f"ファイル確認エラー: {str(e)}"
