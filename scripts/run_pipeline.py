from __future__ import annotations

import argparse
import sys
from pathlib import Path



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AutoCut pipeline")
    parser.add_argument("--episode", required=True, help="Episode ID (folder in input/)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "src"))

    from autocut.orchestrator.pipeline import run_pipeline

    run_pipeline(repo_root=repo_root, episode_id=args.episode)


if __name__ == "__main__":
    main()
