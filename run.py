import sys
import os
import subprocess
import venv
from pathlib import Path


MIN_PY = (3, 10)


BASE_DIR = Path(__file__).parent.resolve()
VENV_DIR = BASE_DIR / ".venv"
REQUIREMENTS = BASE_DIR / "requirements.txt"
MAIN_PY = BASE_DIR / "src" / "main.py"


def check_python_version():
    if sys.version_info < MIN_PY:
        sys.exit(f"[ОШИБКА] Требуется Python {MIN_PY[0]}.{MIN_PY[1]}+, обнаружен {sys.version_info.major}.{sys.version_info.minor}")


def get_python_executable():
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    exe_name = "python.exe" if os.name == "nt" else "python3"
    return VENV_DIR / bin_dir / exe_name


def create_env():
    if VENV_DIR.exists():
        print("✅ Виртуальное окружение уже существует")
    else:
        print("🔧 Создание виртуального окружения...")
        venv.create(VENV_DIR, with_pip=True)
        print("✅ Виртуальное окружение создано.")


def install_deps():
    py = get_python_executable()
    if not py.exists():
        sys.exit("[ОШИБКА] Python из виртуального окружения не найден.")
    if not REQUIREMENTS.exists():
        sys.exit(f"[ОШИБКА] requirements.txt не найден: {REQUIREMENTS}")
    print("📦 Обновление pip...")
    subprocess.check_call([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    print("📥 Установка зависимостей...")
    subprocess.check_call([str(py), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    print("✅ Зависимости установлены.")


def run_main():
    py = get_python_executable()
    if not py.exists():
        sys.exit("[ОШИБКА] Python из виртуального окружения не найден.")
    if not MAIN_PY.exists():
        sys.exit(f"[ОШИБКА] main.py не найден: {MAIN_PY}")
    print("▶️ Запуск main.py...")
    subprocess.check_call([str(py), str(MAIN_PY)], cwd="src")


def main():
    check_python_version()
    create_env()
    install_deps()
    run_main()

if __name__ == "__main__":
    main()