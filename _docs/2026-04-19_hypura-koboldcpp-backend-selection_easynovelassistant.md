# Overview

- EasyNovelAssistant に `KoboldCpp` と `Hypura` のバックエンド切替を追加した。
- Hypura は native API ではなく `hypura koboldcpp <model>` の互換モードで起動する構成にした。
- 生成、途中経過確認、停止は既存の Kobold 互換 HTTP フローをそのまま使う。

# Background / Requirements

- ユーザー要件は「KoboldCpp か Hypura を選べるようにする」ことだった。
- EasyNovelAssistant 側は既存で Kobold 互換 API を前提にしていた。
- Hypura 側にはすでに `/api/v1/model`、`/api/v1/generate`、`/api/extra/generate/check`、`/api/extra/abort` が存在していたため、EasyNovelAssistant は launch 分岐を中心に変更した。

# Assumptions / Decisions

- `llm_backend` は `koboldcpp` または `hypura` の 2 値に正規化する。
- `ctx.kobold_cpp` という既存の参照名は維持し、内部だけ backend-aware にした。
- Hypura 実行ファイルは `hypura_path` があればそれを優先し、なければ `PATH` 上の `hypura` を探す。
- Hypura 選択時も EasyNovelAssistant 側の生成 API 呼び出しは Kobold 互換面を使い続ける。
- 既存の `generator.py` にはローカル変更が入っていたため、その前提を壊さないよう `backend` 属性と `generate_stream()` を維持した。

# Changed Files

- `C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\src\kobold_cpp.py`
- `C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\src\form.py`
- `C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\src\menu\model_menu.py`
- `C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\src\menu\setting_menu.py`
- `C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\setup\res\default_config.json`
- `C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\tests\test_backend_selection.py`
- `C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\README.md`
- `C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\Run-EasyNovelAssistant-HypuraProxy.bat`
- `C:\Users\downl\Desktop\hypura-main\hypura-main\docs\superpowers\specs\2026-04-19-easy-novel-assistant-backend-selection-design.md`
- `C:\Users\downl\Desktop\hypura-main\hypura-main\docs\superpowers\plans\2026-04-19-easy-novel-assistant-backend-selection.md`

# Implementation Details

## Backend helpers

- `normalize_backend_name()` を追加して、無効値や空値を `koboldcpp` に正規化するようにした。
- `display_backend_name()` を追加して UI 表示を一元化した。
- `build_hypura_command()` を追加して `hypura koboldcpp <model> --host --port --context` の起動引数を固定した。

## KoboldCpp facade

- `KoboldCpp` クラスの公開インターフェースは維持した。
- 内部に `set_backend()` と `display_backend_name()` を追加した。
- Hypura 実行ファイルの解決は `hypura_path` -> `PATH` の順にした。
- `launch_server()` は backend に応じて:
  - `koboldcpp.exe` の起動
  - `hypura koboldcpp` の起動
  を切り替えるようにした。
- 生成と停止のエンドポイントは両方とも Kobold 互換面のままにした。

## Settings UI

- `設定` メニューに `LLMバックエンド` のラジオ選択を追加した。
- `Hypura 実行ファイル` の入力項目を追加した。
- タイトルバーに現在のバックエンド表示を追加した。

## Model handling

- モデルメニューの存在確認を `local_file` の絶対パスにも対応させた。
- GGUF 直接選択では、Hypura 選択時に元ファイルをそのまま参照するようにした。

## Docs

- README にバックエンド切替の説明を追加した。
- 既存の proxy launcher は削除せず、今は legacy optional flow である旨を追記した。

# Commands Run

- `py -3 -m pytest C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\tests\test_backend_selection.py -v`
- `py -3 -m py_compile C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\src\kobold_cpp.py C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\src\form.py C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\src\menu\setting_menu.py C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\src\menu\model_menu.py`
- `C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'C:\Users\downl\Desktop\EasyNovelAssistant\EasyNovelAssistant\EasyNovelAssistant\src'); import easy_novel_assistant; print('import-ok')"`
- `C:\Users\downl\Desktop\hypura-main\hypura-main\target\debug\hypura.exe koboldcpp --help`

# Test / Verification Results

- `pytest`: PASS
  - 4 tests passed
  - covered backend normalization, backend label mapping, and Hypura compat command generation
- `py_compile`: PASS
  - modified Python files compiled successfully
- app import smoke check with EasyNovelAssistant venv: PASS
  - `import easy_novel_assistant` succeeded when using the project venv
- Hypura CLI compat help: PASS
  - confirmed `hypura koboldcpp` supports `<MODEL>`, `--host`, `--port`, and `--context`

# Residual Risks

- Full GUI runtime smoke was not executed in this session, so actual menu interaction and end-to-end live generation against a real model remain manually unverified.
- The EasyNovelAssistant repository already had unrelated local changes:
  - `EasyNovelAssistant/src/generator.py`
  - `KoboldCpp/koboldcpp.py` deletion
  - `config.json`
  - `20260404_161422.txt`
  - `EasyNovelAssistant/src/kobold._cpp.py`
  These were not reverted or normalized here.
- Hypura launch success still depends on the user having a valid `hypura.exe` path or `PATH` entry.

# Recommended Next Actions

- Open EasyNovelAssistant and switch `設定 -> LLMバックエンド` between `KoboldCpp` and `Hypura`.
- For Hypura mode, set `設定 -> Hypura 実行ファイル` to the desired `hypura.exe` if `PATH` does not already resolve it.
- Run one live generation in each backend mode and confirm:
  - model launch
  - partial output rendering
  - stop / abort behavior
