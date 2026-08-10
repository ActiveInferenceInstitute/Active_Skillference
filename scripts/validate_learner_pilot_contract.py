#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.pilot.contract import load_pilot_contract


def main() -> int:
    path = _ROOT / "data" / "learner_pilot_contract.json"
    payload = load_pilot_contract(path)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "contractVersion": payload["contractVersion"],
                "participantFields": len(payload["participants"]["requiredFields"]),
                "eventTypes": len(payload["events"]["allowedEventTypes"]),
                "outcomes": 1 + len(payload["outcomes"]["secondary"]),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
