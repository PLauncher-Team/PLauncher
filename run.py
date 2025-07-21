import sys
import os
import subprocess
import venv
from pathlib import Path

# Minimum supported Python version
MIN_PY = (3, 10)

# Paths
BASE_DIR = Path(__file__).parent.resolve()
VENV_DIR = BASE_DIR / ".venv"
REQUIREMENTS = BASE_DIR / "requirements.txt"
MAIN_PY = BASE_DIR / "src" / "main.py"

def check_python_version():
    """
    Ensure the current Python interpreter meets the minimum version requirement.
    """
    if sys.version_info < MIN_PY:
        sys.exit(f"[ERROR] Python {MIN_PY[0]}.{MIN_PY[1]}+ is required, found {sys.version_info.major}.{sys.version_info.minor}")

def get_python_executable():
    """
    Return the path to the Python executable inside the virtual environment.
    """
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    exe_name = "python.exe" if os.name == "nt" else "python3"
    return VENV_DIR / bin_dir / exe_name

def create_env():
    """
    Create a virtual environment in .venv/ if it doesn't exist.
    """
    if VENV_DIR.exists():
        print("✅ Virtual environment already exists at")
    else:
        print("🔧 Creating virtual environment...")
        venv.create(VENV_DIR, with_pip=True)
        print("✅ Virtual environment created.")

def install_deps():
    """
    Upgrade pip and install dependencies from requirements.txt into the venv.
    """
    py = get_python_executable()
    if not py.exists():
        sys.exit("[ERROR] Virtualenv python not found.")
    if not REQUIREMENTS.exists():
        sys.exit(f"[ERROR] requirements.txt not found at {REQUIREMENTS}")
    print("📦 Upgrading pip...")
    subprocess.check_call([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    print("📥 Installing requirements...")
    subprocess.check_call([str(py), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    print("✅ Dependencies installed.")

def run_main():
    """
    Execute main.py using the Python interpreter from the venv.
    """
    py = get_python_executable()
    if not py.exists():
        sys.exit("[ERROR] Virtualenv python not found.")
    if not MAIN_PY.exists():
        sys.exit(f"[ERROR] main.py not found at {MAIN_PY}")
    print("▶️ Running main.py...")
    subprocess.check_call([str(py), str(MAIN_PY)], cwd="src")

def main():
    """
    Full bootstrap process:
      1. Check Python version
      2. Create virtual environment
      3. Install dependencies
      4. Run main.py
    """
    check_python_version()
    create_env()
    install_deps()
    run_main()

if __name__ == "__main__":
    main()
