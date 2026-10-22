"""Portable manifest v1 JSON Schema and bundle-level invariants."""

import json
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

SCHEMA = json.loads(
    files("psd_import").joinpath("manifest-v1.schema.json").read_text(encoding="utf-8")
)
_VALIDATOR = Draft202012Validator(SCHEMA)


def validate_manifest(manifest: Any) -> None:
    """Raise ValidationError for an invalid manifest, including duplicate IDs/order."""
    _VALIDATOR.validate(manifest)
    layers = manifest["layers"]
    for field in ("id", "image", "order"):
        values = [layer[field] for layer in layers]
        if len(values) != len(set(values)):
            raise ValidationError(f"layers must have unique {field} values")
    if [layer["order"] for layer in layers] != list(range(len(layers))):
        raise ValidationError("layers must be stored in contiguous bottom-to-top order")
