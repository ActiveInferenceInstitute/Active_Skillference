#!/usr/bin/env python3
"""Upload the release PDF to the reserved Zenodo draft and publish it.

This is the irreversible half of the DOI workflow and is deliberately a separate
script from ``reserve_zenodo_doi.py``: publishing mints a permanent, public,
non-deletable record. It refuses to run without ``--confirm-publish`` and it
refuses to publish a deposit whose DOI does not match the recorded reservation.
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
    publish_deposit,
    read_token,
    upload_deposit_file,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--env-file",
        default=str(Path.home() / "Documents" / "GitHub" / "template" / ".env"),
        help=f"dotenv file holding {TOKEN_ENV_VAR}",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="artifact to attach to the deposit before publishing",
    )
    parser.add_argument(
        "--confirm-publish",
        action="store_true",
        help="required: publishing mints a permanent DOI that cannot be deleted",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.confirm_publish:
        print(
            "ERROR: refusing to publish without --confirm-publish. Publishing a "
            "Zenodo deposit is permanent and cannot be undone.",
            file=sys.stderr,
        )
        return 2
    record_path = _ROOT / "data" / "zenodo_reservation.json"
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        token = read_token(Path(args.env_file))
        artifact = Path(args.file)
        if not artifact.is_file():
            raise ZenodoError(f"artifact to deposit does not exist: {artifact}")
        upload_deposit_file(
            token=token,
            deposition_id=int(record["depositionId"]),
            path=artifact,
        )
        published = publish_deposit(
            token=token,
            deposition_id=int(record["depositionId"]),
            expected_doi=str(record["doi"]),
        )
    except (OSError, ValueError, KeyError, ZenodoError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(published, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
