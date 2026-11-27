import argparse
import json
import subprocess
from pathlib import Path


JSON_MERGE_FILES = [
    "EasyNovelAssistant/setup/res/default_llm.json",
    "EasyNovelAssistant/setup/res/default_llm_sequence.json",
    "EasyNovelAssistant/setup/res/default_config.json",
]

TEXT_COPY_IF_MISSING = [
    "Activate-venv.bat",
    "Update-KoboldCpp.bat",
    "Update-KoboldCpp_CUDA12.bat",
    "EasyNovelAssistant/setup/ActivateVirtualEnvironment.bat",
    "EasyNovelAssistant/setup/Setup-Style-Bert-VITS2.bat",
]

REQUIREMENTS_FILE = Path("EasyNovelAssistant/setup/res/requirements.txt")


def git_show(ref, path):
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def load_json_bytes(payload):
    return json.loads(payload.decode("utf-8-sig"))


def load_local_json(path):
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json_if_changed(path, old_data, new_data):
    if old_data == new_data:
        return False
    with Path(path).open("w", encoding="utf-8-sig", newline="\n") as handle:
        json.dump(new_data, handle, ensure_ascii=False, indent=4)
        handle.write("\n")
    return True


def merge_json_file(ref, path):
    upstream = load_json_bytes(git_show(ref, path))
    local = load_local_json(path)
    merged = dict(local)
    added = []
    conflicts = []

    for key, upstream_value in upstream.items():
        if key not in merged:
            merged[key] = upstream_value
            added.append(key)
        elif merged[key] != upstream_value:
            conflicts.append(key)

    changed = write_json_if_changed(path, local, merged)
    return {
        "path": path,
        "changed": changed,
        "added_keys": added,
        "preserved_local_conflicts": conflicts,
        "local_only_keys": sorted(set(local) - set(upstream)),
    }


def copy_if_missing(ref, path):
    target = Path(path)
    if target.exists():
        return {"path": path, "changed": False, "reason": "exists"}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(git_show(ref, path))
    return {"path": path, "changed": True, "reason": "created_from_upstream"}


def bump_requests(requirements_path, version):
    if not requirements_path.exists():
        return {"path": str(requirements_path), "changed": False, "reason": "missing"}

    original = requirements_path.read_text(encoding="utf-8-sig").splitlines()
    updated = []
    changed = False
    found = False
    for line in original:
        if line.startswith("requests=="):
            found = True
            new_line = f"requests=={version}"
            updated.append(new_line)
            changed = changed or (line != new_line)
        else:
            updated.append(line)
    if not found:
        updated.insert(0, f"requests=={version}")
        changed = True

    if changed:
        requirements_path.write_text("\n".join(updated) + "\n", encoding="utf-8-sig")
    return {
        "path": str(requirements_path),
        "changed": changed,
        "requests_version": version,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-ref", default="upstream/main")
    parser.add_argument("--requests-version", default="2.34.2")
    parser.add_argument("--no-security-bump", action="store_true")
    args = parser.parse_args()

    report = {
        "upstream_ref": args.upstream_ref,
        "json_merges": [merge_json_file(args.upstream_ref, path) for path in JSON_MERGE_FILES],
        "created_missing_files": [copy_if_missing(args.upstream_ref, path) for path in TEXT_COPY_IF_MISSING],
    }
    if not args.no_security_bump:
        report["security_bump"] = bump_requests(REQUIREMENTS_FILE, args.requests_version)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
