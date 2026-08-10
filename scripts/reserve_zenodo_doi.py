#!/usr/bin/env python3
"""Reserve a Zenodo DOI on an unpublished draft; never publish one.

Zenodo allocates the identifier immediately but it does not resolve until the
draft is published. Publishing is a permanent, outward-facing act and is left to
a human running the release tooling.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.publication.zenodo import (
    TOKEN_ENV_VAR,
    ZenodoError,
    find_draft,
    read_token,
    reserve_doi,
    zenodo_metadata,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--env-file",
        default=str(Path.home() / "Documents" / "GitHub" / "template" / ".env"),
        help=f"dotenv file holding {TOKEN_ENV_VAR}",
    )
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="return the existing unpublished draft instead of creating another",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        token = read_token(Path(args.env_file))
        metadata = zenodo_metadata(_ROOT / ".zenodo.json")
        existing = find_draft(token=token, title=str(metadata["title"]))
        if existing is not None:
            if not args.reuse_existing:
                print(
                    "ERROR: an unpublished draft already exists "
                    f"(deposition {existing.deposition_id}, doi {existing.doi}). "
                    "Pass --reuse-existing to report it instead of reserving another.",
                    file=sys.stderr,
                )
                return 1
            reserved = existing
        else:
            reserved = reserve_doi(token=token, metadata=metadata)
    except ZenodoError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(reserved.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
