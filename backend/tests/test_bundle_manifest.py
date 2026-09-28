"""Bundle transfer must detect missing/altered files and wrong target ABI."""
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from scripts.bundle_manifest import main


def test_bundle_manifest_detects_mutation_and_python_mismatch():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        asset = root / "wheelhouse" / "local.whl"
        asset.parent.mkdir()
        asset.write_bytes(b"offline dependency bytes")
        with patch.object(sys, "argv", ["bundle_manifest.py", str(root)]):
            main()
        with patch.object(sys, "argv", ["bundle_manifest.py", str(root), "--verify"]):
            main()
        manifest = root / "bundle-manifest.json"
        record = json.loads(manifest.read_text(encoding="utf-8"))
        record["environment"]["python_minor"] = "0.0"
        manifest.write_text(json.dumps(record), encoding="utf-8")
        with patch.object(sys, "argv", ["bundle_manifest.py", str(root), "--verify"]), pytest.raises(RuntimeError, match="python_minor"):
            main()
        record["environment"]["python_minor"] = f"{sys.version_info.major}.{sys.version_info.minor}"
        manifest.write_text(json.dumps(record), encoding="utf-8")
        asset.write_bytes(b"tampered")
        with patch.object(sys, "argv", ["bundle_manifest.py", str(root), "--verify"]), pytest.raises(RuntimeError, match="changed bundle file"):
            main()
