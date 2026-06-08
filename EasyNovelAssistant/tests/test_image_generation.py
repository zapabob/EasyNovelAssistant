import base64
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from image_manager import (
    HUGGING_FACE,
    STABLE_DIFFUSION_CPP,
    STABLE_DIFFUSION_WEBUI,
    ImageManager,
    normalize_image_provider,
)
from path import Path as AppPath


EASY_SDXL_WEBUI = "easy_sdxl_webui"


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
        "easy_sdxl_webui_mode": "forge",
        "easy_sdxl_webui_forge_bat": "C:/EasySdxlWebUi/SdxlWebUi-forge.bat",
        "easy_sdxl_webui_a1111_bat": "C:/EasySdxlWebUi/SdxlWebUi-a1111.bat",
        "easy_sdxl_webui_extra_args": "--theme dark",
        "huggingface_image_model": "stabilityai/stable-diffusion-xl-base-1.0",
        "huggingface_image_endpoint_url": "",
        "huggingface_image_token_env": "HF_TOKEN",
        "stable_diffusion_cpp_executable": "sd-cli",
        "stable_diffusion_cpp_model": "",
        "stable_diffusion_cpp_diffusion_model": "",
        "stable_diffusion_cpp_vae": "",
        "stable_diffusion_cpp_clip_l": "",
        "stable_diffusion_cpp_clip_g": "",
        "stable_diffusion_cpp_t5xxl": "",
        "stable_diffusion_cpp_llm": "",
        "stable_diffusion_cpp_threads": -1,
        "stable_diffusion_cpp_extra_args": "",
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


def test_normalize_image_provider_accepts_stable_diffusion_cpp():
    assert normalize_image_provider(STABLE_DIFFUSION_CPP) == STABLE_DIFFUSION_CPP


def test_normalize_image_provider_accepts_easy_sdxl_webui():
    assert normalize_image_provider(EASY_SDXL_WEBUI) == EASY_SDXL_WEBUI


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


def test_easy_sdxl_webui_generation_reuses_webui_api(monkeypatch):
    ctx = image_context(image_generation_provider=EASY_SDXL_WEBUI)
    manager = manager_for(ctx)
    generated = []
    monkeypatch.setattr(
        manager,
        "_generate_stable_diffusion_webui",
        lambda prompt, source_text: generated.append((prompt, source_text)) or ["image.png"],
    )

    assert manager._generate("prompt text", "source text") == ["image.png"]
    assert generated == [("prompt text", "source text")]


def test_build_easy_sdxl_webui_launch_command_adds_api_and_extra_args():
    manager = manager_for(image_context())

    command, error = manager.build_easy_sdxl_webui_launch_command()

    assert error is None
    assert command[:4] == ["cmd.exe", "/c", "call", "C:/EasySdxlWebUi/SdxlWebUi-forge.bat"]
    assert command[4:] == ["--api", "--theme", "dark"]


def test_build_easy_sdxl_webui_launch_command_uses_a1111_mode():
    manager = manager_for(image_context(easy_sdxl_webui_mode="a1111", easy_sdxl_webui_extra_args="--skip-torch-cuda-test"))

    command, error = manager.build_easy_sdxl_webui_launch_command()

    assert error is None
    assert command[:4] == ["cmd.exe", "/c", "call", "C:/EasySdxlWebUi/SdxlWebUi-a1111.bat"]
    assert command[4:] == ["--api", "--skip-torch-cuda-test"]


def test_check_easy_sdxl_webui_status_reads_options(monkeypatch):
    manager = manager_for(image_context())
    captured = {}

    class FakeResponse:
        status_code = 200
        text = "ok"

        def json(self):
            return {"sd_model_checkpoint": "animagine.safetensors"}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("image_manager.requests.get", fake_get)

    status = manager.check_easy_sdxl_webui_status()

    assert status["ok"] is True
    assert status["model"] == "animagine.safetensors"
    assert captured["url"] == "http://127.0.0.1:7860/sdapi/v1/options"
    assert captured["timeout"] == 120


def test_list_easy_sdxl_webui_models(monkeypatch):
    manager = manager_for(image_context())

    class FakeResponse:
        status_code = 200
        text = "ok"

        def json(self):
            return [
                {"title": "animagine-xl-3.1.safetensors"},
                {"model_name": "ponyDiffusionV6XL"},
            ]

    monkeypatch.setattr("image_manager.requests.get", lambda *_args, **_kwargs: FakeResponse())

    assert manager.list_easy_sdxl_webui_models() == ["animagine-xl-3.1.safetensors", "ponyDiffusionV6XL"]


def test_easy_sdxl_webui_progress(monkeypatch):
    manager = manager_for(image_context())

    class FakeResponse:
        status_code = 200
        text = "ok"

        def json(self):
            return {"progress": 0.5, "eta_relative": 12.3, "state": {"job": "txt2img"}}

    monkeypatch.setattr("image_manager.requests.get", lambda *_args, **_kwargs: FakeResponse())

    assert manager.easy_sdxl_webui_progress() == {"progress": 0.5, "eta_relative": 12.3, "job": "txt2img"}


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


def test_stable_diffusion_cpp_command_and_image_save(tmp_path, monkeypatch):
    ctx = image_context(
        image_generation_provider=STABLE_DIFFUSION_CPP,
        image_generation_sampler="Euler a",
        image_generation_seed=123,
        stable_diffusion_cpp_executable="C:/tools/sd-cli.exe",
        stable_diffusion_cpp_diffusion_model="C:/models/flux-q4.gguf",
        stable_diffusion_cpp_vae="C:/models/ae.safetensors",
        stable_diffusion_cpp_clip_l="C:/models/clip_l.safetensors",
        stable_diffusion_cpp_t5xxl="C:/models/t5xxl_fp16.safetensors",
        stable_diffusion_cpp_threads=6,
        stable_diffusion_cpp_extra_args="--vae-tiling --rng cpu",
    )
    manager = manager_for(ctx)
    monkeypatch.setattr(AppPath, "daily_image", str(tmp_path))

    captured = {}

    class FakeResult:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        output_path = Path(command[command.index("-o") + 1])
        output_path.write_bytes(b"\x89PNG\r\n\x1a\nlocal")
        return FakeResult()

    monkeypatch.setattr("image_manager.subprocess.run", fake_run)

    paths = manager._generate_stable_diffusion_cpp("prompt text", "source text")

    assert captured["command"][:4] == ["C:/tools/sd-cli.exe", "-M", "img_gen", "-p"]
    assert captured["command"][captured["command"].index("--diffusion-model") + 1] == "C:/models/flux-q4.gguf"
    assert captured["command"][captured["command"].index("--vae") + 1] == "C:/models/ae.safetensors"
    assert captured["command"][captured["command"].index("--clip_l") + 1] == "C:/models/clip_l.safetensors"
    assert captured["command"][captured["command"].index("--t5xxl") + 1] == "C:/models/t5xxl_fp16.safetensors"
    assert captured["command"][captured["command"].index("--sampling-method") + 1] == "euler_a"
    assert captured["command"][captured["command"].index("-s") + 1] == "123"
    assert captured["command"][captured["command"].index("-t") + 1] == "6"
    assert "--vae-tiling" in captured["command"]
    assert "--rng" in captured["command"]
    assert captured["kwargs"]["timeout"] == 120
    assert len(paths) == 1
    assert Path(paths[0]).read_bytes() == b"\x89PNG\r\n\x1a\nlocal"
    assert Path(paths[0]).with_suffix(".txt").read_text(encoding="utf-8-sig").startswith("# Prompt\nprompt text")


def test_stable_diffusion_cpp_requires_model_path(monkeypatch):
    ctx = image_context(image_generation_provider=STABLE_DIFFUSION_CPP)
    manager = manager_for(ctx)

    def fail_if_run(*_args, **_kwargs):
        raise AssertionError("stable-diffusion.cpp should not run without a model path")

    monkeypatch.setattr("image_manager.subprocess.run", fail_if_run)

    assert manager._generate_stable_diffusion_cpp("prompt text", "source text") is None


def test_stable_diffusion_cpp_extra_args_strip_quotes_on_windows():
    manager = manager_for(image_context())

    args = manager._split_extra_args('--lora-model-dir "C:/models/my lora" --rng cpu')

    assert args == ["--lora-model-dir", "C:/models/my lora", "--rng", "cpu"]
