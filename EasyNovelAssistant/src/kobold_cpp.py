import json
import os
import shutil
import subprocess
import webbrowser
from sys import platform

import requests
from path import Path


KOBOLDCPP_BACKEND = "koboldcpp"
HYPURA_BACKEND = "hypura"
DEFAULT_LLM_NAME = "[元祖] LightChatAssistant-TypeB-2x7B-IQ4_XS"
DEFAULT_GPU_LAYER = 0


def normalize_backend_name(raw_backend):
    if raw_backend is None:
        return KOBOLDCPP_BACKEND

    backend = str(raw_backend).strip().lower()
    if backend == HYPURA_BACKEND:
        return HYPURA_BACKEND
    return KOBOLDCPP_BACKEND


def display_backend_name(raw_backend):
    backend = normalize_backend_name(raw_backend)
    if backend == HYPURA_BACKEND:
        return "Hypura"
    return "KoboldCpp"


def build_hypura_command(executable, model_path, host, port, context_size):
    return [
        executable,
        "koboldcpp",
        model_path,
        "--host",
        str(host),
        "--port",
        str(port),
        "--context",
        str(context_size),
    ]


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
        self.stream_url = f"{self.base_url}/api/extra/generate/stream"
        self.check_url = f"{self.base_url}/api/extra/generate/check"
        self.abort_url = f"{self.base_url}/api/extra/abort"
        self.backend = normalize_backend_name(ctx["llm_backend"])
        self.model_name = None

        self._prepare_llm_entries()

    def _prepare_llm_entries(self):
        for llm_name, llm in self.ctx.llm.items():
            name = llm_name
            if "/" in llm_name:
                _, name = llm_name.split("/", 1)
            if " " in name:
                name = name.split(" ")[-1]
            llm["name"] = name

            if llm.get("local_file", False):
                if "file_name" not in llm:
                    if llm.get("urls"):
                        llm["file_name"] = llm["urls"][0].split("/")[-1]
                    else:
                        llm["file_name"] = "unknown.gguf"
                llm["file_names"] = [llm["file_name"]]
                llm["info_url"] = "local_file"
            else:
                llm["file_names"] = [url.split("/")[-1] for url in llm["urls"]]
                llm["file_name"] = llm["file_names"][0]
                if "/resolve/main/" in llm["urls"][0]:
                    llm["info_url"] = llm["urls"][0].split("/resolve/main/")[0]
                elif "/resolve/" in llm["urls"][0]:
                    llm["info_url"] = llm["urls"][0].split("/resolve/")[0]
                else:
                    llm["info_url"] = llm["urls"][0]

            context_size = min(llm["context_size"], self.ctx["llm_context_size"])
            safe_name = Path.get_path_name(llm["name"])
            bat_file = os.path.join(Path.kobold_cpp, f"Run-{safe_name}-C{context_size // 1024}K-L0.bat")
            curl_cmd = ""
            if not llm.get("local_file", False):
                for url in llm["urls"]:
                    curl_cmd += self.CURL_TEMPLATE.format(
                        url=url,
                        file_name=url.split("/")[-1],
                        info_url=llm["info_url"],
                    )
            bat_text = self.BAT_TEMPLATE.format(
                curl_cmd=curl_cmd,
                option=self.ctx["koboldcpp_arg"],
                context_size=context_size,
                file_name=llm["file_name"],
            )
            with open(bat_file, "w", encoding="utf-8") as file:
                file.write(bat_text)

    def set_backend(self, backend):
        normalized = normalize_backend_name(backend)
        self.ctx["llm_backend"] = normalized
        self.backend = normalized

    def display_backend_name(self, backend=None):
        if backend is None:
            backend = self.backend
        return display_backend_name(backend)

    def _ensure_selected_model(self):
        llm_name = self.ctx["llm_name"]
        if llm_name in self.ctx.llm:
            return llm_name, self.ctx.llm[llm_name], None

        if DEFAULT_LLM_NAME in self.ctx.llm:
            llm_name = DEFAULT_LLM_NAME
        else:
            llm_name = next(iter(self.ctx.llm), None)

        if llm_name is None:
            return None, None, "モデル設定がありません。llm.json を確認してください。"

        self.ctx["llm_name"] = llm_name
        self.ctx["llm_gpu_layer"] = DEFAULT_GPU_LAYER
        return llm_name, self.ctx.llm[llm_name], None

    def _resolve_model_path(self, llm):
        if llm.get("local_file", False) and llm.get("urls"):
            local_url = llm["urls"][0]
            if local_url.startswith("file://"):
                return local_url[7:]
        return os.path.join(Path.kobold_cpp, llm["file_name"])

    def _resolve_hypura_executable(self):
        configured_path = self.ctx["hypura_path"]
        if configured_path is not None:
            configured_path = str(configured_path).strip()
        if configured_path:
            if os.path.isdir(configured_path):
                filename = "hypura.exe" if platform == "win32" else "hypura"
                candidate = os.path.join(configured_path, filename)
                if os.path.exists(candidate):
                    return candidate
            if os.path.exists(configured_path):
                return configured_path
            return None

        return shutil.which("hypura")

    def get_model(self):
        try:
            response = requests.get(self.model_url, timeout=self.ctx["koboldcpp_command_timeout"])
            if response.status_code == 200:
                payload = response.json()
                result = payload.get("result")
                if isinstance(result, str) and result.strip():
                    self.model_name = result.split("/")[-1]
                    return self.model_name
        except Exception:
            pass

        self.model_name = None
        return None

    def get_instruct_sequence(self):
        if self.model_name is None:
            return None

        for sequence in self.ctx.llm_sequence.values():
            for model_name in sequence["model_names"]:
                if model_name in self.model_name:
                    return sequence["instruct"]
        return None

    def get_stop_sequence(self):
        if self.model_name is None:
            return []

        for sequence in self.ctx.llm_sequence.values():
            for model_name in sequence["model_names"]:
                if model_name in self.model_name:
                    return sequence["stop"]
        return []

    def download_model(self, llm_name):
        llm = self.ctx.llm[llm_name]
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

    def _launch_koboldcpp(self, llm_name, gpu_layer, llm_path, context_size):
        if platform == "win32":
            if not os.path.exists(Path.kobold_cpp_win):
                return f"KoboldCpp が見つかりません。\n{Path.kobold_cpp_win}"
            command_args = (
                f'{self.ctx["koboldcpp_arg"]} --gpulayers {gpu_layer} '
                f"--contextsize {context_size} {llm_path}"
            )
            command = ["start", f"{llm_name} L{gpu_layer}", "cmd", "/c"]
            command.append(f"{Path.kobold_cpp_win} {command_args} || pause")
            subprocess.run(command, cwd=Path.kobold_cpp, shell=True)
            return None

        if not os.path.exists(Path.kobold_cpp_linux):
            return f"KoboldCpp が見つかりません。\n{Path.kobold_cpp_linux}"

        command_args = (
            f'{self.ctx["koboldcpp_arg"]} --gpulayers {gpu_layer} '
            f"--contextsize {context_size} {llm_path}"
        )
        subprocess.Popen(f"{Path.kobold_cpp_linux} {command_args}", cwd=Path.kobold_cpp, shell=True)
        return None

    def _launch_hypura(self, llm_path, context_size):
        executable = self._resolve_hypura_executable()
        configured_path = self.ctx["hypura_path"]
        if configured_path is not None:
            configured_path = str(configured_path).strip()

        if executable is None:
            if configured_path:
                return (
                    "Hypura 実行ファイルが見つかりません。\n"
                    f"設定値: {configured_path}\n"
                    "設定メニューで Hypura 実行ファイルのパスを確認してください。"
                )
            return (
                "Hypura 実行ファイルが見つかりません。\n"
                "設定メニューで Hypura 実行ファイルのパスを設定するか、PATH に hypura を追加してください。"
            )

        command = build_hypura_command(
            executable=executable,
            model_path=llm_path,
            host=self.ctx["koboldcpp_host"],
            port=self.ctx["koboldcpp_port"],
            context_size=context_size,
        )

        popen_kwargs = {"cwd": os.getcwd()}
        if platform == "win32" and hasattr(subprocess, "CREATE_NEW_CONSOLE"):
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE

        try:
            subprocess.Popen(command, **popen_kwargs)
        except Exception as error:
            return f"Hypura の起動に失敗しました。\n{error}"

        return None

    def launch_server(self):
        loaded_model = self.get_model()
        if loaded_model is not None:
            return (
                f"{loaded_model} がすでにロード済みです。\n"
                "モデルサーバーのコマンドプロンプトを閉じてからロードしてください。"
            )

        llm_name, llm, error = self._ensure_selected_model()
        if error is not None:
            return error

        llm_path = self._resolve_model_path(llm)
        if not os.path.exists(llm_path) and not llm.get("local_file", False):
            result = self.download_model(llm_name)
            if result is not None:
                return result

        if not os.path.exists(llm_path):
            return f"{llm_path} がありません。"

        context_size = min(llm["context_size"], self.ctx["llm_context_size"])
        gpu_layer = self.ctx["llm_gpu_layer"]
        if self.backend == HYPURA_BACKEND:
            return self._launch_hypura(llm_path, context_size)
        return self._launch_koboldcpp(llm_name, gpu_layer, llm_path, context_size)

    def _build_generate_args(self, text):
        _, llm, error = self._ensure_selected_model()
        if error is not None:
            raise RuntimeError(error)

        max_context_length = min(llm["context_size"], self.ctx["llm_context_size"])
        if self.ctx["max_length"] >= max_context_length:
            print(
                f'生成文の長さ ({self.ctx["max_length"]}) がコンテキストサイズ上限 '
                f'({max_context_length}) 以上なため、{max_context_length // 2} に短縮します。'
            )
            self.ctx["max_length"] = max_context_length // 2

        return {
            "max_context_length": max_context_length,
            "max_length": self.ctx["max_length"],
            "prompt": text,
            "quiet": False,
            "stop_sequence": self.get_stop_sequence(),
            "rep_pen": self.ctx["rep_pen"],
            "rep_pen_range": self.ctx["rep_pen_range"],
            "rep_pen_slope": self.ctx["rep_pen_slope"],
            "temperature": self.ctx["temperature"],
            "tfs": self.ctx["tfs"],
            "top_a": self.ctx["top_a"],
            "top_k": self.ctx["top_k"],
            "top_p": self.ctx["top_p"],
            "typical": self.ctx["typical"],
            "min_p": self.ctx["min_p"],
            "sampler_order": self.ctx["sampler_order"],
        }

    def generate(self, text):
        try:
            args = self._build_generate_args(text)
        except Exception as error:
            print(f"[例外] KoboldCpp.generate(): {error}")
            return None

        print(f"KoboldCpp.generate({args})")
        try:
            response = requests.post(self.generate_url, json=args)
            if response.status_code == 200:
                if self.model_name is not None:
                    args["model_name"] = self.model_name
                args["result"] = response.json()["results"][0]["text"]
                print(f'KoboldCpp.generate(): {args["result"]}')
                with open(Path.generate_log, "a", encoding="utf-8-sig") as file:
                    json.dump(args, file, indent=4, ensure_ascii=False)
                    file.write("\n")
                return args["result"]
            print(f"[失敗] KoboldCpp.generate(): {response.text}")
        except Exception as error:
            print(f"[例外] KoboldCpp.generate(): {error}")
        return None

    def generate_stream(self, text, on_token=None):
        if self.backend != HYPURA_BACKEND:
            result = self.generate(text)
            if result and on_token is not None:
                on_token(result)
            return result

        try:
            args = self._build_generate_args(text)
        except Exception as error:
            print(f"[例外] KoboldCpp.generate_stream(): {error}")
            return None

        print(f"KoboldCpp.generate_stream(max_length={args.get('max_length')})")
        try:
            response = requests.post(self.stream_url, json=args, stream=True, timeout=600)
            if response.status_code != 200:
                print(f"[失敗] KoboldCpp.generate_stream(): {response.text}")
                return None

            full_parts = []
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                try:
                    payload = json.loads(line_stripped)
                except json.JSONDecodeError:
                    continue
                token = payload.get("token")
                if not token:
                    continue
                full_parts.append(token)
                if on_token is not None:
                    on_token(token)

            full_text = "".join(full_parts)
            if self.model_name is not None:
                args["model_name"] = self.model_name
            args["result"] = full_text
            with open(Path.generate_log, "a", encoding="utf-8-sig") as file:
                json.dump(args, file, indent=4, ensure_ascii=False)
                file.write("\n")
            return full_text
        except Exception as error:
            print(f"[例外] KoboldCpp.generate_stream(): {error}")
        return None

    def check(self):
        try:
            response = requests.get(self.check_url, timeout=self.ctx["koboldcpp_command_timeout"])
            if response.status_code == 200:
                return response.json()["results"][0]["text"]
            print(f"[失敗] KoboldCpp.check(): {response.text}")
        except Exception:
            pass
        return None

    def abort(self):
        try:
            response = requests.post(self.abort_url, timeout=self.ctx["koboldcpp_command_timeout"])
            if response.status_code == 200:
                return response.json()["success"]
            print(f"[失敗] KoboldCpp.abort(): {response.text}")
        except Exception as error:
            print(f"[例外] KoboldCpp.abort(): {error}")
        return None
