from typing import TYPE_CHECKING, Optional, Literal

if TYPE_CHECKING:
    from context import *

def excepthook(exc_type, exc_value, exc_tb) -> None:
    is_main = threading.current_thread().name == "MainThread"
    log(level="FATAL" if is_main else "ERROR", exc_info=[exc_type, exc_value, exc_tb])

    level_colors = {
        "FATAL": "\033[31;1m",
        "ERROR": "\033[31m",
    }

    error_color = level_colors.get("FATAL" if is_main else "ERROR")

    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    tb_text = "".join(tb_lines)

    with log_lock:
        print(f"{error_color}{tb_text}\033[0m", end="")

        with open("launcher.log", "a", encoding="utf-8") as f:
            f.write(tb_text)

    if is_main:
        os._exit(1)

def log(message: str="LOG", level: str = 'INFO', exc_info=()) -> None:
    os.system("")

    level_colors = {
        "FATAL": "\033[31;1m",
        "ERROR": "\033[31m",
        "WARNING": "\033[33m",
        "INFO": "\033[36m"
    }
    color_reset = "\033[0m"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    if exc_info:
        exc_type, exc_value, exc_tb = exc_info
        tb = exc_tb
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        code = frame.f_code
        filename = os.path.relpath(code.co_filename)
        func_name = code.co_name
        lineno = tb.tb_lineno
        thread_name = threading.current_thread().name.split(" (")[0]
        message = f"{exc_type.__name__}: {exc_value}"
    else:
        caller_frame = sys._getframe(1)
        caller_code = caller_frame.f_code
        filename = os.path.relpath(caller_code.co_filename)
        func_name = caller_code.co_name
        lineno = caller_frame.f_lineno
        thread_name = threading.current_thread().name.split(" (")[0]

    pycharm_link = f'File "{filename}", line {lineno}'
    meta = f"{level:<7} │ {thread_name:<10} │ {pycharm_link[-45:]:<45} │ {func_name + '()':<30}"

    lvl_upper = level.upper()
    level_color = level_colors.get(lvl_upper, color_reset)

    if lvl_upper in ("ERROR", "FATAL"):
        output_console = f"{level_color}[{timestamp}] │ {meta} │ {message}{color_reset}"
    else:
        console_meta = f"{level_color}{level:<7}{color_reset} │ {thread_name:<10} │ {pycharm_link:<45} │ {func_name + '()':<30}"
        output_console = f"[{timestamp}] │ {console_meta} │ {message}"

    output_file = f"[{timestamp}] │ {meta} │ {message}"

    with log_lock:
        print(output_console)

    with open("launcher.log", "a", encoding="utf-8") as f:
        f.write(output_file + "\n")

import time
import ctypes
import threading
import os
import sys
from datetime import datetime

start_time = time.perf_counter()

kernel32 = ctypes.windll.kernel32
mutex = kernel32.CreateMutexW(None, False, "PLauncher")
if kernel32.GetLastError() == 183:
    os._exit(0)

log_lock = threading.Lock()
if os.path.isfile("launcher.log"):
    os.remove("launcher.log")

sys.excepthook = excepthook
threading.excepthook = lambda args: excepthook(args.exc_type, args.exc_value, args.exc_traceback)
log("Добро пожаловать в дебаг...")

import json
import re
import traceback
import shutil
import random
import webbrowser
import subprocess
try:
    import tomllib
except ImportError:
    import tomli as tomllib
import zipfile
import hashlib
from io import BytesIO
from locale import getdefaultlocale
from socket import create_connection
from uuid import uuid4
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES

import minecraft_launcher_lib as mcl
import customtkinter as ctk
import requests
import packaging
import hPyT
import win32job
import win32con
import win32api
import optipy
import PIL
import PIL.ImageDraw
import concurrent
from requests_cache import CachedSession
from CTkScrollableDropdownPP import CTkScrollableDropdown
from psutil import virtual_memory
from pywinstyles import set_opacity
from ratelimit import rate_limited
from json_repair import repair_json

log("Импорт библиотек завершен")

ctk.deactivate_automatic_dpi_awareness()

def execute_module(module_name: str) -> None:
    module_path = os.path.join("modules", f"{module_name}.py")

    try:
        with open(module_path, "rb") as f:
            code_bytes = f.read()
        exec(compile(code_bytes, module_path, "exec"), globals())

    except Exception:
        log(f"Ошибка в модуле {module_name}, выход...", "FATAL")
        excepthook(*sys.exc_info())


if __name__ == "__main__":
    for module in ["utils", "launcher_core", "loaders", "profiles", "window_utils", "skin", "translator", "java", "crash", "settings_gui",
                   "notifications", "definitions", "mod_viewer_gui", "mod_viewer"]:
        execute_module(module)

    log("Динамическая загрузка модулей завершена")

    log(f"Версия: {LauncherConfig.CURRENT_VERSION}")
    log(f"Частота обновления монитора: {LauncherConfig.FPS} Hz")
    log(f"Интернет статус: {LauncherConfig.IS_INTERNET}, Ping: {LauncherConfig.ping}ms")
    log(f"Объём ОЗУ: {LauncherConfig.MAX_MEMORY_GB} GB")

    default_config = {
        "name": "Steve",
        "debug": False,
        "release": True,
        "snapshot": False,
        "old_beta": False,
        "old_alpha": False,
        "check_files": True,
        "random_theme": True,
        "selected_theme": 1,
        "custom_image": "",
        "custom_theme": "",
        "hide": False,
        "mine_path": "",
        "memory_args": str(min(max(LauncherConfig.MAX_MEMORY_GB * 1024 // 2, 512), 4096)),
        "custom_args": "",
        "ely_by": False,
        "custom_skin": "",
        "default_skin": True,
        "language": "",
        "default_path": True,
        "java_paths": [],
        "java": "Latest"
    }

    if os.path.isfile("data.json"):
        with open("data.json") as f:
            LauncherConfig.config = json.load(f)

        for t in default_config:
            if t not in LauncherConfig.config:
                log(f"Новый параметр настроек: {t}={default_config[t]}")
                LauncherConfig.config[t] = default_config[t]

        if LauncherConfig.config["custom_image"] and not os.path.isfile(LauncherConfig.config["custom_image"]):
            log(f"Файл изображения не найден: {LauncherConfig.config['custom_image']}", "WARNING")
            LauncherConfig.config["custom_image"] = default_config["custom_image"]

        if LauncherConfig.config["custom_skin"] and not os.path.isfile(LauncherConfig.config["custom_skin"]):
            log(f"Файл скина не найден: {LauncherConfig.config['custom_skin']}", "WARNING")
            LauncherConfig.config["custom_skin"] = default_config["custom_skin"]

        if LauncherConfig.config["custom_theme"] and not os.path.isfile(LauncherConfig.config["custom_theme"]):
            log(f"Файл темы не найден: {LauncherConfig.config['custom_theme']}", "WARNING")
            LauncherConfig.config["custom_theme"] = default_config["custom_theme"]
        
        LauncherConfig.config = dict(sorted(LauncherConfig.config.items()))
        save_config()
        log("data.json найден, настройки загружены")
    else:
        LauncherConfig.config = default_config
        save_config()
        log("data.json не найден, был создан новый")

    if not LauncherConfig.config["mine_path"] or LauncherConfig.config["default_path"] or not os.path.isdir(LauncherConfig.config["mine_path"]):
        LaunchOptions.minecraft_path = os.path.join(os.getenv('APPDATA'), ".minecraft")
        LauncherConfig.config["mine_path"] = ""
        save_config()
        if not os.path.isdir(LaunchOptions.minecraft_path):
            os.makedirs(LaunchOptions.minecraft_path)
    else:
        LaunchOptions.minecraft_path = LauncherConfig.config["mine_path"]

    if LauncherConfig.config["java_paths"]:
        for java_path in LauncherConfig.config["java_paths"]:
            if not os.path.isfile(java_path):
                LauncherConfig.config["java_paths"].remove(java_path)
                log(f"{java_path} не найдена", "ERROR")

    if os.path.isfile("java_temp.zip"):
        os.remove("java_temp.zip")

    default_version = {
        "download": [],
        "not_comp": [],
        "version": "",
        "profile": False
    }

    version_file = os.path.join(LaunchOptions.minecraft_path, "version.json")
    if os.path.isfile(version_file):
        with open(version_file) as f:
            LauncherConfig.version = json.load(f)

        for t in default_version:
            if t not in LauncherConfig.version:
                log(f"Новый параметр настроек: {t}={default_version[t]}")
                LauncherConfig.version[t] = default_version[t]

        save_version()
        log("version.json файл найден, настройки загружены")
    else:
        LauncherConfig.version = default_version
        save_version()
        log("version.json не найден, был создан новый")

    LaunchOptions.latest_version = LauncherConfig.version["version"]

    language_manager = Translator(LauncherConfig.config["language"])
    language = language_manager.language
    log(f"Язык лаунчера: {language}")

    if LauncherConfig.version["profile"]:
        if not os.path.isdir(os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + LauncherConfig.version["profile"])):
            log("Папка профиля не найдена", "ERROR")
            LauncherConfig.version["profile"] = False
            save_version()

    create_minecraft_environment()

    log(f"Запускаем инициализацию интерфейса")
    execute_module("gui")
    root.mainloop()
