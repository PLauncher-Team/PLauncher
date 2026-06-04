import os
import sys
import subprocess
import venv
import shutil
from pathlib import Path





if os.environ.get('CI') == 'true' or sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')


MIN_PY_VERSION = (3, 10)


BASE_DIR = Path(__file__).parent.resolve()
VENV_DIR = BASE_DIR / ".venv"
PY_EXE = VENV_DIR / "Scripts" / "python.exe"

MAIN_PY = BASE_DIR / 'src' / 'main.py'
RESOURCES_DIR = BASE_DIR / 'src'
DIST_DIR = BASE_DIR / 'dist' / 'main.dist'


NUITKA_CMD = [
    str(PY_EXE), '-m', 'nuitka',
    '--standalone',
    "--assume-yes-for-downloads",
    '--windows-console-mode=disable',
    f'--output-dir={DIST_DIR.parent}',
    '--enable-plugin=tk-inter',
    '--include-package=customtkinter',
    '--include-package=hPyT',
    '--include-package=minecraft_launcher_lib',
    '--include-package=requests',
    '--include-package=CTkScrollableDropdownPP',
    '--include-package=PIL',
    '--include-package=optipy',
    '--include-package=packaging',
    '--include-module=psutil._psutil_windows',
    '--include-package=pywinstyles',
    '--include-package=ratelimit',
    str(MAIN_PY)
]


def check_windows():
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


if __name__ == '__main__':
    check_windows()
    check_python_version()

    create_virtualenv()
    install_dependencies()

    print("🛠 Starting compilation...")
    ret = run_command(NUITKA_CMD)
    if ret != 0:
        print(f"[ERROR] Compilation failed with code {ret}")
        sys.exit(ret)
    print("✅ Compilation finished.")

    copy_resources()

    print("🎉 Build complete! Check dist/main.dist/main.exe")
