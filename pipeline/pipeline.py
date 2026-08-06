"""End-to-end orchestrator for the NepalHelpDesk content pipeline.

Usage:
  python pipeline/pipeline.py                # full run (collect -> classify -> verify -> publish)
  python pipeline/pipeline.py --dry-run      # collect + classify only, no writes
  python pipeline/pipeline.py --no-llm       # never call the LLM (KB matches only)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from common import log, log_exit, env_flag

PIPELINE_DIR = Path(__file__).resolve().parent


def _run(script: str, extra: list[str] | None = None, check: bool = True) -> int:
    cmd = [sys.executable, str(PIPELINE_DIR / script)] + (extra or [])
    log(f"==> {script} {' '.join(extra or [])}")
    result = subprocess.run(cmd)
    if check and result.returncode != 0:
        log_exit(f"{script} failed with exit {result.returncode}", 1)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="collect + classify only")
    parser.add_argument("--no-llm", action="store_true", help="never call the LLM")
    parser.add_argument("--build-check", action="store_true",
                        help="build the Astro site afterwards to validate content")
    args = parser.parse_args()

    run_llm = not (args.no_llm or env_flag("PIPELINE_NO_LLM"))
    build_check = args.build_check or env_flag("PIPELINE_BUILD_CHECK")

    log("=== NepalHelpDesk pipeline start ===")
    _run("collect.py", ["--reset"] if args.dry_run else [])
    _run("classify.py")
    if args.dry_run:
        log("=== dry run complete (no verification or publishing) ===")
        return
    _run("verify.py", ["--no-llm"] if not run_llm else [])
    _run("publish.py")

    if build_check:
        site_dir = PIPELINE_DIR.parent / "site"
        log("==> astro build check")
        result = subprocess.run(["npm", "run", "build"], cwd=str(site_dir))
        if result.returncode != 0:
            log_exit("astro build failed — content invalid", 1)
        log("astro build OK")

    log("=== pipeline complete ===")


if __name__ == "__main__":
    main()
