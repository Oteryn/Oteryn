#!/usr/bin/env python3
"""Offline structure/admission validation; does not authenticate provider evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry

ROOT = Path(__file__).resolve().parents[2]
DRAFT = "https://json-schema.org/draft/2020-12/schema"


def _check_local_references(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"$ref", "$dynamicRef"} and (not isinstance(child, str) or not child.startswith("#")):
                raise ValueError("compatibility schema references must be document-local")
            _check_local_references(child)
    elif isinstance(value, list):
        for child in value:
            _check_local_references(child)


def load_validator(path: Path) -> Draft202012Validator:
    schema = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict) or schema.get("$schema") != DRAFT or schema.get("type") != "object":
        raise ValueError("compatibility schema must be a draft 2020-12 object")
    _check_local_references(schema)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ValueError(f"invalid compatibility schema: {exc.message}") from exc
    # Explicit empty registry has no network retrieval; provider schemas stay provider-owned.
    return Draft202012Validator(schema, registry=Registry())


def validate_manifest(document: Any, path: Path, validator: Draft202012Validator) -> None:
    try:
        validator.validate(document)
    except ValidationError as exc:
        location = "/".join(str(part) for part in exc.absolute_path) or "<root>"
        raise ValueError(f"{path}:{location}: {exc.message}") from exc
    if document["release_id"] != path.stem:
        raise ValueError(f"{path}: release_id must equal the filename stem")
    if any(contract["status"] != "compatible" for contract in document["contracts"]):
        raise ValueError(f"{path}: committed release contracts must have status compatible")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, default=ROOT / "ecosystem/compatibility.schema.json")
    parser.add_argument("--release-dir", type=Path, default=ROOT / "ecosystem/releases")
    args = parser.parse_args()
    try:
        validator = load_validator(args.schema)
        if args.release_dir.exists() and not args.release_dir.is_dir():
            raise ValueError("release-dir must be a directory, not a regular file")
        files = sorted(args.release_dir.glob("*.json"))
        for path in files:
            validate_manifest(json.loads(path.read_text(encoding="utf-8")), path, validator)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"status": "STRUCTURE_VALID", "release_manifests": len(files),
                      "provider_evidence": "NOT_AUTHENTICATED"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
