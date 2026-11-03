"""python -m harvester_risk_atlas <stage> [<stage> ...] [--offline]"""
from __future__ import annotations

import argparse

from .pipeline import run

STAGES = ["fetch", "base", "index", "validate", "export"]


def main() -> None:
    parser = argparse.ArgumentParser(prog="harvester_risk_atlas", description="Build the v2 atlas data.")
    parser.add_argument("stages", nargs="+", choices=[*STAGES, "all"])
    parser.add_argument("--offline", action="store_true", help="use cached raw data only; never fetch")
    args = parser.parse_args()
    stages = STAGES if "all" in args.stages else args.stages
    run(stages, offline=args.offline)


if __name__ == "__main__":
    main()
