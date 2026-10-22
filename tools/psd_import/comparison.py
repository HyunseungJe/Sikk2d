"""Reconstruct a bundle without its PSD and quantify visible RGBA differences."""

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from psd_tools import PSDImage

from psd_import.schema import validate_manifest


def reconstruct(bundle: Path) -> Image.Image:
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    validate_manifest(manifest)
    canvas = manifest["canvas"]
    result = Image.new("RGBA", (canvas["width"], canvas["height"]))
    for layer in manifest["layers"]:
        image_path = (bundle / layer["image"]).resolve()
        if not image_path.is_relative_to(bundle.resolve()):
            raise ValueError("Layer image must remain inside the bundle.")
        with Image.open(image_path) as image:
            if image.mode != "RGBA" or image.size != (layer["width"], layer["height"]):
                raise ValueError(f"Layer PNG disagrees with manifest: {layer['id']}")
            if layer["visible"]:
                result.alpha_composite(image, (layer["x"], layer["y"]))
    return result


def pixel_metrics(actual: Image.Image, expected: Image.Image) -> dict[str, float]:
    if actual.size != expected.size:
        raise ValueError("Cannot compare different canvas sizes.")

    def premultiplied(image: Image.Image) -> np.ndarray:
        pixels = np.asarray(image.convert("RGBA"), dtype=np.float64).copy()
        pixels[:, :, :3] *= pixels[:, :, 3:] / 255.0
        return pixels

    # Ignore RGB stored under alpha=0, but retain alpha as a separate channel.
    delta = np.abs(premultiplied(actual) - premultiplied(expected))
    return {
        "maxChannelError": float(delta.max()),
        "meanAbsoluteError": float(delta.mean()),
        "rootMeanSquareError": float(np.sqrt(np.mean(delta**2))),
        "pixelsOverOneRatio": float(np.any(delta > 1.0, axis=2).mean()),
    }


def compare_bundle(
    source: Path,
    bundle: Path,
    *,
    max_error: float = 4.0,
    mean_error: float = 0.1,
) -> dict[str, Any]:
    psd = PSDImage.open(source)
    actual = reconstruct(bundle)
    # A saved PSD preview may be stale or RGB-only (all three private fixtures
    # have RGB previews). Re-render source layers/masks for an RGBA reference.
    expected = psd.composite(ignore_preview=True)
    metrics = pixel_metrics(actual, expected)
    report: dict[str, Any] = {
        "reference": "psd-tools composite(ignore_preview=True), sRGB RGBA",
        "metric": "premultiplied RGBA, 0..255",
        **metrics,
        "limits": {"maxChannelError": max_error, "meanAbsoluteError": mean_error},
        "passed": (
            metrics["maxChannelError"] <= max_error
            and metrics["meanAbsoluteError"] <= mean_error
        ),
    }
    preview = psd.topil()
    if preview is not None:
        saved = preview.convert("RGBA")
        alpha_note = "Saved preview alpha is used directly."
        if "A" not in preview.getbands():
            saved.putalpha(expected.convert("RGBA").getchannel("A"))
            alpha_note = (
                "RGB-only preview: source recomposite alpha masks the RGB comparison; "
                "preview does not independently validate alpha."
            )
        preview_metrics = pixel_metrics(actual, saved)
        report["savedPreview"] = {
            "mode": preview.mode,
            "alphaNote": alpha_note,
            **preview_metrics,
        }
        report["passed"] = (
            report["passed"]
            and preview_metrics["maxChannelError"] <= max_error
            and preview_metrics["meanAbsoluteError"] <= mean_error
        )
    return report
