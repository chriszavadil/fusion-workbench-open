#!/usr/bin/env python3
"""Expand the frozen MAST vertical-challenge cohort source bundle."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path

EXPECTED_BUNDLE_SHA256 = "05aee37169b6b69f571ecf1d63303579c65a69778666d5160d460c0a980d5478"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract", type=Path, required=True)
    args = parser.parse_args()
    chunk_dir = Path(__file__).with_name("mast_challenge_bundle_chunks")
    chunks = sorted(chunk_dir.glob("*.txt"))
    if not chunks:
        raise RuntimeError("MAST challenge source chunks are missing")
    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in chunks)
    raw = lzma.decompress(base64.b64decode(encoded))
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_BUNDLE_SHA256:
        raise RuntimeError(f"bundle SHA-256 {digest} != frozen {EXPECTED_BUNDLE_SHA256}")
    files = json.loads(raw.decode("utf-8"))
    if not isinstance(files, dict) or not files:
        raise RuntimeError("source bundle is empty or malformed")
    manifest: dict[str, str] = {}
    for relative, content in files.items():
        target = args.extract / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        if target.suffix == ".py":
            target.chmod(0o755)
        manifest[relative] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    (args.extract / "SOURCE_BUNDLE_SHA256.txt").write_text(digest + "\n")
    (args.extract / "SOURCE_FILE_SHA256.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({"bundle_sha256": digest, "files": manifest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
