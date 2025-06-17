import subprocess
import sys
import time
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
        start = time.time()
        try:
            # Special handling for flake8 to print a custom message when no issues are found.
            # Unlike other tools, flake8 returns exit code 0 and prints nothing when no issues are found,
            # so we check its stdout to print meaningful feedback.
            if cmd[0] == "flake8":
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.stdout.strip():
                    print(result.stdout)
                    sys.exit(result.returncode)
                else:
                    print("flake8 found no issues")
            else:
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    sys.exit(result.returncode)
        finally:
            end = time.time()
            print(f"Execution time: {end - start:.1f}s")


if __name__ == "__main__":
    main()
