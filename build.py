import os
import shutil
import subprocess
import sys
from pathlib import Path


if os.environ.get("CI") == "true" or sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


BASE_DIR = Path(__file__).parent.resolve()
VENV_DIR = BASE_DIR / ".venv"
REQUIREMENTS = BASE_DIR / "requirements.txt"
PY_EXE = VENV_DIR / "Scripts" / "python.exe"
MAIN_PY = BASE_DIR / "src" / "main.py"
RESOURCES_DIR = BASE_DIR / "src"
DIST_DIR = BASE_DIR / "dist" / "main.dist"
UV = shutil.which("uv")


def fail(message, code=1):
    print(f"[ОШИБКА] {message}")
    raise SystemExit(code)


def check_windows():
    if os.name != "nt":
        fail("Этот скрипт сборки работает только на Windows.")


def check_uv():
    if UV is None:
        fail("uv не найден. Установите uv: https://docs.astral.sh/uv/getting-started/installation/")


def create_env():
    if VENV_DIR.exists():
        print("✅ Виртуальное окружение уже существует.")
        return

    print("🔧 Создание виртуального окружения...")
    subprocess.check_call([UV, "venv", "--python", ">=3.10", str(VENV_DIR)], cwd=BASE_DIR)


def install_dependencies():
    if not REQUIREMENTS.exists():
        fail(f"requirements.txt не найден: {REQUIREMENTS}")

    print("📦 Установка зависимостей через uv...")
    try:
        subprocess.check_call(
            [UV, "pip", "install", "--python", str(PY_EXE), "-r", str(REQUIREMENTS), "nuitka"],
            cwd=BASE_DIR,
        )
    except subprocess.CalledProcessError as error:
        fail(f"Ошибка установки зависимостей: {error}", error.returncode)


def run_command(command):
    try:
        sys.stdout.flush()
        return subprocess.run(command, cwd=BASE_DIR, check=False).returncode
    except Exception as error:
        print(f"[ОШИБКА] Ошибка выполнения команды: {error}")
        return 1


def copy_resources():
    print("📁 Копирование ресурсов...")
    targets = ["modules", "locales", "ofb", "png", "icons", "themes"]

    for target in targets:
        source = RESOURCES_DIR / target
        destination = DIST_DIR / target
        if source.exists():
            shutil.copytree(source, destination, dirs_exist_ok=True)
            print(f"  → {destination.relative_to(DIST_DIR)}")
        else:
            print(f"  [ПРЕДУПРЕЖДЕНИЕ] Ресурс не найден: {source}")

    for filename in ("bridge.jar", "injector.jar", "log4jshell.xml"):
        source = RESOURCES_DIR / filename
        destination = DIST_DIR / filename
        if source.exists():
            shutil.copy2(source, destination)
            print(f"  → {filename}")
        else:
            print(f"  [ПРЕДУПРЕЖДЕНИЕ] Файл не найден: {source}")


def main():
    check_windows()
    check_uv()
    create_env()
    install_dependencies()

    command = [
        str(PY_EXE),
        "-m",
        "nuitka",
        "--standalone",
        "--assume-yes-for-downloads",
        "--windows-console-mode=disable",
        f"--output-dir={DIST_DIR.parent}",
        "--enable-plugin=tk-inter",
        str(MAIN_PY),
    ]

    print("🛠 Начало компиляции...")
    return_code = run_command(command)
    if return_code != 0:
        fail(f"Компиляция завершилась с ошибкой, код {return_code}", return_code)

    print("✅ Компиляция завершена.")
    copy_resources()
    print("🎉 Сборка завершена! Проверьте dist/main.dist/main.exe")


if __name__ == "__main__":
    main()
