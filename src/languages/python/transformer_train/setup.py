#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def log(msg: str):
    print(f"[INFO] {msg}")

def err(msg: str):
    print(f"[ERROR] {msg}")
    sys.exit(1)

def check_pip():
    """Check if pip is available."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True)
    except subprocess.CalledProcessError:
        err("pip not found. Please ensure Python and pip are installed.")

def install_missing_packages(req_path: Path):
    """Install missing Python packages listed in requirements.txt"""
    if not req_path.exists():
        log("No requirements.txt found, skipping setup.")
        return

    log(f"Reading requirements from {req_path}")

    with req_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not lines:
        log("requirements.txt is empty, nothing to install.")
        return

    for pkg in lines:
        pkg_name = pkg.split("==")[0].split(">=")[0].split("<=")[0].strip()
        # check if installed
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.returncode == 0:
            log(f"[OK] {pkg_name} already installed.")
        else:
            log(f"[INSTALL] Installing {pkg} ...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg],
                    check=True
                )
            except subprocess.CalledProcessError:
                log(f"[WARNING] Failed to install {pkg}")

def main():
    cwd = Path(__file__).resolve().parent
    log(f"Setting up Python environment for {cwd.name}")
    check_pip()
    install_missing_packages(cwd / "requirements.txt")
    log("Python environment setup complete.")

if __name__ == "__main__":
    main()
