#!/usr/bin/env python3
"""Offline structure/admission validation; does not authenticate provider evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

ROOT = Path(__file__).resolve().parents[2]
DRAFT = "https://json-schema.org/draft/2020-12/schema"


def _check_local_references(resource: Resource, resolver: Any) -> None:
    # Resolve all schema references, including unused optional/definition paths.
    # The library preserves nested $id and anchor scope; no URI is fetched.
    if isinstance(resource.contents, dict):
        for key in ("$ref", "$dynamicRef"):
            if key not in resource.contents:
                continue
            reference = resource.contents[key]
            if not isinstance(reference, str) or not reference.startswith("#"):
                raise ValueError("compatibility schema references must be document-local")
            try:
                resolved = resolver.lookup(reference)
                Draft202012Validator.check_schema(resolved.contents)
            except (Unresolvable, SchemaError) as exc:
                raise ValueError(f"invalid local schema reference {reference!r}: {exc}") from exc
    for child in resource.subresources():
        _check_local_references(child, resolver.in_subresource(child))


def load_validator(path: Path) -> Draft202012Validator:
    schema = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict) or schema.get("$schema") != DRAFT or schema.get("type") != "object":
        raise ValueError("compatibility schema must be a draft 2020-12 object")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ValueError(f"invalid compatibility schema: {exc.message}") from exc
    # Registry has no network retrieval; provider schemas stay provider-owned.
    resource = Resource.from_contents(schema)
    uri = resource.id() or "urn:oteryn:compatibility-schema"
    registry = Registry().with_resource(uri, resource).crawl()
    _check_local_references(resource, registry.resolver(uri))
    return Draft202012Validator(schema, registry=registry)


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
    parser.add_argument("--release-dir", type=Path, default=None)
    args = parser.parse_args()
    try:
        validator = load_validator(args.schema)
        release_dir = args.release_dir if args.release_dir is not None else ROOT / "ecosystem/releases"
        if (args.release_dir is not None or release_dir.exists()) and not release_dir.is_dir():
            raise ValueError("release-dir must be an existing directory")
        files = sorted(release_dir.glob("*.json"))
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
