import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PIPELINE = [
    "etl_pipeline.py",
    "customers.py",
    "forecasting.py",
    "export_tables.py",
    "test_system.py",
]


def run_step(script):
    print(f"\n{'=' * 70}\nRUNNING {script}\n{'=' * 70}")
    subprocess.run([sys.executable, script], cwd=ROOT, check=True)


if __name__ == "__main__":
    steps = list(PIPELINE)

    if "--regenerate-data" in sys.argv:
        answer = input("This deletes and regenerates ALL database data. Type YES to continue: ")
        if answer != "YES":
            raise SystemExit("Cancelled.")
        steps.insert(0, "generate_data.py")

    for script in steps:
        try:
            run_step(script)
        except subprocess.CalledProcessError:
            raise SystemExit(f"\nStopped: {script} failed.")

    print("\nAll steps finished.")