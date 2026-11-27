import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_declares_uv_application_dependencies():
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["name"] == "easy-novel-assistant"
    assert "requests==2.34.2" in project["project"]["dependencies"]
    assert "tkinterdnd2==0.3.0" in project["project"]["dependencies"]
    assert "scipy==1.13.0" in project["project"]["dependencies"]
    assert "watchdog==4.0.0" in project["project"]["dependencies"]
    assert project["dependency-groups"]["dev"] == ["pytest>=9.0.0"]


def test_uv_run_bat_launches_same_app_entrypoint():
    bat_path = PROJECT_ROOT / "Run-EasyNovelAssistant-uv.bat"
    content = bat_path.read_text(encoding="utf-8")

    assert "uv run" in content
    assert "EasyNovelAssistant\\src\\easy_novel_assistant.py" in content


def test_combined_easy_sdxl_uv_launcher_starts_webui_and_app():
    bat_path = PROJECT_ROOT / "Run-EasyNovelAssistant-EasySdxlWebUi-uv.bat"
    content = bat_path.read_text(encoding="utf-8")

    assert "EASY_SDXL_WEBUI_DIR" in content
    assert "H:\\EasySdxlWebUi" in content
    assert "SdxlWebUi-forge.bat" in content
    assert "--api" in content
    assert "uv run python EasyNovelAssistant\\src\\easy_novel_assistant.py" in content


def test_setup_uses_uv_sync_instead_of_requirements_install():
    setup_bat = (PROJECT_ROOT / "EasyNovelAssistant" / "setup" / "Setup-EasyNovelAssistant.bat").read_text(
        encoding="utf-8"
    )
    setup_sh = (PROJECT_ROOT / "EasyNovelAssistant" / "setup" / "Setup-EasyNovelAssistant.sh").read_text(
        encoding="utf-8"
    )

    assert "python -m uv sync --active --no-dev" in setup_bat
    assert "python -m uv sync --active --no-dev" in setup_sh
    assert "pip install -q -r" not in setup_bat
    assert "pip install -r ./EasyNovelAssistant/setup/res/requirements.txt" not in setup_sh


def test_pyproject_uses_current_python_floor():
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["requires-python"] == ">=3.10,<3.13"
