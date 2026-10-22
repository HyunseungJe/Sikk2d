# Layer bundle manifest v1

`tools/psd_import/manifest-v1.schema.json` is the portable JSON Schema (Draft 2020-12). `psd_import.schema.validate_manifest` also checks unique IDs, image paths and orders, and contiguous order in the layer array. The schema is included in the installed Python package. The web consumer is a later phase.

| Field                           | Meaning                                                                            |
| ------------------------------- | ---------------------------------------------------------------------------------- |
| `version`                       | Integer `1`                                                                        |
| `canvas.width`, `canvas.height` | Positive pixel dimensions of the PSD canvas                                        |
| `layers`                        | Raster records in bottom-to-top painting order                                     |
| `layers[].id`                   | `layer-` plus the zero-based sibling-index path through the PSD tree               |
| `name`                          | Original Unicode name; empty and duplicate names are preserved                     |
| `image`                         | Relative `layers/<id>.png` path; filenames never use layer names                   |
| `order`                         | Contiguous zero-based paint order; larger values paint on top                      |
| `x`, `y`                        | Tight alpha bounding box origin in PSD canvas coordinates; may be negative         |
| `width`, `height`               | Positive dimensions matching the cropped RGBA PNG                                  |
| `visible`                       | Effective visibility, including all parent groups                                  |
| `groupPath`                     | Ancestor names from outermost to innermost; names are descriptive, not unique keys |
| `warnings`                      | Ordered `{code, message, layerId?}` records; document warnings have no `layerId`   |

IDs depend on structural indices, never names, output paths, timestamps or random values. Repeated conversion of the same input yields identical manifest and PNG bytes in the same locked environment. IDs are not promised to survive source hierarchy edits. Skipping an empty or unsupported layer does not renumber the other IDs. `order` includes exported hidden layers.

Hidden raster layers retain their PNGs and have `visible: false`; a hidden parent makes all descendants effectively hidden. The bundle is a flat snapshot, so parent groups are represented by names rather than editable group records. Fully transparent layers after masks/opacity, or zero-size raster layers, are omitted with `EMPTY_LAYER` warnings identifying their structural IDs. This avoids zero-size images and preserves a positive-size PNG contract. Names and visibility are preserved for every exported raster layer.

Active raster masks, their offsets and background coverage, pixel transparency, fill opacity and layer opacity are baked into PNG alpha by `psd-tools`. Disabled raster masks do not affect pixels. Tight bounds come from the resulting alpha channel, including semitransparent pixels. Opacity must not be multiplied again by a consumer. Reconstruction starts with a transparent canvas, sorts/validates paint order, skips hidden records and applies normal source-over at `(x, y)`. Off-canvas pixels remain in the layer PNG and are clipped only when painting the canvas.

## Compatibility and warnings

RGB 8-bit raster layers with normal blending are the supported fidelity target. Ordinary nested groups preserve child order, names and effective visibility. Other modes/depths receive `UNSUPPORTED_COLOR_MODE` because 8-bit RGBA conversion can lose precision/color/alpha. ICC-profile conversion receives `COLOR_PROFILE` because independently converting layers to sRGB can differ from document-space blending.

Non-raster layers (text, shape, smart object, adjustment, fill, etc.) are omitted with `UNSUPPORTED_LAYER`. Context-dependent features receive explicit warnings: non-normal blending, clipping relationships, effects, vector masks, group masks/opacity, artboard clipping and advanced blending. Vector masks/effects may be rasterized or approximated by the library; group opacity/masks are not propagated to children. Warning-bearing bundles are best-effort exports and must not be assumed to match Photoshop. Warnings are in both the manifest and CLI output.

## Reconstruction comparison

`--compare` reconstructs from exported PNGs and the validated manifest without using PSD pixel data. It compares against `PSDImage.composite(ignore_preview=True)` with default sRGB conversion. The saved PSD preview is compared separately when present. For RGB-only previews, reference composite alpha is used to weight preview RGB; the preview cannot independently validate alpha. The integration tests independently check exported alpha against each original raster transparency × active mask as well.

Metrics use premultiplied RGBA in the 0–255 range: maximum channel error, mean absolute error (MAE), root mean square error (RMSE), and ratio of pixels with any channel error greater than 1. RGB underneath alpha=0 is ignored; alpha errors remain measurable. The default limits are max ≤ 4 and MAE ≤ 0.1 for both the recomputed reference and saved preview. These allow small 8-bit per-layer rounding differences while rejecting changes to pixels, masks, placement and stacking. `comparison.json` records the reference, preview alpha caveat, all metrics, limits and pass/fail. This is a quantitative check, not a claim of bit-identical Photoshop rendering.

`npm run check` runs synthetic/schema/CLI tests first, then all three private PSD integrations with printed comparison metrics. Missing private files generate explicit skip messages. Output stays outside Git; no private artwork is needed to validate the schema or run synthetic tests.
