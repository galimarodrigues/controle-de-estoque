import os
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
HARDCODED_SEED_API_KEY = "seed-api-key-estoque-2026"
DEFAULT_SEED_NAME = "seed_prod_v2"
SUPPORTED_SEEDS = {
    DEFAULT_SEED_NAME: {
        "script": "scripts/seed_prod_v2.py",
    },
}


def get_supported_seed_names() -> list[str]:
    return sorted(SUPPORTED_SEEDS.keys())


def run_seed(*, seed_name: str, mode: str = "orm", dry_run: bool = False, force_sqlite: bool = False):
    if seed_name not in SUPPORTED_SEEDS:
        raise ValueError(
            f"Seed invalido: {seed_name}. Seeds disponiveis: {', '.join(get_supported_seed_names())}"
        )

    if mode not in {"orm", "http"}:
        raise ValueError("Modo invalido. Use 'orm' ou 'http'.")

    command = [
        sys.executable,
        str(BASE_DIR / SUPPORTED_SEEDS[seed_name]["script"]),
        "--mode",
        mode,
    ]
    if dry_run:
        command.append("--dry-run")

    env = os.environ.copy()
    if force_sqlite:
        env.pop("DATABASE_URL", None)
        env["FORCE_SQLITE"] = "1"

    completed = subprocess.run(
        command,
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    return completed
