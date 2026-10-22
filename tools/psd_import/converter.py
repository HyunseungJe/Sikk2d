"""Export RGB/8 raster PSDs into deterministic, independently usable layer bundles."""

import json
from pathlib import Path
from typing import Any

from psd_tools import PSDImage
from psd_tools.api.layers import GroupMixin, Layer
from psd_tools.constants import BlendMode, ColorMode, Resource, Tag

from psd_import.schema import validate_manifest


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _check_destination(destination: Path) -> Path:
    destination = destination.resolve()
    if any(
        (parent / ".git").exists() for parent in (destination, *destination.parents)
    ):
        raise ValueError(
            "Bundle output must be outside a Git checkout (private artwork)."
        )
    if destination.exists() and (
        not destination.is_dir() or any(destination.iterdir())
    ):
        raise ValueError(
            "Output directory must be new or empty; bundles are not overwritten."
        )
    return destination


def convert(source: Path, destination: Path) -> dict[str, Any]:
    """Export tight PNGs, then validate/write manifest.json. Never modify the source.

    psd-tools iterates siblings bottom-to-top. Structural sibling indices provide
    IDs independent of names and skipped/hidden layers. Empty rasters are omitted
    with a warning; hidden rasters are exported with effective visible=False.
    """
    destination = _check_destination(destination)
    psd = PSDImage.open(source)
    manifest: dict[str, Any] = {
        "version": 1,
        "canvas": {"width": psd.width, "height": psd.height},
        "layers": [],
        "warnings": [],
    }

    def warn(code: str, message: str, layer_id: str | None = None) -> None:
        warning = {"code": code, "message": message}
        if layer_id is not None:
            warning["layerId"] = layer_id
        manifest["warnings"].append(warning)

    if psd.color_mode != ColorMode.RGB or psd.depth != 8:
        warn(
            "UNSUPPORTED_COLOR_MODE",
            "Only RGB/8 is supported; converting to RGBA may lose color or alpha.",
        )
    if Resource.ICC_PROFILE in psd.image_resources:
        warn(
            "COLOR_PROFILE",
            "PNG pixels are converted to sRGB; per-layer color conversion may differ "
            "from document compositing in its original color space.",
        )

    destination.mkdir(parents=True, exist_ok=True)
    (destination / "layers").mkdir()

    def visit(group: GroupMixin, indices: tuple[int, ...], names: list[str]) -> None:
        for index, layer in enumerate(group):
            path = (*indices, index)
            layer_id = "layer-" + "-".join(str(i) for i in path)
            _feature_warnings(layer, layer_id, warn)
            if layer.is_group():
                visit(layer, path, [*names, layer.name])
                continue
            if layer.kind != "pixel":
                warn(
                    "UNSUPPORTED_LAYER",
                    f"Layer kind {layer.kind!r} is omitted; only raster layers export.",
                    layer_id,
                )
                continue
            if layer.width <= 0 or layer.height <= 0:
                warn("EMPTY_LAYER", "Empty raster layer omitted.", layer_id)
                continue
            # Unlike topil(), composite() applies active raster masks (including
            # offsets, density and feather) and opacity. Include hidden pixels
            # without changing the PSD's source visibility or ancestor state.
            image = layer.composite(
                viewport=layer.bbox,
                layer_filter=lambda candidate, target=layer: candidate is target,
            )
            if image is None:
                warn("EMPTY_LAYER", "Raster layer has no pixels; omitted.", layer_id)
                continue
            image = image.convert("RGBA")
            bounds = image.getchannel("A").getbbox()
            if bounds is None:
                warn("EMPTY_LAYER", "Fully transparent raster layer omitted.", layer_id)
                continue
            cropped = image.crop(bounds)
            image_path = f"layers/{layer_id}.png"
            cropped.save(destination / image_path, format="PNG")
            manifest["layers"].append(
                {
                    "id": layer_id,
                    "name": layer.name,
                    "image": image_path,
                    "order": len(manifest["layers"]),
                    "x": layer.left + bounds[0],
                    "y": layer.top + bounds[1],
                    "width": cropped.width,
                    "height": cropped.height,
                    "visible": layer.is_visible(),
                    "groupPath": names.copy(),
                }
            )

    visit(psd, (), [])
    validate_manifest(manifest)
    write_json(destination / "manifest.json", manifest)
    return manifest


def _feature_warnings(layer: Layer, layer_id: str, warn: Any) -> None:
    """Flag context-dependent PSD behavior that flat normal-alpha PNGs cannot retain."""
    allowed_blends = {BlendMode.NORMAL}
    if layer.is_group():
        allowed_blends.add(BlendMode.PASS_THROUGH)
    if layer.blend_mode not in allowed_blends:
        warn(
            "UNSUPPORTED_BLEND_MODE",
            f"Blend mode {layer.blend_mode.name} is flattened as normal alpha.",
            layer_id,
        )
    if layer.clipping or layer.has_clip_layers():
        warn(
            "UNSUPPORTED_CLIPPING", "Clipping relationships are not retained.", layer_id
        )
    if layer.has_effects():
        warn(
            "UNSUPPORTED_EFFECTS",
            "Layer effects may be cropped or approximated by the raster exporter.",
            layer_id,
        )
    if layer.has_vector_mask():
        warn(
            "UNSUPPORTED_VECTOR_MASK",
            "Vector masks are rasterized; exact fidelity is not guaranteed.",
            layer_id,
        )
    if layer.is_group() and (
        layer.opacity != 255 or layer.has_mask() or layer.has_vector_mask()
    ):
        warn(
            "UNSUPPORTED_GROUP_COMPOSITING",
            "Group opacity and masks are not applied to flattened child layers.",
            layer_id,
        )
    if layer.kind == "artboard":
        warn("UNSUPPORTED_ARTBOARD", "Artboard clipping is not retained.", layer_id)
    if Tag.BLEND_INTERIOR_ELEMENTS in layer.tagged_blocks:
        warn(
            "UNSUPPORTED_ADVANCED_BLENDING",
            "Advanced blending settings may not survive normal-alpha flattening.",
            layer_id,
        )
