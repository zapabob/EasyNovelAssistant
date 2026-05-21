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
