# 2026-05-21 Hypura GGUF Attach

## Overview

Added an explicit Hypura GGUF attach path to EasyNovelAssistant's model menu.
When the selected LLM backend is Hypura, GGUF selection keeps the original file
path and launches `hypura koboldcpp <model>` against that path instead of
copying the file into the KoboldCpp directory.

## Background / Requirements

- The user requested a runtime choice between KoboldCpp and Hypura.
- The user requested that choosing Hypura allows attaching a GGUF file.
- Existing branch work already had backend normalization, Hypura launch command
  construction, and direct GGUF selection; this pass tightened the Hypura attach
  behavior and made it test-covered.

## Assumptions / Decisions

- KoboldCpp keeps the existing behavior: GGUF files are copied into
  `KoboldCpp/` when needed.
- Hypura uses the selected source GGUF path directly so large files do not need
  a second copy.
- The persistent `GGUF file add` flow also stores the source path when Hypura is
  selected.

## Changed Files

- `EasyNovelAssistant/src/menu/model_menu.py`
- `EasyNovelAssistant/tests/test_backend_selection.py`
- `README.md`

The branch already contained related backend-selection changes in:

- `EasyNovelAssistant/src/kobold_cpp.py`
- `EasyNovelAssistant/src/generator.py`
- `EasyNovelAssistant/setup/res/default_llm_sequence.json`

## Implementation Details

- Added `choose_gguf_target_path()` so Hypura uses the original file path while
  KoboldCpp uses the KoboldCpp model directory.
- Added `build_local_gguf_model_config()` so temporary and persistent GGUF
  entries record the same local-file shape.
- Changed the model menu label to `GGUF file to Hypura attach` wording when the
  active backend is Hypura.
- Added `name` to generated local GGUF config so sequence lookup can use model
  hints consistently.
- Updated README with the Hypura attach menu path.

## Commands Run

```powershell
python -m pytest EasyNovelAssistant\tests\test_backend_selection.py -q
python -m py_compile EasyNovelAssistant\src\kobold_cpp.py EasyNovelAssistant\src\generator.py EasyNovelAssistant\src\menu\model_menu.py EasyNovelAssistant\src\menu\setting_menu.py
```

## Test / Verification Results

- `pytest`: passed, `16 passed`.
- `py_compile`: passed for the touched Python modules.

## Residual Risks

- Full GUI click-through was not run in this pass.
- Actual Hypura launch still depends on `hypura_path` or `PATH` resolving a
  working `hypura` executable.

## Recommended Next Actions

- Open the app, choose `Settings -> LLM backend -> Hypura`, and attach a local
  GGUF from the model menu for a live smoke test.
