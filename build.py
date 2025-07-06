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

MODULES_DIR = BASE_DIR / 'scr' / 'modules'
MAIN_PY = BASE_DIR / 'scr' / 'main.py'
RESOURCES_DIR = BASE_DIR / 'scr'
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
    '--include-package=CTkScrollableDropdown',
    '--include-package=PIL',
    '--include-package=optipy',
    '--include-package=packaging',
    '--include-package=psutil',
    '--include-module=psutil._psutil_windows',
    '--include-package=pywinstyles',
    '--include-package=ratelimit',
    str(MAIN_PY)
]

# Expected hash placeholder (will be updated dynamically)
EXPECTED_HASHES = {}


def check_windows():
    if os.name != 'nt':
        print("[ERROR] This build script runs only on Windows.")
        sys.exit(1)


def check_python_version():
    if sys.version_info < MIN_PY_VERSION:
        print(f"[ERROR] Python {MIN_PY_VERSION[0]}.{MIN_PY_VERSION[1]}+ is required.")
        sys.exit(1)


def create_virtualenv():
    if not VENV_DIR.exists():
        print("🔧 Creating virtual environment...")
        venv.create(VENV_DIR, with_pip=True)
    else:
        print("✅ Virtual environment already exists.")


def install_dependencies():
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([str(PY_EXE), '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.check_call([str(PY_EXE), '-m', 'pip', 'install', '-r', 'requirements.txt'])
        subprocess.check_call([str(PY_EXE), '-m', 'pip', 'install', 'nuitka'])
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Dependency installation failed: {e}")
        sys.exit(e.returncode)


def compute_sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha.update(chunk)
    return sha.hexdigest()


def collect_hashes() -> dict:
    if not MODULES_DIR.is_dir():
        print(f"[ERROR] Modules directory not found: {MODULES_DIR}")
        sys.exit(1)
    hashes = {}
    for file in sorted(MODULES_DIR.glob('*.py')):
        hashes[file.stem] = compute_sha256(file)
    return hashes


def update_expected_hashes(hashes: dict):
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
    print("📁 Copying resources...")
    targets = [
        'modules', 'locales', 'ofb', 'png', os.path.join('files', 'CTkMessagebox')
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
    content = MAIN_PY.read_text(encoding='utf-8')
    cleared = re.sub(r'EXPECTED_HASHES\s*=\s*\{[^}]*\}', 'EXPECTED_HASHES = {}', content, flags=re.DOTALL)
    MAIN_PY.write_text(cleared, encoding='utf-8')
    print("🔄 EXPECTED_HASHES cleared.")


if __name__ == '__main__':
    check_windows()
    check_python_version()

    create_virtualenv()
    install_dependencies()

    hashes = collect_hashes()
    update_expected_hashes(hashes)

    print("🛠 Starting compilation...")
    ret = run_command(NUITKA_CMD)
    if ret != 0:
        print(f"[ERROR] Compilation failed with code {ret}")
        sys.exit(ret)
    print("✅ Compilation finished.")

    copy_resources()
    clear_expected_hashes()

    print("🎉 Build complete! Check dist/main.dist/main.exe")
