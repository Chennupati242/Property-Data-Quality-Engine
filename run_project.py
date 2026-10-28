
"""Run the complete property data quality project."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

COMMANDS = [
    [sys.executable, "src/main.py"],
    [sys.executable, "src/database.py"],
]


def main():
    print("PROPERTY DATA QUALITY ENGINE")

    for command in COMMANDS:
        print(f"\nRunning: {' '.join(command)}")

        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
        )

        if result.returncode != 0:
            print(
                f"\nERROR: Command failed with exit code "
                f"{result.returncode}."
            )
            sys.exit(result.returncode)

    print("\nAll project stages completed successfully.")


if __name__ == "__main__":
    main()
