import subprocess
import sys
from pathlib import Path


def main():
    root = Path.cwd()

    # Ensure we're in project root
    if not (root / "pyproject.toml").exists():
        print(
            "ERROR: This script must be run from the project root (where pyproject.toml is).",
            file=sys.stderr,
        )
        sys.exit(1)

    targets = ["app", "tests", "scripts"]

    commands = [
        ["black", "."],
        ["isort", "."],
        ["flake8", *targets],
        ["mypy", *targets, "--follow-untyped-imports"],
    ]

    for cmd in commands:
        print(f"\n=== Running: {' '.join(cmd)} ===")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            sys.exit(result.returncode)


if __name__ == "__main__":
    main()
