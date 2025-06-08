import shutil
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

    for dirpath in root.rglob("__pycache__"):
        if dirpath.is_dir():
            shutil.rmtree(dirpath)
            print(".", end="", flush=True)


if __name__ == "__main__":
    main()
