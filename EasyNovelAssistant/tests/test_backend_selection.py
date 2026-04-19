import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from kobold_cpp import build_hypura_command, display_backend_name, normalize_backend_name


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
