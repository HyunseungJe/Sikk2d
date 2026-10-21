"""Command-line entry point; deliberately does not read or convert artwork."""

import argparse
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sikk2d PSD importer scaffold. Conversion is not implemented."
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.0.0")
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
