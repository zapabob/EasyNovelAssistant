import base64
import os
import shlex
import subprocess
import time

import requests
from job_queue import JobQueue
from path import Path


STABLE_DIFFUSION_WEBUI = "stable_diffusion_webui"
EASY_SDXL_WEBUI = "easy_sdxl_webui"
HUGGING_FACE = "huggingface"
STABLE_DIFFUSION_CPP = "stable_diffusion_cpp"

IMAGE_PROVIDER_LABELS = {
    STABLE_DIFFUSION_WEBUI: "Stable Diffusion WebUI",
    EASY_SDXL_WEBUI: "EasySdxlWebUi",
    HUGGING_FACE: "Hugging Face",
    STABLE_DIFFUSION_CPP: "ローカル GGUF (stable-diffusion.cpp)",
}


def normalize_image_provider(provider):
    if provider in IMAGE_PROVIDER_LABELS:
        return provider
    return STABLE_DIFFUSION_WEBUI


class ImageManager:
    def __init__(self, ctx):
        self.ctx = ctx
        self.gen_queue = JobQueue()
        self.pending_lines = []
        self.image_count = 0

    def update(self):
        self.gen_queue.update()

    def abort(self):
        self.pending_lines = []
        self.gen_queue.cancel_all()

    def collect(self, text):
        if not self.ctx["auto_image_generation"]:
            return False

        text = self._clean_text(text)
        if text == "":
            return False

        self.pending_lines.append(text)
        pending_text = self._pending_text()
        interval_lines = self._int_config("auto_image_generation_lines", 6)
        min_chars = self._int_config("auto_image_generation_min_chars", 240)

        if len(self.pending_lines) >= interval_lines or len(pending_text) >= min_chars:
            self.pending_lines = []
            return self.generate(pending_text)
        return False

    def flush(self):
        pending_text = self._pending_text()
        self.pending_lines = []
        if pending_text == "":
            return False
        return self.generate(pending_text, force=True)

    def generate(self, story_text, force=False):
        story_text = self._clean_text(story_text)
        if story_text == "":
            return False

        max_queue = self._int_config("max_image_generation_queue", 1)
        if (not force) and self.gen_queue.len() >= max_queue:
            print(f"[Info] Image generation queue is busy. Canceled image generation: {story_text[:80]}")
            return False

        prompt = self.build_prompt(story_text)
        self.gen_queue.push(self._generate, prompt=prompt, source_text=story_text)
        return True

    def build_prompt(self, story_text):
        story_text = self._trim_context(self._clean_text(story_text))
        template = self.ctx["image_generation_prompt_template"] or "{text}"
        try:
            return template.format(
                text=story_text,
                char_name=self.ctx["char_name"],
                user_name=self.ctx["user_name"],
            )
        except Exception:
            return f"{template}\n{story_text}"

    def provider_label(self):
        provider = normalize_image_provider(self.ctx["image_generation_provider"])
        if provider != self.ctx["image_generation_provider"]:
            self.ctx["image_generation_provider"] = provider
        return IMAGE_PROVIDER_LABELS[provider]

    def _generate(self, prompt, source_text):
        provider = normalize_image_provider(self.ctx["image_generation_provider"])
        if provider == HUGGING_FACE:
            return self._generate_huggingface(prompt, source_text)
        if provider == STABLE_DIFFUSION_CPP:
            return self._generate_stable_diffusion_cpp(prompt, source_text)
        if provider == EASY_SDXL_WEBUI:
            return self._generate_easy_sdxl_webui(prompt, source_text)
        return self._generate_stable_diffusion_webui(prompt, source_text)

    def _generate_easy_sdxl_webui(self, prompt, source_text):
        return self._generate_stable_diffusion_webui(prompt, source_text)

    def _generate_stable_diffusion_webui(self, prompt, source_text):
        base_url = self._image_base_url()
        url = f"{base_url}/sdapi/v1/txt2img"
        payload = {
            "prompt": prompt,
            "negative_prompt": self.ctx["image_generation_negative_prompt"] or "",
            "width": self._int_config("image_generation_width", 1024),
            "height": self._int_config("image_generation_height", 1024),
            "steps": self._int_config("image_generation_steps", 25),
            "cfg_scale": self._float_config("image_generation_cfg_scale", 7.0),
        }

        sampler = self.ctx["image_generation_sampler"]
        if sampler:
            payload["sampler_name"] = sampler

        seed = self._int_config("image_generation_seed", -1)
        if seed >= 0:
            payload["seed"] = seed

        try:
            response = requests.post(url, json=payload, timeout=self._int_config("image_generation_timeout", 120))
            if response.status_code != 200:
                print(f"[Failed] ImageManager.generate(): {response.text}")
                return None

            data = response.json()
            paths = []
            for image in data.get("images", []):
                image_data = image.split(",", 1)[-1]
                paths.append(self._save_image(base64.b64decode(image_data), prompt, source_text, ".png"))
            if len(paths) == 0:
                print("[Failed] ImageManager.generate(): response did not contain images")
                return None
            print(f"Image generation: {paths[0]}")
            return paths
        except Exception as e:
            print(f"[Exception] ImageManager.generate(): {e}")
        return None

    def _generate_huggingface(self, prompt, source_text):
        endpoint_url = self.ctx["huggingface_image_endpoint_url"]
        if not endpoint_url:
            model = self.ctx["huggingface_image_model"] or "stabilityai/stable-diffusion-xl-base-1.0"
            endpoint_url = f"https://api-inference.huggingface.co/models/{model}"

        headers = {"accept": "image/png"}
        token = self._huggingface_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": self.ctx["image_generation_negative_prompt"] or "",
                "width": self._int_config("image_generation_width", 1024),
                "height": self._int_config("image_generation_height", 1024),
                "num_inference_steps": self._int_config("image_generation_steps", 25),
                "guidance_scale": self._float_config("image_generation_cfg_scale", 7.0),
            },
        }

        seed = self._int_config("image_generation_seed", -1)
        if seed >= 0:
            payload["parameters"]["seed"] = seed

        try:
            response = requests.post(
                endpoint_url,
                headers=headers,
                json=payload,
                timeout=self._int_config("image_generation_timeout", 120),
            )
            content_type = response.headers.get("content-type", "")
            if response.status_code != 200:
                print(f"[Failed] Hugging Face image generation: {response.text}")
                return None
            if "application/json" in content_type:
                print(f"[Failed] Hugging Face image generation: {response.text}")
                return None

            path = self._save_image(response.content, prompt, source_text, ".png")
            print(f"Hugging Face image generation: {path}")
            return [path]
        except Exception as e:
            print(f"[Exception] Hugging Face image generation: {e}")
        return None

    def build_easy_sdxl_webui_launch_command(self):
        bat_path = self._easy_sdxl_webui_bat_path()
        if bat_path == "":
            return [], "EasySdxlWebUiの起動batパスを設定してください。"

        extra_args = self._split_extra_args(self.ctx["easy_sdxl_webui_extra_args"])
        if extra_args is None:
            return [], "EasySdxlWebUi追加引数の引用符が正しくありません。"
        if not any(str(arg).lower() == "--api" for arg in extra_args):
            extra_args = ["--api"] + extra_args

        if os.name == "nt":
            return ["cmd.exe", "/c", "call", bat_path] + extra_args, None
        return [bat_path] + extra_args, None

    def launch_easy_sdxl_webui(self):
        command, error = self.build_easy_sdxl_webui_launch_command()
        if error:
            print(f"[Failed] EasySdxlWebUi launch: {error}")
            return False

        cwd = os.path.dirname(self._easy_sdxl_webui_bat_path()) or None
        try:
            kwargs = {"cwd": cwd}
            if os.name == "nt":
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            subprocess.Popen(command, **kwargs)
            print(f"EasySdxlWebUi launch: {' '.join(command)}")
            return True
        except Exception as e:
            print(f"[Exception] EasySdxlWebUi launch: {e}")
        return False

    def check_easy_sdxl_webui_status(self):
        url = f"{self._image_base_url()}/sdapi/v1/options"
        try:
            response = requests.get(url, timeout=self._int_config("image_generation_timeout", 120))
            if response.status_code != 200:
                return {"ok": False, "error": response.text}
            data = response.json()
            return {"ok": True, "model": data.get("sd_model_checkpoint", ""), "options": data}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def list_easy_sdxl_webui_models(self):
        url = f"{self._image_base_url()}/sdapi/v1/sd-models"
        try:
            response = requests.get(url, timeout=self._int_config("image_generation_timeout", 120))
            if response.status_code != 200:
                print(f"[Failed] EasySdxlWebUi models: {response.text}")
                return []
            models = []
            for item in response.json():
                model = item.get("title") or item.get("model_name") or item.get("filename")
                if model:
                    models.append(model)
            return models
        except Exception as e:
            print(f"[Exception] EasySdxlWebUi models: {e}")
        return []

    def easy_sdxl_webui_progress(self):
        url = f"{self._image_base_url()}/sdapi/v1/progress"
        try:
            response = requests.get(url, timeout=self._int_config("image_generation_timeout", 120))
            if response.status_code != 200:
                return {"progress": 0.0, "eta_relative": 0.0, "job": "", "error": response.text}
            data = response.json()
            state = data.get("state") or {}
            return {
                "progress": data.get("progress", 0.0),
                "eta_relative": data.get("eta_relative", 0.0),
                "job": state.get("job", ""),
            }
        except Exception as e:
            return {"progress": 0.0, "eta_relative": 0.0, "job": "", "error": str(e)}

    def _easy_sdxl_webui_bat_path(self):
        mode = (self.ctx["easy_sdxl_webui_mode"] or "forge").lower()
        key = "easy_sdxl_webui_a1111_bat" if mode == "a1111" else "easy_sdxl_webui_forge_bat"
        bat_path = self.ctx[key]
        if bat_path:
            return bat_path
        return self._find_easy_sdxl_webui_bat(mode)

    def _find_easy_sdxl_webui_bat(self, mode):
        file_name = f"SdxlWebUi-{mode}.bat"
        roots = [
            os.getcwd(),
            os.path.dirname(os.getcwd()),
            os.path.join(os.getcwd(), "EasySdxlWebUi"),
            os.path.join(os.path.dirname(os.getcwd()), "EasySdxlWebUi"),
        ]
        for root in roots:
            candidate = os.path.join(root, file_name)
            if os.path.exists(candidate):
                return candidate
        return ""

    def _generate_stable_diffusion_cpp(self, prompt, source_text):
        output_path = self._next_image_path(source_text, ".png")
        command, error = self._build_stable_diffusion_cpp_command(prompt, output_path)
        if error:
            print(f"[Failed] stable-diffusion.cpp image generation: {error}")
            return None

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self._int_config("image_generation_timeout", 120),
            )
        except subprocess.TimeoutExpired:
            print("[Failed] stable-diffusion.cpp image generation: timeout")
            return None
        except Exception as e:
            print(f"[Exception] stable-diffusion.cpp image generation: {e}")
            return None

        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            print(f"[Failed] stable-diffusion.cpp image generation: {detail}")
            return None

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            detail = (result.stderr or result.stdout or "").strip()
            print(f"[Failed] stable-diffusion.cpp image generation: output was not written. {detail}")
            return None

        self._save_prompt_sidecar(output_path, prompt, source_text)
        print(f"stable-diffusion.cpp image generation: {output_path}")
        return [output_path]

    def _build_stable_diffusion_cpp_command(self, prompt, output_path):
        executable = self.ctx["stable_diffusion_cpp_executable"] or "sd-cli"
        model = self.ctx["stable_diffusion_cpp_model"]
        diffusion_model = self.ctx["stable_diffusion_cpp_diffusion_model"]
        if not model and not diffusion_model:
            return [], "モデルまたはdiffusionモデルのパスを設定してください。"

        command = [
            executable,
            "-M",
            "img_gen",
            "-p",
            prompt,
            "-n",
            self.ctx["image_generation_negative_prompt"] or "",
            "-W",
            str(self._int_config("image_generation_width", 1024)),
            "-H",
            str(self._int_config("image_generation_height", 1024)),
            "--steps",
            str(self._int_config("image_generation_steps", 25)),
            "--cfg-scale",
            str(self._float_config("image_generation_cfg_scale", 7.0)),
            "-o",
            output_path,
        ]

        if model:
            command.extend(["-m", model])
        if diffusion_model:
            command.extend(["--diffusion-model", diffusion_model])

        for key, option in (
            ("stable_diffusion_cpp_vae", "--vae"),
            ("stable_diffusion_cpp_clip_l", "--clip_l"),
            ("stable_diffusion_cpp_clip_g", "--clip_g"),
            ("stable_diffusion_cpp_t5xxl", "--t5xxl"),
            ("stable_diffusion_cpp_llm", "--llm"),
        ):
            value = self.ctx[key]
            if value:
                command.extend([option, value])

        sampler = self._stable_diffusion_cpp_sampler(self.ctx["image_generation_sampler"])
        if sampler:
            command.extend(["--sampling-method", sampler])

        seed = self._int_config("image_generation_seed", -1)
        if seed >= 0:
            command.extend(["-s", str(seed)])

        threads = self._int_config("stable_diffusion_cpp_threads", -1)
        if threads > 0:
            command.extend(["-t", str(threads)])

        extra_args = self._split_extra_args(self.ctx["stable_diffusion_cpp_extra_args"])
        if extra_args is None:
            return [], "追加CLI引数の引用符が正しくありません。"
        command.extend(extra_args)
        return command, None

    def _stable_diffusion_cpp_sampler(self, sampler):
        sampler = self._clean_text(sampler).lower()
        if sampler == "":
            return ""
        known = {
            "euler a": "euler_a",
            "euler_a": "euler_a",
            "euler": "euler",
            "heun": "heun",
            "dpm2": "dpm2",
            "dpm++ 2s a": "dpm++2s_a",
            "dpm++2s a": "dpm++2s_a",
            "dpm++ 2m": "dpm++2m",
            "dpm++2m": "dpm++2m",
            "dpm++ 2m v2": "dpm++2mv2",
            "dpm++2m v2": "dpm++2mv2",
            "lcm": "lcm",
        }
        return known.get(sampler, sampler.replace(" ", "_"))

    def _split_extra_args(self, extra_args):
        extra_args = self._clean_text(extra_args)
        if extra_args == "":
            return []
        if os.name == "nt":
            return self._split_windows_args(extra_args)
        try:
            return shlex.split(extra_args, posix=True)
        except ValueError:
            return None

    def _split_windows_args(self, extra_args):
        try:
            import ctypes
            from ctypes import wintypes

            argc = ctypes.c_int()
            command_line_to_argv = ctypes.windll.shell32.CommandLineToArgvW
            command_line_to_argv.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
            command_line_to_argv.restype = ctypes.POINTER(wintypes.LPWSTR)
            local_free = ctypes.windll.kernel32.LocalFree
            local_free.argtypes = [wintypes.HLOCAL]
            local_free.restype = wintypes.HLOCAL

            argv = command_line_to_argv(extra_args, ctypes.byref(argc))
            if not argv:
                return None
            try:
                return [argv[i] for i in range(argc.value)]
            finally:
                local_free(argv)
        except Exception:
            return None

    def _save_image(self, image_bytes, prompt, source_text, extension):
        image_path = self._next_image_path(source_text, extension)
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        self._save_prompt_sidecar(image_path, prompt, source_text)
        return image_path

    def _image_base_url(self):
        return (self.ctx["image_generation_base_url"] or "http://127.0.0.1:7860").rstrip("/")

    def _next_image_path(self, source_text, extension):
        os.makedirs(Path.daily_image, exist_ok=True)
        self.image_count += 1
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        name = Path.get_path_name(source_text[:64]) or "image"
        return os.path.join(Path.daily_image, f"{timestamp}-{self.image_count:04d}-{name}{extension}")

    def _save_prompt_sidecar(self, image_path, prompt, source_text):
        prompt_path = os.path.splitext(image_path)[0] + ".txt"
        with open(prompt_path, "w", encoding="utf-8-sig") as f:
            f.write("# Prompt\n")
            f.write(prompt)
            f.write("\n\n# Source\n")
            f.write(source_text)

    def _pending_text(self):
        return self._trim_context("\n".join(self.pending_lines))

    def _trim_context(self, text):
        max_chars = self._int_config("image_generation_context_chars", 1000)
        if max_chars <= 0 or len(text) <= max_chars:
            return text
        return text[-max_chars:]

    def _clean_text(self, text):
        if text is None:
            return ""
        return str(text).strip()

    def _huggingface_token(self):
        env_name = self.ctx["huggingface_image_token_env"] or "HF_TOKEN"
        for name in (env_name, "HF_TOKEN", "HUGGINGFACEHUB_API_TOKEN"):
            token = os.environ.get(name)
            if token:
                return token
        return ""

    def _int_config(self, key, default):
        try:
            return int(self.ctx[key])
        except (TypeError, ValueError):
            return default

    def _float_config(self, key, default):
        try:
            return float(self.ctx[key])
        except (TypeError, ValueError):
            return default
