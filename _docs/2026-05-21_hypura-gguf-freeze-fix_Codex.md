# Hypura GGUF attach freeze fix

## Context

Hypura backend selection could make the EasyNovelAssistant UI appear frozen after
choosing a GGUF file. Runtime inspection showed that the Hypura process was
spawned, so the risk was in the Tk callback path rather than only in Hypura
process discovery.

## Root cause

The direct GGUF selection flow still used the KoboldCpp-oriented GPU layer modal
and then launched the backend synchronously from the Tk menu callback. It also
showed a success modal after launch. In Hypura mode those dialogs are not needed
and can leave the user with a blocked or hidden modal while Hypura starts.

## Change

- Skip the GPU layer prompt for Hypura GGUF attach.
- Launch the selected model server from a background thread.
- Keep KoboldCpp's success dialog, but do not show a success modal for Hypura
  attach; Hypura errors still surface through the UI.
- Add regression tests proving Hypura attach does not open the GPU layer dialog
  and KoboldCpp still does.

## Verification

```powershell
python -m pytest EasyNovelAssistant\tests\test_backend_selection.py -q
python -m py_compile EasyNovelAssistant\src\kobold_cpp.py EasyNovelAssistant\src\generator.py EasyNovelAssistant\src\menu\model_menu.py EasyNovelAssistant\src\menu\setting_menu.py
git diff --check
```

Result: all checks passed.

## Follow-up: generation did not start after attach

After the first freeze fix, Hypura launch and EasyNovelAssistant generation
enablement were separated. Hypura also needs time before `/api/v1/model` starts
answering, so the attach flow now waits for that readiness signal before turning
generation on.

Additional hardening:

- Store the direct GGUF attach metadata in `config.json` so a Hypura source path
  can be restored after app restart.
- Recover direct-selected models from that saved attach metadata before falling
  back to the legacy KoboldCpp copied-file lookup.

Additional verification:

```powershell
python -m pytest EasyNovelAssistant\tests\test_backend_selection.py -q
python -m py_compile EasyNovelAssistant\src\kobold_cpp.py EasyNovelAssistant\src\generator.py EasyNovelAssistant\src\menu\model_menu.py EasyNovelAssistant\src\menu\setting_menu.py
git diff --check
```

Result: all checks passed with 20 tests.

## Follow-up: Hypura extraction failed on full C drive

Hypura failed before model startup with PyInstaller-style extraction errors such
as `_decimal.pyd` and `cublas64_12.dll`. The machine had only about `0.04 GB`
free on `C:` and `%TEMP%` pointed at `C:\Users\downl\AppData\Local\Temp`.

Immediate remediation:

- Removed stale `%TEMP%` extraction/build leftovers such as `_MEI*`,
  `go-build*`, `pytest-of-*`, and old temp files.
- Recovered `C:` free space to about `5.21 GB`.

Code hardening:

- Hypura subprocess launches now receive `TEMP`, `TMP`, and `TMPDIR` pointing to
  a dedicated temp directory on a drive with more free space when the default
  temp drive is low.
- On this PC the resolver selects `H:\HypuraTemp`.
- `HYPURA_TEMP_DIR` can override that directory for explicit local setups.

Additional verification:

```powershell
python -m pytest EasyNovelAssistant\tests\test_backend_selection.py -q
python -m py_compile EasyNovelAssistant\src\kobold_cpp.py EasyNovelAssistant\src\generator.py EasyNovelAssistant\src\menu\model_menu.py EasyNovelAssistant\src\menu\setting_menu.py
$env:PYTHONPATH='EasyNovelAssistant\src'; python -c "from kobold_cpp import resolve_hypura_temp_dir; print(resolve_hypura_temp_dir())"
```

Result: all checks passed with 22 tests, and the resolver printed
`H:\HypuraTemp`.
