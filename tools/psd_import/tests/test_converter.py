"""File-based edge cases: order, offsets, masks, visibility and stable bundles."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from psd_import.comparison import compare_bundle, pixel_metrics, reconstruct
from psd_import.converter import convert
from psd_tools import PSDImage
from psd_tools.api.layers import Group, PixelLayer
from psd_tools.constants import BlendMode


def test_deterministic_bundle_order_and_tight_bounds(synthetic_psd, tmp_path):
    original = synthetic_psd.read_bytes()
    first, second = tmp_path / "first", tmp_path / "second"
    manifest = convert(synthetic_psd, first)
    assert convert(synthetic_psd, second) == manifest
    for path in first.rglob("*"):
        if path.is_file():
            assert path.read_bytes() == (second / path.relative_to(first)).read_bytes()
    assert synthetic_psd.read_bytes() == original
    assert manifest["canvas"] == {"width": 12, "height": 10}
    bottom, top, hidden = manifest["layers"]
    assert [item["order"] for item in manifest["layers"]] == [0, 1, 2]
    assert [item["id"] for item in manifest["layers"]] == [
        "layer-0",
        "layer-2-0-0",
        "layer-3",
    ]
    assert [item["name"] for item in manifest["layers"]] == ["same", "same", ""]
    assert (bottom["x"], bottom["y"], bottom["width"], bottom["height"]) == (
        -1,
        3,
        6,
        4,
    )
    assert top["groupPath"] == ["group/한글", "nested"]
    assert hidden["visible"] is False
    assert (first / hidden["image"]).is_file()
    assert manifest["warnings"] == [
        {
            "code": "EMPTY_LAYER",
            "message": "Fully transparent raster layer omitted.",
            "layerId": "layer-1",
        }
    ]
    reconstructed = reconstruct(first)
    assert reconstructed.getpixel((0, 3)) == (255, 0, 0, 255)
    # Top opacity (128/255) multiplies its pixel alpha (128/255), once only.
    assert Image.open(first / top["image"]).getchannel("A").getextrema() == (64, 64)
    assert reconstructed.getpixel((8, 2))[3] == 0
    assert compare_bundle(synthetic_psd, first)["passed"]


@pytest.mark.parametrize("disabled", [False, True])
@pytest.mark.parametrize("background", [0, 255])
def test_mask_offset_alpha_and_disabled_state(tmp_path, disabled, background):
    psd = PSDImage.new("RGBA", (10, 10))
    layer = PixelLayer.frompil(
        Image.new("RGBA", (6, 5), (20, 30, 40, 128)),
        psd,
        left=1,
        top=2,
        name="masked",
    )
    mask = layer.create_mask(Image.new("L", (2, 2), 128), left=3, top=3)
    mask.disabled = disabled
    mask._data.background_color = background
    source = tmp_path / "mask.psd"
    psd.save(source)
    output = tmp_path / "bundle"
    manifest = convert(source, output)
    exported = manifest["layers"][0]
    with Image.open(output / exported["image"]) as image:
        if disabled or background:
            assert (exported["x"], exported["y"], image.size) == (1, 2, (6, 5))
        else:
            assert (exported["x"], exported["y"], image.size) == (3, 3, (2, 2))
        assert image.getpixel((3 - exported["x"], 3 - exported["y"]))[3] in (
            (128,) if disabled else (63, 64)
        )
    assert compare_bundle(source, output)["passed"]


def test_hidden_group_and_hidden_leaf_keep_pixels(tmp_path):
    psd = PSDImage.new("RGBA", (4, 4))
    group = Group.new(psd, "hidden parent")
    group.visible = False
    PixelLayer.frompil(Image.new("RGBA", (2, 2), "red"), group, name="child")
    source = tmp_path / "hidden.psd"
    psd.save(source)
    output = tmp_path / "bundle"
    layer = convert(source, output)["layers"][0]
    assert layer["visible"] is False
    assert layer["groupPath"] == ["hidden parent"]
    with Image.open(output / layer["image"]) as image:
        assert image.getchannel("A").getextrema() == (255, 255)
    assert reconstruct(output).getchannel("A").getbbox() is None


def test_unsupported_features_warn_and_do_not_claim_fidelity(tmp_path):
    psd = PSDImage.new("RGBA", (4, 4))
    group = Group.new(psd, "group")
    group.opacity = 100
    layer = PixelLayer.frompil(Image.new("RGBA", (4, 4), "red"), group)
    layer.blend_mode = BlendMode.MULTIPLY
    PixelLayer.frompil(Image.new("RGBA", (4, 4), "blue"), group).clipping = True
    source = tmp_path / "unsupported.psd"
    psd.save(source)
    output = tmp_path / "bundle"
    manifest = convert(source, output)
    codes = {warning["code"] for warning in manifest["warnings"]}
    assert {
        "UNSUPPORTED_BLEND_MODE",
        "UNSUPPORTED_GROUP_COMPOSITING",
        "UNSUPPORTED_CLIPPING",
    } <= codes
    assert not compare_bundle(source, output)["passed"]


def test_grayscale_warns_about_conversion(tmp_path):
    psd = PSDImage.new("L", (2, 2))
    PixelLayer.frompil(Image.new("L", (2, 2), 100), psd)
    source = tmp_path / "gray.psd"
    psd.save(source)
    assert "UNSUPPORTED_COLOR_MODE" in {
        item["code"] for item in convert(source, tmp_path / "bundle")["warnings"]
    }


def test_existing_output_and_git_checkout_are_rejected(synthetic_psd, tmp_path):
    output = tmp_path / "bundle"
    convert(synthetic_psd, output)
    original = (output / "manifest.json").read_bytes()
    with pytest.raises(ValueError, match="new or empty"):
        convert(synthetic_psd, output)
    assert (output / "manifest.json").read_bytes() == original
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / ".git").write_text("gitdir: /elsewhere")
    with pytest.raises(ValueError, match="outside a Git checkout"):
        convert(synthetic_psd, repository / "bundle")
    assert not (repository / "bundle").exists()


def test_pixel_metrics_ignore_transparent_rgb_but_detect_alpha_and_color():
    transparent = Image.new("RGBA", (2, 2), (255, 0, 0, 0))
    assert pixel_metrics(transparent, Image.new("RGBA", (2, 2)))["maxChannelError"] == 0
    assert (
        pixel_metrics(transparent, Image.new("RGBA", (2, 2), "red"))["maxChannelError"]
        == 255
    )
    with pytest.raises(ValueError, match="canvas sizes"):
        pixel_metrics(transparent, Image.new("RGBA", (1, 1)))


def test_bad_reconstruction_is_detected(synthetic_psd, tmp_path):
    output = tmp_path / "bundle"
    manifest = convert(synthetic_psd, output)
    first = manifest["layers"][0]
    with Image.open(output / first["image"]) as image:
        Image.new("RGBA", image.size, "green").save(output / first["image"])
    assert not compare_bundle(synthetic_psd, output)["passed"]


def test_reconstruct_rejects_mismatched_png(synthetic_psd, tmp_path):
    output = tmp_path / "bundle"
    manifest = convert(synthetic_psd, output)
    Image.new("RGBA", (1, 1)).save(output / manifest["layers"][0]["image"])
    with pytest.raises(ValueError, match="disagrees"):
        reconstruct(output)


def test_mask_removes_fully_transparent_layer(tmp_path):
    psd = PSDImage.new("RGBA", (3, 3))
    layer = PixelLayer.frompil(Image.new("RGBA", (3, 3), "red"), psd)
    layer.create_mask(Image.new("L", (3, 3), 0))
    source = tmp_path / "empty.psd"
    psd.save(source)
    manifest = convert(source, tmp_path / "bundle")
    assert manifest["layers"] == []
    assert manifest["warnings"][0]["code"] == "EMPTY_LAYER"


@pytest.mark.integration
@pytest.mark.parametrize("number,expected_count", [(1, 20), (2, 15), (3, 18)])
def test_private_psds(number, expected_count, tmp_path):
    import os

    assets = Path(
        os.environ.get("SIKK2D_TEST_ASSETS", "/tmp/sasfairy-private-assets/SAS-1")
    )
    source = assets / f"test{number}.psd"
    if not source.is_file():
        pytest.skip(
            f"Private PSD missing: {source}; restore SAS-1 attachments outside Git"
        )
    original_hash = hashlib.sha256(source.read_bytes()).digest()
    psd = PSDImage.open(source)
    assert all(layer.has_mask() and not layer.mask.disabled for layer in psd)
    output = tmp_path / "bundle"
    manifest = convert(source, output)
    assert manifest["canvas"] == {"width": 768, "height": 768}
    assert len(manifest["layers"]) == expected_count
    assert all(layer["visible"] for layer in manifest["layers"])
    assert manifest["warnings"] == []
    second = tmp_path / "repeat"
    assert convert(source, second) == manifest
    for layer in manifest["layers"]:
        assert (output / layer["image"]).read_bytes() == (
            second / layer["image"]
        ).read_bytes()
    # Check mask alpha against stored raster transparency independently of the
    # compositor used for export/reference; allow one 8-bit quantization step.
    for original, exported in zip(psd, manifest["layers"], strict=True):
        alpha = np.asarray(original.topil().getchannel("A"), dtype=float)
        mask = np.asarray(original.mask.topil(layer_sized=True), dtype=float)
        expected_alpha = alpha * mask / 255
        x, y = exported["x"] - original.left, exported["y"] - original.top
        expected_alpha = expected_alpha[
            y : y + exported["height"], x : x + exported["width"]
        ]
        with Image.open(output / exported["image"]) as image:
            assert image.getchannel("A").getbbox() == (0, 0, image.width, image.height)
            actual_alpha = np.asarray(image.getchannel("A"), dtype=float)
        assert np.abs(actual_alpha - expected_alpha).max() <= 1.01
    report = compare_bundle(source, output)
    print(f"test{number}.psd: {json.dumps(report, sort_keys=True)}")
    assert report["passed"], report
    assert hashlib.sha256(source.read_bytes()).digest() == original_hash
