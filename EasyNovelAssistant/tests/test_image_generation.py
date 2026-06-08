import base64
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from image_manager import HUGGING_FACE, STABLE_DIFFUSION_WEBUI, ImageManager, normalize_image_provider
from path import Path as AppPath


class DummyContext(dict):
    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)


def image_context(**overrides):
    values = {
        "auto_image_generation": True,
        "image_generation_provider": STABLE_DIFFUSION_WEBUI,
        "image_generation_base_url": "http://127.0.0.1:7860",
        "huggingface_image_model": "stabilityai/stable-diffusion-xl-base-1.0",
        "huggingface_image_endpoint_url": "",
        "huggingface_image_token_env": "HF_TOKEN",
        "image_generation_timeout": 120,
        "image_generation_width": 1024,
        "image_generation_height": 1024,
        "image_generation_steps": 25,
        "image_generation_cfg_scale": 7.0,
        "image_generation_sampler": "",
        "image_generation_seed": -1,
        "image_generation_negative_prompt": "",
        "image_generation_prompt_template": "illustration: {text} / {char_name} / {user_name}",
        "image_generation_context_chars": 1000,
        "auto_image_generation_lines": 2,
        "auto_image_generation_min_chars": 240,
        "max_image_generation_queue": 1,
        "char_name": "Alice",
        "user_name": "Bob",
    }
    values.update(overrides)
    return DummyContext(values)


def manager_for(ctx):
    manager = object.__new__(ImageManager)
    manager.ctx = ctx
    manager.pending_lines = []
    manager.image_count = 0
    return manager


def test_normalize_image_provider_defaults_to_stable_diffusion_webui():
    assert normalize_image_provider(None) == STABLE_DIFFUSION_WEBUI
    assert normalize_image_provider("") == STABLE_DIFFUSION_WEBUI
    assert normalize_image_provider("invalid") == STABLE_DIFFUSION_WEBUI


def test_normalize_image_provider_accepts_huggingface():
    assert normalize_image_provider(HUGGING_FACE) == HUGGING_FACE


def test_image_prompt_template_receives_story_and_names():
    manager = manager_for(image_context())

    assert manager.build_prompt("A quiet room.") == "illustration: A quiet room. / Alice / Bob"


def test_collect_triggers_after_configured_line_count(monkeypatch):
    manager = manager_for(image_context(auto_image_generation_lines=2, auto_image_generation_min_chars=9999))
    generated = []
    monkeypatch.setattr(manager, "generate", lambda text, force=False: generated.append((text, force)) or True)

    assert manager.collect("first line") is False
    assert manager.collect("second line") is True

    assert generated == [("first line\nsecond line", False)]
    assert manager.pending_lines == []


def test_stable_diffusion_webui_payload_and_image_save(tmp_path, monkeypatch):
    ctx = image_context(image_generation_sampler="Euler a", image_generation_seed=42)
    manager = manager_for(ctx)
    monkeypatch.setattr(AppPath, "daily_image", str(tmp_path))

    captured = {}
    image_b64 = base64.b64encode(b"\x89PNG\r\n\x1a\nfake").decode("ascii")

    class FakeResponse:
        status_code = 200
        text = "ok"

        def json(self):
            return {"images": [image_b64]}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["payload"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("image_manager.requests.post", fake_post)

    paths = manager._generate_stable_diffusion_webui("prompt text", "source text")

    assert captured["url"] == "http://127.0.0.1:7860/sdapi/v1/txt2img"
    assert captured["payload"]["prompt"] == "prompt text"
    assert captured["payload"]["width"] == 1024
    assert captured["payload"]["height"] == 1024
    assert captured["payload"]["sampler_name"] == "Euler a"
    assert captured["payload"]["seed"] == 42
    assert captured["timeout"] == 120
    assert len(paths) == 1
    assert Path(paths[0]).read_bytes() == b"\x89PNG\r\n\x1a\nfake"
    assert Path(paths[0]).with_suffix(".txt").read_text(encoding="utf-8-sig").startswith("# Prompt\nprompt text")


def test_huggingface_payload_and_image_save(tmp_path, monkeypatch):
    ctx = image_context(
        image_generation_provider=HUGGING_FACE,
        huggingface_image_endpoint_url="https://example.test/models/demo",
    )
    manager = manager_for(ctx)
    monkeypatch.setattr(AppPath, "daily_image", str(tmp_path))
    monkeypatch.setenv("HF_TOKEN", "hf_test")

    captured = {}

    class FakeResponse:
        status_code = 200
        text = ""
        content = b"\x89PNG\r\n\x1a\nhf"
        headers = {"content-type": "image/png"}

    def fake_post(endpoint_url, headers, json, timeout):
        captured["endpoint_url"] = endpoint_url
        captured["headers"] = headers
        captured["payload"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("image_manager.requests.post", fake_post)

    paths = manager._generate_huggingface("prompt text", "source text")

    assert captured["endpoint_url"] == "https://example.test/models/demo"
    assert captured["headers"]["Authorization"] == "Bearer hf_test"
    assert captured["payload"]["inputs"] == "prompt text"
    assert captured["payload"]["parameters"]["num_inference_steps"] == 25
    assert captured["timeout"] == 120
    assert len(paths) == 1
    assert Path(paths[0]).read_bytes() == b"\x89PNG\r\n\x1a\nhf"
