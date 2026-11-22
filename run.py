import os
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).parent.resolve()
VENV_DIR = BASE_DIR / ".venv"
REQUIREMENTS = BASE_DIR / "requirements.txt"
MAIN_PY = BASE_DIR / "src" / "main.py"
UV = [sys.executable, "-m", "uv"]


def fail(message, code=1):
    print(f"[ОШИБКА] {message}")
    raise SystemExit(code)


def get_python_executable():
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    exe_name = "python.exe" if os.name == "nt" else "python"
    return VENV_DIR / bin_dir / exe_name


def check_uv():
    result = subprocess.run(UV + ["--version"], cwd=BASE_DIR, check=False)
    if result.returncode != 0:
        print("📥 Установка uv...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"], cwd=BASE_DIR)
        subprocess.check_call(UV + ["--version"], cwd=BASE_DIR)


def create_env():
    if VENV_DIR.exists():
        print("✅ Виртуальное окружение уже существует")
        return

    print("🔧 Создание виртуального окружения...")
    subprocess.check_call(UV + ["venv", "--python", ">=3.10", str(VENV_DIR)], cwd=BASE_DIR)
    print("✅ Виртуальное окружение создано.")


def install_deps():
    py = get_python_executable()
    if not py.exists():
        fail("Python из виртуального окружения не найден.")
    if not REQUIREMENTS.exists():
        fail(f"requirements.txt не найден: {REQUIREMENTS}")

    print("📥 Установка зависимостей через uv...")
    subprocess.check_call(
        UV + ["pip", "install", "--python", str(py), "-r", str(REQUIREMENTS)],
        cwd=BASE_DIR,
    )
    print("✅ Зависимости установлены.")


def run_main():
    py = get_python_executable()
    if not py.exists():
        fail("Python из виртуального окружения не найден.")
    if not MAIN_PY.exists():
        fail(f"main.py не найден: {MAIN_PY}")

    print("▶️ Запуск main.py...")
    subprocess.check_call([str(py), str(MAIN_PY)], cwd=MAIN_PY.parent)


def main():
    check_uv()
    create_env()
    install_deps()
    run_main()


if __name__ == "__main__":
    main()
