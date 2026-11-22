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
UV = [sys.executable, "-m", "uv"]


def fail(message, code=1):
    print(f"[ERROR] {message}")
    raise SystemExit(code)


def check_windows():
    if os.name != "nt":
        fail("This build script only works on Windows.")


def check_uv():
    result = subprocess.run(UV + ["--version"], cwd=BASE_DIR, check=False)
    if result.returncode != 0:
        print("📥 Installing uv...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"], cwd=BASE_DIR)
        subprocess.check_call(UV + ["--version"], cwd=BASE_DIR)


def create_env():
    if VENV_DIR.exists():
        print("✅ Virtual environment already exists.")
        return

    print("🔧 Creating virtual environment...")
    subprocess.check_call(UV + ["venv", "--python", ">=3.10", str(VENV_DIR)], cwd=BASE_DIR)


def install_dependencies():
    if not REQUIREMENTS.exists():
        fail(f"requirements.txt не найден: {REQUIREMENTS}")

    print("📦 Installing dependencies with uv...")
    try:
        subprocess.check_call(
            UV + ["pip", "install", "--python", str(PY_EXE), "-r", str(REQUIREMENTS), "nuitka"],
            cwd=BASE_DIR,
        )
    except subprocess.CalledProcessError as error:
        fail(f"Failed to install dependencies: {error}", error.returncode)


def run_command(command):
    try:
        sys.stdout.flush()
        return subprocess.run(command, cwd=BASE_DIR, check=False).returncode
    except Exception as error:
        print(f"[ERROR] Command execution failed: {error}")
        return 1


def prepare_tcl_libraries():
    try:
        import tkinter

        interpreter = tkinter.Tcl()
        tcl_library = interpreter.eval("info library")
        if not tcl_library.startswith("//zipfs:/"):
            return []

        interpreter.eval("package require Tk")
        tk_library = interpreter.eval("set tk_library")
    except Exception as error:
        fail(f"Failed to locate Tcl/Tk libraries in ZIPFS: {error}")

    extraction_dir = BASE_DIR / "build" / "tcl-runtime"
    if extraction_dir.exists():
        shutil.rmtree(extraction_dir)
    extraction_dir.mkdir(parents=True)

    try:
        interpreter.call("file", "copy", "-force", tcl_library, str(extraction_dir))
        interpreter.call("file", "copy", "-force", tk_library, str(extraction_dir))
    except Exception as error:
        fail(f"Failed to extract Tcl/Tk libraries from ZIPFS: {error}")

    tcl_dir = extraction_dir / Path(tcl_library).name
    tk_dir = extraction_dir / Path(tk_library).name

    required_files = (
        tcl_dir / "init.tcl",
        tk_dir / "tk.tcl",
        tk_dir / "dialog.tcl",
    )
    missing_files = [str(path) for path in required_files if not path.is_file()]
    if missing_files:
        fail("Tcl/Tk extraction is incomplete: " + ", ".join(missing_files))

    print("📦 Extracted Tcl/Tk libraries from Python ZIPFS.")
    return [
        f"--tcl-library-dir={tcl_dir}",
        f"--tk-library-dir={tk_dir}",
    ]


def copy_resources():
    print("📁 Copying resources...")
    targets = ["modules", "locales", "ofb", "png", "icons", "themes"]

    for target in targets:
        source = RESOURCES_DIR / target
        destination = DIST_DIR / target
        if source.exists():
            shutil.copytree(source, destination, dirs_exist_ok=True)
            print(f"  → {destination.relative_to(DIST_DIR)}")
        else:
            print(f"  [WARNING] Resource not found: {source}")

    for filename in ("bridge.jar", "injector.jar", "log4jshell.xml"):
        source = RESOURCES_DIR / filename
        destination = DIST_DIR / filename
        if source.exists():
            shutil.copy2(source, destination)
            print(f"  → {filename}")
        else:
            print(f"  [WARNING] File not found: {source}")


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

    command.extend(prepare_tcl_libraries())

    print("🛠 Starting compilation...")
    return_code = run_command(command)
    if return_code != 0:
        fail(f"Компиляция завершилась с ошибкой, код {return_code}", return_code)

    print("✅ Compilation completed.")
    copy_resources()
    print("🎉 Build completed! Check dist/main.dist/main.exe")


if __name__ == "__main__":
    main()
