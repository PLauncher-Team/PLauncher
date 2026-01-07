import os
import sys
import hashlib
import re
import subprocess
import venv
import shutil
from pathlib import Path

# Build script for Windows (build.py)
# Usage: python build.py

# Minimum supported Python version
MIN_PY_VERSION = (3, 10)

# --- Paths ---
BASE_DIR = Path(__file__).parent.resolve()
VENV_DIR = BASE_DIR / ".venv"
PY_EXE = VENV_DIR / "Scripts" / "python.exe"

MODULES_DIR = BASE_DIR / 'src' / 'modules'
MAIN_PY = BASE_DIR / 'src' / 'main.py'
RESOURCES_DIR = BASE_DIR / 'src'
DIST_DIR = BASE_DIR / 'dist' / 'main.dist'

# Nuitka command
NUITKA_CMD = [
    str(PY_EXE), '-m', 'nuitka',
    '--standalone',
    '--windows-console-mode=disable',
    f'--output-dir={DIST_DIR.parent}',
    '--enable-plugin=tk-inter',
    '--include-package=customtkinter',
    '--include-package=hPyT',
    '--include-package=minecraft_launcher_lib',
    '--include-package=requests',
    '--include-package=CTkMessagebox',
    '--include-package=CTkScrollableDropdownPP',
    '--include-package=PIL',
    '--include-package=optipy',
    '--include-package=packaging',
    '--include-module=psutil._psutil_windows',
    '--include-package=pywinstyles',
    '--include-package=ratelimit',
    str(MAIN_PY)
]

# Expected hash placeholder (will be updated dynamically)
EXPECTED_HASHES = {}


def check_windows():
    """Check if the script is running on Windows."""
    if os.name != 'nt':
        print("[ERROR] This build script runs only on Windows.")
        sys.exit(1)


def check_python_version():
    """Check if the Python version meets the minimum requirement."""
    if sys.version_info < MIN_PY_VERSION:
        print(f"[ERROR] Python {MIN_PY_VERSION[0]}.{MIN_PY_VERSION[1]}+ is required.")
        sys.exit(1)


def create_virtualenv():
    """Create a virtual environment if it doesn't exist."""
    if not VENV_DIR.exists():
        print("🔧 Creating virtual environment...")
        venv.create(VENV_DIR, with_pip=True)
    else:
        print("✅ Virtual environment already exists.")


def install_dependencies():
    """Install required dependencies from requirements.txt."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([str(PY_EXE), '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.check_call([str(PY_EXE), '-m', 'pip', 'install', '-r', 'requirements.txt'])
        subprocess.check_call([str(PY_EXE), '-m', 'pip', 'install', 'nuitka==2.7.16'])
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Dependency installation failed: {e}")
        sys.exit(e.returncode)


def compute_sha256(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha.update(chunk)
    return sha.hexdigest()


def collect_hashes() -> dict:
    """Collect SHA256 hashes of all Python files in the modules directory."""
    if not MODULES_DIR.is_dir():
        print(f"[ERROR] Modules directory not found: {MODULES_DIR}")
        sys.exit(1)
    hashes = {}
    for file in sorted(MODULES_DIR.glob('*.py')):
        hashes[file.stem] = compute_sha256(file)
    return hashes


def update_expected_hashes(hashes: dict):
    """Update the EXPECTED_HASHES dictionary in main.py with computed hashes."""
    new_block = ["EXPECTED_HASHES = {"]
    for name, h in hashes.items():
        new_block.append(f'    "{name}": "{h}",')
    new_block.append('}')
    block_text = "\n".join(new_block)

    content = MAIN_PY.read_text(encoding='utf-8')
    pattern = re.compile(r'EXPECTED_HASHES\s*=\s*\{[^}]*\}', re.DOTALL)
    if not pattern.search(content):
        print("[ERROR] EXPECTED_HASHES block not found in main.py.")
        sys.exit(1)
    updated = pattern.sub(block_text, content)
    MAIN_PY.write_text(updated, encoding='utf-8')
    print("✅ EXPECTED_HASHES updated.")


def run_command(cmd: list) -> int:
    """Run a shell command and print its output in real-time."""
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            print(line, end='')
        proc.wait()
        return proc.returncode
    except Exception as e:
        print(f"[ERROR] Command execution failed: {e}")
        return 1


def copy_resources():
    """Copy required resource files and directories to the distribution folder."""
    print("📁 Copying resources...")
    targets = [
        'modules', 'locales', 'ofb', 'png', os.path.join('files', 'CTkMessagebox'), "themes"
    ]
    for t in targets:
        src = RESOURCES_DIR / t
        dst = DIST_DIR / Path(t).name
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print(f"  → {dst.relative_to(DIST_DIR)}")
        else:
            print(f"  [WARN] Resource not found: {src}")

    for fname in ('bridge.jar', 'injector.jar'):
        src = RESOURCES_DIR / fname
        dst = DIST_DIR / fname
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  → {fname}")
        else:
            print(f"  [WARN] File not found: {src}")


def clear_expected_hashes():
    """Clear the EXPECTED_HASHES dictionary in main.py (set to empty)."""
    content = MAIN_PY.read_text(encoding='utf-8')
    cleared = re.sub(r'EXPECTED_HASHES\s*=\s*\{[^}]*\}', 'EXPECTED_HASHES = {}', content, flags=re.DOTALL)
    MAIN_PY.write_text(cleared, encoding='utf-8')
    print("🔄 EXPECTED_HASHES cleared.")


def ask_insert_hashes() -> bool:
    """Ask user whether to insert hashes into main.py."""
    while True:
        response = input("Insert hashes into main.py? [Y/n]: ").strip().upper()
        if response == '':
            return True  # Default: Y
        if response in ['Y', 'YES']:
            return True
        if response in ['N', 'NO']:
            return False
        print("Please enter Y or N")


if __name__ == '__main__':
    check_windows()
    check_python_version()

    create_virtualenv()
    install_dependencies()

    # Ask user whether to insert hashes
    hashes = collect_hashes()
    if ask_insert_hashes():
        update_expected_hashes(hashes)
    else:
        print("⏭ Skipping hash insertion...")

    print("🛠 Starting compilation...")
    ret = run_command(NUITKA_CMD)
    if ret != 0:
        print(f"[ERROR] Compilation failed with code {ret}")
        sys.exit(ret)
    print("✅ Compilation finished.")

    copy_resources()

    # Only clear hashes if they were inserted
    if hashes:
        clear_expected_hashes()
    else:
        print("⏭ Skipping hash cleanup...")

    print("🎉 Build complete! Check dist/main.dist/main.exe")