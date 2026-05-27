from __future__ import annotations

import argparse
import sys

from openapi_diff_checker.checker import compare


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="openapi-diff-checker",
        description="Check if two OpenAPI specs are functionally equivalent",
    )
    parser.add_argument("src", help="Path to source OpenAPI file (YAML or JSON)")
    parser.add_argument("dest", help="Path to destination OpenAPI file (YAML or JSON)")
    args = parser.parse_args()

    result = compare(args.src, args.dest)

    if result.equivalent:
        print("Specs are functionally equivalent.")
        sys.exit(0)
    else:
        print(f"Found {len(result.differences)} functional difference(s):\n")
        for diff in result.differences:
            print(f"  {diff}")
        sys.exit(1)
