import json
import os
import subprocess
import webbrowser
from typing import Callable, Optional
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
        self.backend = (ctx["llm_backend"] or "koboldcpp").lower()
        self.base_url = f'http://{ctx["koboldcpp_host"]}:{ctx["koboldcpp_port"]}'
        if self.backend == "hypura":
            # Hypura serves Ollama-compatible endpoints
            self.model_url = f"{self.base_url}/api/tags"
            self.generate_url = f"{self.base_url}/api/generate"
            self.stream_url = f"{self.base_url}/api/extra/generate/stream"
            self.check_url = f"{self.base_url}/api/extra/generate/check"
            self.abort_url = f"{self.base_url}/api/extra/abort"
        else:
            self.model_url = f"{self.base_url}/api/v1/model"
            self.generate_url = f"{self.base_url}/api/v1/generate"
            self.stream_url = None
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

            # ローカルファイルの場合の処理
            if llm.get("local_file", False):
                # ローカルファイルの場合、URLからファイル名を取得せずに直接file_nameを使用
                if "file_name" not in llm:
                    llm["file_name"] = llm["urls"][0].split("/")[-1] if llm.get("urls") else "unknown.gguf"
                llm["file_names"] = [llm["file_name"]]
                llm["info_url"] = "local_file"  # ローカルファイルの場合は特別な値を設定
            else:
                # 通常のリモートファイルの場合の処理
                llm["file_names"] = []
                for url in llm["urls"]:
                    llm["file_names"].append(url.split("/")[-1])
                llm["file_name"] = llm["file_names"][0]
                # urls[0]の "/resolve/main/" より前を取得
                if "/resolve/main/" in llm["urls"][0]:
                    llm["info_url"] = llm["urls"][0].split("/resolve/main/")[0]
                else:
                    llm["info_url"] = llm["urls"][0].split("/resolve/")[0] if "/resolve/" in llm["urls"][0] else llm["urls"][0]

            context_size = min(llm["context_size"], ctx["llm_context_size"])
            # ファイル名に無効な文字が含まれている場合のサニタイズ処理
            safe_name = Path.get_path_name(llm["name"])
            bat_file = os.path.join(Path.kobold_cpp, f'Run-{safe_name}-C{context_size // 1024}K-L0.bat')

            # ローカルファイルの場合はcurl_cmdを空にする
            if llm.get("local_file", False):
                curl_cmd = ""
            else:
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
                if self.backend == "hypura":
                    models = response.json().get("models", [])
                    if len(models) > 0:
                        self.model_name = models[0].get("name") or models[0].get("model")
                    else:
                        self.model_name = None
                else:
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
        
        # ローカルファイルの場合はダウンロードをスキップ
        if llm.get("local_file", False):
            return None
        
        webbrowser.open(llm["info_url"])
        for url in llm["urls"]:
            curl_cmd = f"curl -k -LO {url}"
            if subprocess.run(curl_cmd, shell=True, cwd=Path.kobold_cpp).returncode != 0:
                return f"{llm_name} のダウンロードに失敗しました。\n{curl_cmd}"
        return None

    def download_url(self, url):
        curl_cmd = f"curl -k -LO {url}"
        if subprocess.run(curl_cmd, shell=True, cwd=Path.kobold_cpp).returncode != 0:
            return f"モデルのダウンロードに失敗しました。\n{curl_cmd}"
        return None

    def launch_server(self):
        if self.backend == "hypura":
            loaded_model = self.get_model()
            if loaded_model is None:
                return (
                    f"Hypura に接続できません: {self.base_url}\n"
                    f"先に hypura serve を起動してください。"
                )
            return None

        loaded_model = self.get_model()
        if loaded_model is not None:
            return f"{loaded_model} がすでにロード済みです。\nモデルサーバーのコマンドプロンプトを閉じてからロードしてください。"

        if self.ctx["llm_name"] not in self.ctx.llm:
            self.ctx["llm_name"] = "[元祖] LightChatAssistant-TypeB-2x7B-IQ4_XS"
            self.ctx["llm_gpu_layer"] = 0

        llm_name = self.ctx["llm_name"]
        gpu_layer = self.ctx["llm_gpu_layer"]

        llm = self.ctx.llm[llm_name]
        
        # ローカルファイルの場合は、file://プレフィックスがある場合は除去してパスを取得
        if llm.get("local_file", False) and llm.get("urls") and llm["urls"][0].startswith("file://"):
            llm_path = llm["urls"][0][7:]  # "file://" を除去
        else:
            llm_path = os.path.join(Path.kobold_cpp, llm["file_name"])

        if not os.path.exists(llm_path):
            # ローカルファイルでない場合のみダウンロードを試行
            if not llm.get("local_file", False):
                result = self.download_model(llm_name)
                if result is not None:
                    return result

        if not os.path.exists(llm_path):
            return f"{llm_path} がありません。"

        context_size = min(llm["context_size"], self.ctx["llm_context_size"])
        command_args = f'{self.ctx["koboldcpp_arg"]} --gpulayers {gpu_layer} --contextsize {context_size} {llm_path}'
        if platform == "win32":
            command = ["start", f"{llm_name} L{gpu_layer}", "cmd", "/c"]
            command.append(f"{Path.kobold_cpp_win} {command_args} || pause")
            subprocess.run(command, cwd=Path.kobold_cpp, shell=True)
        else:
            subprocess.Popen(f"{Path.kobold_cpp_linux} {command_args}", cwd=Path.kobold_cpp, shell=True)
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

        if self.backend == "hypura":
            if self.model_name is None:
                self.get_model()
            args = {
                "model": self.model_name or llm.get("name") or llm_name,
                "prompt": text,
                "stream": False,
                "options": {
                    "num_predict": ctx["max_length"],
                    "temperature": ctx["temperature"],
                    "top_k": ctx["top_k"],
                    "top_p": ctx["top_p"],
                    "repeat_penalty": ctx["rep_pen"],
                },
            }
        else:
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
                if self.backend == "hypura":
                    args["result"] = response.json().get("response", "")
                else:
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

    def generate_stream(self, text, on_token: Optional[Callable[[str], None]] = None):
        """
        Stream tokens and return the final combined text.
        Falls back to non-stream generate for non-hypura backends.
        """
        if self.backend != "hypura":
            result = self.generate(text)
            if result and on_token is not None:
                on_token(result)
            return result

        ctx = self.ctx
        if self.ctx["llm_name"] not in self.ctx.llm:
            self.ctx["llm_name"] = "[元祖] LightChatAssistant-TypeB-2x7B-IQ4_XS"
            self.ctx["llm_gpu_layer"] = 0

        llm_name = ctx["llm_name"]
        llm = ctx.llm[llm_name]
        if self.model_name is None:
            self.get_model()

        stream_args = {
            "prompt": text,
            "max_length": ctx["max_length"],
            "temperature": ctx["temperature"],
            "top_k": ctx["top_k"],
            "top_p": ctx["top_p"],
            "rep_pen": ctx["rep_pen"],
            "rep_pen_range": ctx["rep_pen_range"],
            "rep_pen_slope": ctx["rep_pen_slope"],
            "tfs": ctx["tfs"],
            "top_a": ctx["top_a"],
            "typical": ctx["typical"],
            "min_p": ctx["min_p"],
            "sampler_order": ctx["sampler_order"],
            "stop_sequence": self.get_stop_sequence(),
            "model": self.model_name or llm.get("name") or llm_name,
        }
        print(f"KoboldCpp.generate_stream({stream_args})")
        tokens = []
        try:
            with requests.post(
                self.stream_url,
                json=stream_args,
                stream=True,
                timeout=self.ctx["koboldcpp_command_timeout"],
            ) as response:
                if response.status_code != 200:
                    print(f"[失敗] KoboldCpp.generate_stream(): {response.text}")
                    return None
                for raw_line in response.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    try:
                        obj = json.loads(raw_line)
                    except Exception:
                        continue
                    token = obj.get("token")
                    if not token:
                        continue
                    tokens.append(token)
                    if on_token is not None:
                        on_token(token)
            result = "".join(tokens)
            with open(Path.generate_log, "a", encoding="utf-8-sig") as f:
                json.dump(
                    {
                        "stream": True,
                        "model_name": self.model_name,
                        "prompt": text,
                        "result": result,
                    },
                    f,
                    indent=4,
                    ensure_ascii=False,
                )
                f.write("\n")
            return result
        except Exception as e:
            print(f"[例外] KoboldCpp.generate_stream(): {e}")
            return None

    def check(self):
        if self.backend == "hypura":
            # Ollama-compatible generate check endpoint does not exist.
            return None
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
