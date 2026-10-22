"""Command-line PSD converter. User artwork and generated bundles stay outside Git."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from psd_import.comparison import compare_bundle
from psd_import.converter import convert, write_json


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a raster PSD to transparent PNG layers and manifest v1."
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    parser.add_argument("source", type=Path, help="Input PSD (read only)")
    parser.add_argument(
        "output", type=Path, help="New/empty bundle directory outside Git"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare reconstruction with PSD composite",
    )
    args = parser.parse_args(argv)
    try:
        manifest = convert(args.source, args.output)
        print(f"Exported {len(manifest['layers'])} layers to {args.output}")
        for warning in manifest["warnings"]:
            print(f"WARNING {warning['code']}: {warning['message']}")
        if args.compare:
            report = compare_bundle(args.source, args.output)
            write_json(args.output / "comparison.json", report)
            print(json.dumps(report, ensure_ascii=False))
            return 0 if report["passed"] else 1
    except (OSError, ValueError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
