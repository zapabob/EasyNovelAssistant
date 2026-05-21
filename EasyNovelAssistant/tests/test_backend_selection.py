import json
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DEFAULT_SEQUENCE_PATH = Path(__file__).resolve().parents[1] / "setup" / "res" / "default_llm_sequence.json"

from kobold_cpp import (
    DIRECT_SELECT_PREFIX,
    KoboldCpp,
    apply_sequence_generate_args,
    build_hypura_command,
    clean_generated_text,
    display_backend_name,
    find_sequence_config,
    format_prompt_for_generate,
    normalize_backend_name,
)
from menu.model_menu import ModelMenu, build_local_gguf_model_config, choose_gguf_target_path
from path import Path as AppPath


def load_default_sequences():
    return json.loads(DEFAULT_SEQUENCE_PATH.read_text(encoding="utf-8-sig"))


def test_normalize_backend_name_defaults_to_koboldcpp():
    assert normalize_backend_name(None) == "koboldcpp"
    assert normalize_backend_name("") == "koboldcpp"
    assert normalize_backend_name("invalid") == "koboldcpp"


def test_normalize_backend_name_accepts_hypura():
    assert normalize_backend_name("hypura") == "hypura"
    assert normalize_backend_name("Hypura") == "hypura"


def test_display_backend_name_is_user_facing():
    assert display_backend_name("koboldcpp") == "KoboldCpp"
    assert display_backend_name("hypura") == "Hypura"


def test_build_hypura_command_uses_compat_mode():
    command = build_hypura_command(
        executable="hypura",
        model_path="C:/models/demo.gguf",
        host="127.0.0.1",
        port=5001,
        context_size=8192,
    )

    assert command[:3] == ["hypura", "koboldcpp", "C:/models/demo.gguf"]
    assert command[3:] == ["--host", "127.0.0.1", "--port", "5001", "--context", "8192"]


def test_choose_gguf_target_path_keeps_source_for_hypura(tmp_path):
    model_path = tmp_path / "attached-model.gguf"
    model_path.write_bytes(b"GGUF")

    assert choose_gguf_target_path(str(model_path), model_path.name, "hypura") == str(model_path)


def test_choose_gguf_target_path_uses_kobold_dir_for_koboldcpp(tmp_path, monkeypatch):
    monkeypatch.setattr(AppPath, "kobold_cpp", str(tmp_path / "KoboldCpp"))

    assert choose_gguf_target_path("C:/models/source.gguf", "source.gguf", "koboldcpp") == str(
        tmp_path / "KoboldCpp" / "source.gguf"
    )


def test_build_local_gguf_model_config_records_attached_file_path(tmp_path):
    model_path = tmp_path / "attached-model.gguf"
    config = build_local_gguf_model_config(
        target_path=str(model_path),
        file_name=model_path.name,
        model_name="attached-model",
        gpu_layers=33,
        context_size=8192,
        temporary=True,
    )

    assert config == {
        "max_gpu_layer": 33,
        "context_size": 8192,
        "urls": [f"file://{model_path}"],
        "file_name": "attached-model.gguf",
        "name": "attached-model",
        "local_file": True,
        "temporary": True,
    }


def test_hypura_direct_gguf_does_not_open_gpu_layer_dialog(monkeypatch):
    class DummyBackend:
        backend = "hypura"

    class DummyContext:
        kobold_cpp = DummyBackend()

        def __getitem__(self, key):
            if key == "llm_gpu_layer":
                return 77
            raise KeyError(key)

    class DummyForm:
        win = object()

    def fail_if_opened(*_args, **_kwargs):
        raise AssertionError("Hypura GGUF attach should not ask for KoboldCpp GPU layers")

    monkeypatch.setattr("menu.model_menu.simpledialog.askinteger", fail_if_opened)

    menu = object.__new__(ModelMenu)
    menu.ctx = DummyContext()
    menu.form = DummyForm()

    assert menu._ask_gpu_layers_for_direct_gguf("model.gguf") == 77


def test_koboldcpp_direct_gguf_keeps_gpu_layer_dialog(monkeypatch):
    class DummyBackend:
        backend = "koboldcpp"

    class DummyContext:
        kobold_cpp = DummyBackend()

    class DummyForm:
        win = object()

    monkeypatch.setattr("menu.model_menu.simpledialog.askinteger", lambda *_args, **_kwargs: 41)

    menu = object.__new__(ModelMenu)
    menu.ctx = DummyContext()
    menu.form = DummyForm()

    assert menu._ask_gpu_layers_for_direct_gguf("model.gguf") == 41


def test_direct_gguf_launch_result_enables_generation_without_success_modal(monkeypatch):
    class DummyGenerator:
        enabled = False

    class DummyContext:
        generator = DummyGenerator()

    class DummyForm:
        win = object()

        def __init__(self):
            self.title_updates = 0

        def update_title(self):
            self.title_updates += 1

    monkeypatch.setattr("menu.model_menu.messagebox.showinfo", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("menu.model_menu.messagebox.showerror", lambda *_args, **_kwargs: None)

    menu = object.__new__(ModelMenu)
    menu.ctx = DummyContext()
    menu.form = DummyForm()

    menu._handle_launch_result(None, enable_generation=True)

    assert menu.ctx.generator.enabled is True
    assert menu.form.title_updates == 1


def test_qwen_sequence_matches_local_gguf_names():
    sequences = {
        "QwenChatML": {
            "model_names": ["qwen", "qwen35", "huihui", "elt-lm"],
            "instruct": "<|im_start|>user\n{0}<|im_end|>\n<|im_start|>assistant\n",
            "stop": ["<|im_end|>"],
            "auto_instruct": True,
        }
    }

    sequence = find_sequence_config(
        sequences,
        ["huihui-qwen35-4b-roleplay-unsloth-qlora-q8_0"],
    )

    assert sequence is sequences["QwenChatML"]
    assert format_prompt_for_generate("続きを書いて", sequence).startswith("<|im_start|>user\n")


def test_auto_instruct_does_not_double_wrap_prompt():
    sequence = {
        "model_names": ["qwen"],
        "instruct": "<|im_start|>user\n{0}<|im_end|>\n<|im_start|>assistant\n",
        "stop": ["<|im_end|>"],
        "auto_instruct": True,
    }
    prompt = "<|im_start|>user\n続きを書いて<|im_end|>\n<|im_start|>assistant\n"

    assert format_prompt_for_generate(prompt, sequence) == prompt


def test_qwen_default_sequence_adds_system_guardrails():
    sequence = {
        "model_names": ["qwen"],
        "instruct": (
            "<|im_start|>system\n"
            "本文だけを書いてください。<|im_end|>\n"
            "<|im_start|>user\n{0}<|im_end|>\n"
            "<|im_start|>assistant\n"
        ),
        "stop": ["<|im_end|>"],
        "auto_instruct": True,
    }

    prompt = format_prompt_for_generate("続きを書いて", sequence)

    assert prompt.startswith("<|im_start|>system\n")
    assert "<|im_start|>user\n続きを書いて<|im_end|>" in prompt
    assert prompt.endswith("<|im_start|>assistant\n")


def test_default_qwen_sequence_matches_huihui_and_overrides_sampler():
    sequences = load_default_sequences()
    sequence = find_sequence_config(
        sequences,
        ["huihui-qwen35-4b-roleplay-unsloth-qlora-claude35-15k-ms2048-s110-q8_0.gguf"],
    )

    assert sequence is sequences["QwenChatML"]
    prompt = format_prompt_for_generate("続きを書いて", sequence)
    assert prompt.startswith("<|im_start|>system\n")
    assert "思考過程" in prompt
    assert "<|im_start|>user\n続きを書いて<|im_end|>" in prompt
    assert prompt.endswith("<|im_start|>assistant\n")

    args = {
        "temperature": 0.8,
        "top_p": 1.0,
        "top_k": 100,
        "rep_pen": 1.0,
        "min_p": 0.0,
        "max_length": 3072,
        "unknown": "keep",
    }

    assert apply_sequence_generate_args(args, sequence) == {
        "temperature": 0.55,
        "top_p": 0.9,
        "top_k": 40,
        "rep_pen": 1.08,
        "min_p": 0.02,
        "max_length": 768,
        "unknown": "keep",
    }


def test_sequence_generate_args_override_sampler_defaults():
    args = {"temperature": 0.8, "top_p": 1.0, "unknown": "keep"}
    sequence = {"generate_args": {"temperature": 0.55, "top_p": 0.9, "missing": 1}}

    assert apply_sequence_generate_args(args, sequence) == {
        "temperature": 0.55,
        "top_p": 0.9,
        "unknown": "keep",
    }


def test_clean_generated_text_removes_thinking_block():
    assert clean_generated_text("<think>\nnotes\n</think>\n本文です。") == "本文です。"
    assert clean_generated_text("<think>\nnotes") == ""
    assert clean_generated_text("[Start thinking]\nBody") == "Body"
    assert clean_generated_text("私が書きます：\n\n本文です。") == "本文です。"


def test_koboldcpp_builds_qwen_generate_args_with_guardrails():
    class DummyContext(dict):
        pass

    llm_name = "[local] huihui-qwen35-q8"
    ctx = DummyContext(
        llm_name=llm_name,
        llm_context_size=4096,
        max_length=256,
        rep_pen=1.0,
        rep_pen_range=512,
        rep_pen_slope=0.7,
        temperature=0.8,
        tfs=1.0,
        top_a=0.0,
        top_k=100,
        top_p=1.0,
        typical=1.0,
        min_p=0.0,
        sampler_order=[6, 0, 1, 3, 4, 2, 5],
    )
    ctx.llm = {
        llm_name: {
            "context_size": 4096,
            "file_name": "huihui-qwen35-4b-roleplay-unsloth-qlora-q8_0.gguf",
            "name": "Huihui-Qwen3.5-4B-Claude-4.6-Opus-abliterated",
        }
    }
    ctx.llm_sequence = load_default_sequences()
    kobold = object.__new__(KoboldCpp)
    kobold.ctx = ctx
    kobold.model_name = None

    args = kobold._build_generate_args("続きを書いて")

    assert args["prompt"].startswith("<|im_start|>system\n")
    assert "<|im_start|>assistant\n" in args["prompt"]
    assert args["stop_sequence"] == [
        "<|im_end|>",
        "<|endoftext|>",
        "<|end_of_text|>",
        "<|end|>",
        "<|im_start|>user",
        "<|im_start|>system",
    ]
    assert args["temperature"] == 0.55
    assert args["top_p"] == 0.9
    assert args["top_k"] == 40
    assert args["rep_pen"] == 1.08
    assert args["min_p"] == 0.02
    assert args["max_length"] == 768


def test_koboldcpp_recovers_direct_selected_model_from_copied_gguf(tmp_path, monkeypatch):
    class DummyContext:
        def __init__(self, **kwargs):
            self.cfg = kwargs

        def __getitem__(self, key):
            return self.cfg.get(key)

        def __setitem__(self, key, value):
            self.cfg[key] = value

    model_name = "huihui-qwen35-4b-roleplay-unsloth-qlora-q8_0"
    llm_name = f"[直接選択] {model_name}"
    model_file = tmp_path / f"{model_name}.gguf"
    model_file.write_bytes(b"GGUF")
    monkeypatch.setattr(AppPath, "kobold_cpp", str(tmp_path))

    ctx = DummyContext(llm_name=llm_name, llm_gpu_layer=33)
    ctx.llm = {}
    kobold = object.__new__(KoboldCpp)
    kobold.ctx = ctx
    kobold.model_name = None

    selected_name, llm, error = kobold._ensure_selected_model()

    assert error is None
    assert selected_name == llm_name
    assert llm["file_name"] == f"{model_name}.gguf"
    assert llm["name"] == model_name
    assert llm["local_file"] is True
    assert llm["urls"] == [f"file://{model_file}"]


def test_koboldcpp_recovers_direct_selected_model_from_saved_attach_config(tmp_path):
    class DummyContext:
        def __init__(self, **kwargs):
            self.cfg = kwargs

        def __getitem__(self, key):
            return self.cfg.get(key)

        def __setitem__(self, key, value):
            self.cfg[key] = value

    model_name = "attached-hypura-model"
    llm_name = f"{DIRECT_SELECT_PREFIX}{model_name}"
    model_file = tmp_path / f"{model_name}.gguf"
    model_file.write_bytes(b"GGUF")
    attached_config = build_local_gguf_model_config(
        target_path=str(model_file),
        file_name=model_file.name,
        model_name=model_name,
        gpu_layers=0,
        context_size=4096,
        temporary=True,
    )

    ctx = DummyContext(
        llm_name=llm_name,
        llm_gpu_layer=0,
        direct_gguf_model_name=llm_name,
        direct_gguf_model=attached_config,
    )
    ctx.llm = {}
    kobold = object.__new__(KoboldCpp)
    kobold.ctx = ctx
    kobold.model_name = None

    selected_name, llm, error = kobold._ensure_selected_model()

    assert error is None
    assert selected_name == llm_name
    assert llm["file_name"] == model_file.name
    assert llm["local_file"] is True
    assert llm["urls"] == [f"file://{model_file}"]


def test_koboldcpp_uses_configured_model_name_for_sequence_lookup():
    class DummyContext(dict):
        pass

    ctx = DummyContext(llm_name="[直接選択] supergemma4-e4b")
    ctx.llm = {}
    ctx.llm_sequence = {
        "GemmaChat": {
            "model_names": ["gemma", "supergemma"],
            "instruct": "<start_of_turn>user\n{0}<end_of_turn>\n<start_of_turn>model\n",
            "stop": ["<end_of_turn>"],
            "auto_instruct": True,
        }
    }
    kobold = object.__new__(KoboldCpp)
    kobold.ctx = ctx
    kobold.model_name = None

    assert kobold.get_stop_sequence() == ["<end_of_turn>"]
    assert kobold.formats_prompt_for_generate("続きを書いて")
