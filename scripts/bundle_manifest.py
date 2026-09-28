"""Record/verify transferred bundle files, Python ABI and Linux platform."""
import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import sys


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def environment():
    return {"system": platform.system(), "machine": platform.machine(),
            "python_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
            "libc": list(platform.libc_ver())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    root = args.directory.resolve()
    manifest_path = root / "bundle-manifest.json"
    if args.verify:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ("system", "machine", "python_minor"):
            if manifest["environment"][key] != environment()[key]:
                raise RuntimeError(f"Target {key} differs from the bundle build environment")
        for relative, expected in manifest["files"].items():
            path = (root / relative).resolve()
            if not path.is_relative_to(root) or not path.is_file() or digest(path) != expected:
                raise RuntimeError(f"Missing or changed bundle file: {relative}")
        print("Bundle integrity and Python/platform checks passed.")
    else:
        files = {}
        for directory, subdirs, filenames in os.walk(root):
            subdirs[:] = [name for name in subdirs if name not in {".venv", "__pycache__"}]
            for filename in sorted(filenames):
                path = Path(directory) / filename
                if path.is_file() and path != manifest_path:
                    if not path.resolve().is_relative_to(root):
                        raise RuntimeError(f"Bundle contains an external symlink: {path}")
                    files[path.relative_to(root).as_posix()] = digest(path)
        manifest_path.write_text(json.dumps({"schema_version": 1, "environment": environment(), "files": files}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
