import base64
import os
import time

import requests
from job_queue import JobQueue
from path import Path


STABLE_DIFFUSION_WEBUI = "stable_diffusion_webui"
HUGGING_FACE = "huggingface"

IMAGE_PROVIDER_LABELS = {
    STABLE_DIFFUSION_WEBUI: "Stable Diffusion WebUI",
    HUGGING_FACE: "Hugging Face",
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
        return self._generate_stable_diffusion_webui(prompt, source_text)

    def _generate_stable_diffusion_webui(self, prompt, source_text):
        base_url = (self.ctx["image_generation_base_url"] or "http://127.0.0.1:7860").rstrip("/")
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

    def _save_image(self, image_bytes, prompt, source_text, extension):
        os.makedirs(Path.daily_image, exist_ok=True)
        self.image_count += 1
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        name = Path.get_path_name(source_text[:64]) or "image"
        image_path = os.path.join(Path.daily_image, f"{timestamp}-{self.image_count:04d}-{name}{extension}")
        with open(image_path, "wb") as f:
            f.write(image_bytes)

        prompt_path = os.path.splitext(image_path)[0] + ".txt"
        with open(prompt_path, "w", encoding="utf-8-sig") as f:
            f.write("# Prompt\n")
            f.write(prompt)
            f.write("\n\n# Source\n")
            f.write(source_text)
        return image_path

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
