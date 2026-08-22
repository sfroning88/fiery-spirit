#!/usr/bin/env python3
"""
Author: Sean Froning
Created Date: 8.21.2026
Unified test orchestrator for worker pipelines

Usage: python3 -m src.tests.orchestrator <train|predict>

Notes:
- Tests run against the real Supabase project (tables + storage buckets).
  Tests run against the real Cloudlfare workspace (storage buckets).
  Tests run against the real Modal environment (app workspace).
- Postgres + buckets are Supabase/Cloudflare.
  Only Redis runs locally via Docker for the RQ queue.

Setup Steps:
1) pnpm use:local
2) pnpm redis:up
3) cd packages/python
4) python -m src.e2e.orchestrator <ingest|registry>

If Creating or Activating venv:
1) python3 -m venv .venv
2) source .venv/bin/activate
3) pip install -e .

Teardown: pnpm redis:down
"""

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv


def _find_root_env() -> str:
    """Walk up from this file to find monorepo root .env"""
    directory = Path(__file__).resolve().parent
    for _ in range(10):
        env_path = directory / ".env"
        if env_path.is_file():
            return str(env_path)
        directory = directory.parent
    return ""


load_dotenv(_find_root_env())

from .endpoints import WORKER_PORTS, worker_url
from .helpers import TESTS_DIR, wait_for_health
from .redis_clear import clear_redis_queue

MONOREPO_MARKER = "pnpm-workspace.yaml"
HEALTH_TIMEOUT_SECONDS = 120
SHARED_PYTHON_SRC = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    os.pardir,
    os.pardir,
    "src",
)

WORKER_APPS = {
    "backend": "apps/backend",
    "ai": "apps/ai",
}


@dataclass(frozen=True)
class WorkerSpec:
    """Per-domain process plan for a workflow"""

    domain: str
    needs_rq_worker: bool


WORKFLOW_WORKERS: Dict[str, Tuple[WorkerSpec, ...]] = {
    "ingest": (WorkerSpec(domain="ai", needs_rq_worker=True),),
    "registry": (WorkerSpec(domain="backend", needs_rq_worker=False),),
}


def _find_monorepo_root() -> str:
    """Walk up from tests dir to find monorepo root"""
    directory = TESTS_DIR
    for _ in range(10):
        if os.path.isfile(os.path.join(directory, MONOREPO_MARKER)):
            return directory
        directory = os.path.dirname(directory)
    raise RuntimeError("Could not find monorepo root")


def _resolve_python(app_dir: str) -> str:
    """Return the app's .venv Python (fallback to current interpreter)"""
    candidate = os.path.join(app_dir, ".venv", "bin", "python")
    return candidate if os.path.isfile(candidate) else sys.executable


def _spawn_workers(root: str, specs: Tuple[WorkerSpec, ...]) -> List[subprocess.Popen]:
    """Spawn uvicorn (+ optional rq worker) per spec; return process handles"""
    procs: List[subprocess.Popen] = []
    for spec in specs:
        app_dir = os.path.join(root, WORKER_APPS[spec.domain])
        python = _resolve_python(app_dir)
        port = WORKER_PORTS[spec.domain]
        env = {**os.environ, "JOB_DOMAIN": spec.domain}
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = SHARED_PYTHON_SRC + (
            os.pathsep + existing if existing else ""
        )

        procs.append(
            subprocess.Popen(
                [python, "-m", "uvicorn", "src.main:app", "--port", str(port)],
                cwd=app_dir,
                env=env,
            )
        )

        if spec.needs_rq_worker:
            procs.append(
                subprocess.Popen(
                    [python, "-m", "src.worker_runner"],
                    cwd=app_dir,
                    env=env,
                )
            )
    return procs


def _kill_workers(procs: List[subprocess.Popen]) -> None:
    """Terminate all spawned worker processes"""
    for proc in procs:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def _pkill_workers() -> None:
    """Kill any lingering worker processes by command pattern (catches rq forks and restarts)"""
    for pattern in ["src.worker_runner", "uvicorn src.main:app"]:
        try:
            subprocess.run(["pkill", "-f", pattern], check=False)
        except Exception:
            pass


def _await_workers_ready(specs: Tuple[WorkerSpec, ...]) -> None:
    """Poll /health on each spawned API until 200 OK"""
    for spec in specs:
        base = worker_url(spec.domain)
        print(f"Waiting for {spec.domain} API @ {base} to become healthy...")
        if not wait_for_health(base, timeout=HEALTH_TIMEOUT_SECONDS):
            raise RuntimeError(f"{spec.domain} API never became healthy at {base}")
        print(f"{spec.domain} API ready")


def _run_workflow(workflow: str) -> None:
    """Dispatch to the script matching the workflow"""
    if workflow == "ingest":
        from .scripts.ingest import run_ingest_test

        run_ingest_test()
    elif workflow == "registry":
        from .scripts.registry import run_reload_test

        run_reload_test()
    else:
        raise ValueError(f"Unknown workflow: {workflow}")


def main() -> None:
    """CLI entry point - workflow argument is required"""
    parser = argparse.ArgumentParser(
        description="fiery-spirit unified test orchestrator"
    )
    parser.add_argument(
        "workflow",
        choices=sorted(WORKFLOW_WORKERS.keys()),
        help="Test workflow to run",
    )
    args = parser.parse_args()
    workflow: str = args.workflow

    root = _find_monorepo_root()
    specs = WORKFLOW_WORKERS[workflow]

    procs = _spawn_workers(root, specs)
    print(f"Spawned {len(procs)} processes for {[spec.domain for spec in specs]}")

    try:
        _await_workers_ready(specs)
        clear_redis_queue()

        print(f"\n{'=' * 60}")
        print(f"Running {workflow} workflow")
        print(f"{'=' * 60}\n")

        _run_workflow(workflow)

        print(f"\n{'=' * 60}")
        print(f"{workflow.upper()} WORKFLOW PASSED")
        print(f"{'=' * 60}")

    except Exception as err:
        print(f"\n{'=' * 60}")
        print(f"{workflow.upper()} WORKFLOW FAILED: {err}")
        print(f"{'=' * 60}")
        raise

    finally:
        print("\nCleaning up...")
        try:
            clear_redis_queue()
        except Exception as cleanup_err:
            print(f"WARNING: Redis cleanup failed: {cleanup_err}")
        _kill_workers(procs)
        _pkill_workers()
        print("Cleanup complete")


if __name__ == "__main__":
    main()
