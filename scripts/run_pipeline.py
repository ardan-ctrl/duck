from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AutoCut pipeline")
    parser.add_argument("--episode", required=True, help="Episode ID (folder in input/)")
    parser.add_argument("--asr-provider", default="script_stub")
    parser.add_argument("--hooks-provider", default="rules_stub")
    parser.add_argument("--render-provider", default="preview_stub")
    parser.add_argument("--from-scene", type=int, default=None)
    parser.add_argument("--to-scene", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "src"))

    from autocut.config.settings import ProviderSettings
    from autocut.orchestrator.pipeline import run_pipeline

    settings = ProviderSettings(
        asr_provider=args.asr_provider,
        hooks_provider=args.hooks_provider,
        render_provider=args.render_provider,
    )
    run_pipeline(
        repo_root=repo_root,
        episode_id=args.episode,
        settings=settings,
        from_scene=args.from_scene,
        to_scene=args.to_scene,
    )


if __name__ == "__main__":
    main()
