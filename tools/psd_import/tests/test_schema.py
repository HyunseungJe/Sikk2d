"""Schema rejects malformed bundles before any file access."""

from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator, ValidationError
from psd_import.converter import convert
from psd_import.schema import SCHEMA, validate_manifest


def test_schema_is_valid_and_accepts_export(synthetic_psd, tmp_path):
    Draft202012Validator.check_schema(SCHEMA)
    validate_manifest(convert(synthetic_psd, tmp_path / "bundle"))


@pytest.mark.parametrize(
    "field,value",
    [
        ("image", "../private.png"),
        ("image", "/absolute.png"),
        ("image", "layers/layer-0.PNG"),
        ("order", -1),
        ("order", True),
        ("width", 0),
        ("height", -1),
        ("x", 1.5),
        ("visible", 1),
        ("groupPath", "group"),
        ("name", None),
        ("id", ""),
    ],
)
def test_invalid_layer_fields_rejected(synthetic_psd, tmp_path, field, value):
    manifest = convert(synthetic_psd, tmp_path / "bundle")
    manifest["layers"][0][field] = value
    with pytest.raises(ValidationError):
        validate_manifest(manifest)


@pytest.mark.parametrize("field", ["id", "image", "order"])
def test_duplicate_keys_rejected(synthetic_psd, tmp_path, field):
    manifest = convert(synthetic_psd, tmp_path / "bundle")
    manifest["layers"][1][field] = manifest["layers"][0][field]
    with pytest.raises(ValidationError, match="unique"):
        validate_manifest(manifest)


def test_top_level_invariants(synthetic_psd, tmp_path):
    manifest = convert(synthetic_psd, tmp_path / "bundle")
    for field, value in [("version", 2), ("version", True), ("canvas", {"width": 0})]:
        invalid = deepcopy(manifest)
        invalid[field] = value
        with pytest.raises(ValidationError):
            validate_manifest(invalid)
    manifest["layers"] = list(reversed(manifest["layers"]))
    with pytest.raises(ValidationError, match="bottom-to-top"):
        validate_manifest(manifest)
