from __future__ import annotations

from typing import Optional, Literal, Callable
from pathlib import Path
from packaging.version import Version

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

def enable_ansi_colors() -> None:
    if sys.platform != "win32":
        return

    try:
        from ctypes import wintypes

        get_std_handle = kernel32.GetStdHandle
        get_std_handle.argtypes = [wintypes.DWORD]
        get_std_handle.restype = wintypes.HANDLE

        get_console_mode = kernel32.GetConsoleMode
        get_console_mode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        get_console_mode.restype = wintypes.BOOL

        set_console_mode = kernel32.SetConsoleMode
        set_console_mode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        set_console_mode.restype = wintypes.BOOL

        stdout_handle = get_std_handle(-11)
        mode = wintypes.DWORD()

        if stdout_handle and get_console_mode(stdout_handle, ctypes.byref(mode)):
            set_console_mode(stdout_handle, mode.value | 0x0004)
    except Exception:
        pass

def log(message: str="LOG", level: str = 'INFO', exc_info=()) -> None:
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

from plauncher import ui_runtime
from plauncher.controllers import CrashLogWindow, JavaController, LoaderController, ProfileController, SettingsController, SkinController
from plauncher.config import ConfigStore, DEFAULT_SETTINGS, DEFAULT_VERSION, VersionStore
from plauncher.services import CrashLogAnalyzerService, JavaRuntimeService, LoaderCatalogService, LoaderInstallationService, MinecraftEnvironmentService, MinecraftLaunchService, MinecraftProcessService, ProfileService, SkinTexturePackService, TranslationService
from plauncher.state import GuiOption, LauncherConfig, LaunchOptions
from plauncher.settings import LauncherSettingsService

start_time = time.perf_counter()

kernel32 = ctypes.windll.kernel32
mutex = kernel32.CreateMutexW(None, False, "PLauncher")
if kernel32.GetLastError() == 183:
    os._exit(0)

log_lock = threading.Lock()
enable_ansi_colors()
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
from ratelimit import rate_limited
from json_repair import repair_json

import pywinstyles

def fixed_init(self, widget: int, func: Callable, char_limit: int=36767) -> None:
    import platform
    from ctypes import windll, c_buffer, WINFUNCTYPE, c_uint64, sizeof
    from ctypes.wintypes import DWORD
    try:
        hwnd = widget.winfo_id()
    except:
        hwnd = widget
    if not isinstance(hwnd, int):
        raise ValueError("widget ID should be passed, not the widget name.")

    if platform.architecture()[0] == "32bit":
        GetWindowLong = windll.user32.GetWindowLongW
        SetWindowLong = windll.user32.SetWindowLongW
        typ = DWORD

    if platform.architecture()[0] == "64bit":
        GetWindowLong = windll.user32.GetWindowLongPtrA
        SetWindowLong = windll.user32.SetWindowLongPtrA
        typ = c_uint64

    prototype = WINFUNCTYPE(typ, typ, typ, typ, typ)
    WM_DROP_FILES = 0x233
    GWL_WND_PROC = -4
    create_buffer = c_buffer
    func_DragQueryFile = (windll.shell32.DragQueryFile)

    def py_drop_func(hwnd, msg, wp, lp):
        global files
        if msg == WM_DROP_FILES:
            count = func_DragQueryFile(typ(wp), -1, None, None)
            file_buffer = create_buffer(char_limit)
            files = []
            for i in range(count):
                func_DragQueryFile(typ(wp), i, file_buffer, sizeof(file_buffer))
                try:
                    drop_name = file_buffer.value.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        drop_name = file_buffer.value.decode("windows-1251")
                    except UnicodeDecodeError:
                        drop_name = file_buffer.value.decode("mbcs")
                files.append(drop_name)
            func(files)
            windll.shell32.DragFinish(typ(wp))

        return windll.user32.CallWindowProcW(
            *map(typ, (globals()[old], hwnd, msg, wp, lp))
        )

    limit_num = 10
    for i in range(limit_num):
        if i + 1 == limit_num:
            raise OverflowError("DND limit reached for this session!")
        owp = f"old_wnd_proc_{i}"
        if owp not in globals():
            old, new = owp, f"new_wnd_proc_{i}"
            break

    globals()[old] = None
    globals()[new] = prototype(py_drop_func)

    windll.shell32.DragAcceptFiles(hwnd, True)
    globals()[old] = GetWindowLong(hwnd, GWL_WND_PROC)
    SetWindowLong(hwnd, GWL_WND_PROC, globals()[new])

pywinstyles.apply_dnd.__init__ = fixed_init
del fixed_init

log("Импорт библиотек завершен")

ctk.deactivate_automatic_dpi_awareness()


def run() -> None:
    ui_runtime.configure(**globals())
    LauncherConfig.ping = ui_runtime.check_internet_connection()
    LauncherConfig.IS_INTERNET = bool(LauncherConfig.ping)
    LauncherConfig.FPS = ui_runtime.get_refresh_rate()
    LauncherConfig.MAX_MEMORY_GB = ui_runtime.get_available_memory()
    LauncherConfig.USER_AGENT = f"PLauncher-Team/PLauncher/{LauncherConfig.CURRENT_VERSION}"

    log(f"Версия: {LauncherConfig.CURRENT_VERSION}")
    log(f"Частота обновления монитора: {LauncherConfig.FPS} Hz")
    log(f"Интернет статус: {LauncherConfig.IS_INTERNET}, Ping: {LauncherConfig.ping}ms")
    log(f"Объём ОЗУ: {LauncherConfig.MAX_MEMORY_GB} GB")

    settings_service = LauncherSettingsService(
        config_path="data.json",
        minecraft_directory=Path(os.getenv("APPDATA")) / ".minecraft",
        memory_megabytes=min(max(LauncherConfig.MAX_MEMORY_GB * 1024 // 2, 512), 4096),
        logger=log,
    )
    LauncherConfig.config, config_file_exists = settings_service.load_config("themes")
    default_config = settings_service.defaults
    config_store = settings_service.config_store

    def save_config() -> None:
        settings_service.config = LauncherConfig.config
        settings_service.save_config()

    def save_version() -> None:
        settings_service.version = LauncherConfig.version
        settings_service.save_version()

    log("data.json найден, настройки загружены" if config_file_exists else "data.json не найден, был создан новый")

    if not LauncherConfig.config["mine_path"] or LauncherConfig.config["default_path"] or not os.path.isdir(LauncherConfig.config["mine_path"]):
        LaunchOptions.minecraft_path = os.path.join(os.getenv('APPDATA'), ".minecraft")
        LauncherConfig.config["mine_path"] = ""
        save_config()
        if not os.path.isdir(LaunchOptions.minecraft_path):
            os.makedirs(LaunchOptions.minecraft_path)
    else:
        LaunchOptions.minecraft_path = LauncherConfig.config["mine_path"]

    profile_service = ProfileService(LaunchOptions.minecraft_path)

    if LauncherConfig.config["java_paths"]:
        for java_path in LauncherConfig.config["java_paths"]:
            if not os.path.isfile(java_path):
                LauncherConfig.config["java_paths"].remove(java_path)
                log(f"{java_path} не найдена", "ERROR")

    if os.path.isfile("java_temp.zip"):
        os.remove("java_temp.zip")

    LauncherConfig.version, version_file_exists = settings_service.load_version(LaunchOptions.minecraft_path)
    version_store = settings_service.version_store
    log("version.json файл найден, настройки загружены" if version_file_exists else "version.json не найден, был создан новый")

    LaunchOptions.latest_version = LauncherConfig.version["version"]

    language_manager = TranslationService(
        "locales",
        language=LauncherConfig.config["language"],
        settings=LauncherConfig.config,
        save_settings=save_config,
        logger=log,
    )
    language = language_manager.language
    log_analyzer = CrashLogAnalyzerService(
        http_client=requests,
        user_agent=LauncherConfig.USER_AGENT,
        logger=log,
    )

    def update_java_versions(versions: list[int]) -> None:
        LaunchOptions.available_major_versions = versions
        ui_runtime.java_combobox.configure(values=ui_runtime.java_controller.get_java_options())

    java_runtime_service = JavaRuntimeService(
        minecraft_directory=LaunchOptions.minecraft_path,
        user_agent=LauncherConfig.USER_AGENT,
        online=LauncherConfig.IS_INTERNET,
        http_client=requests,
        logger=log,
        status_message=language_manager.get("main.mcl_status.install_java_runtime"),
        versions_loaded=update_java_versions,
    )

    loader_installer = LoaderInstallationService(
        minecraft_directory=LaunchOptions.minecraft_path,
        java_runtime=java_runtime_service,
        available_java_versions=lambda: LaunchOptions.available_major_versions,
        launcher_api=mcl,
        optifine_api=optipy,
        http_client=requests,
        logger=log,
        process_changed=lambda process: setattr(LaunchOptions, "loader_process", process),
    )

    loader_catalog = LoaderCatalogService(
        launcher_api=mcl,
        optifine_api=optipy,
        version_parser=Version,
        logger=log,
    )

    launch_service = MinecraftLaunchService(
        minecraft_directory=LaunchOptions.minecraft_path,
        launcher_directory=os.getcwd(),
        launcher_api=mcl,
        java_runtime=java_runtime_service,
        online=LauncherConfig.IS_INTERNET,
        logger=log,
    )
    process_service = MinecraftProcessService(job_api=win32job, process_api=subprocess)
    log(f"Язык лаунчера: {language}")

    if LauncherConfig.version["profile"]:
        if not os.path.isdir(os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + LauncherConfig.version["profile"])):
            log("Папка профиля не найдена", "ERROR")
            LauncherConfig.version["profile"] = False
            save_version()

    environment_service = MinecraftEnvironmentService(LaunchOptions.minecraft_path)
    environment_service.ensure()

    log(f"Запускаем инициализацию интерфейса")
    ui_runtime.configure(**globals())
    ui_runtime.configure(**locals())
    ui_runtime.configure(
        default_config=default_config,
        config_store=config_store,
        version_store=version_store,
        profile_service=profile_service,
        language_manager=language_manager,
        language=language,
        log_analyzer=log_analyzer,
        MinecraftTexturePackCreator=SkinTexturePackService,
        loader_installer=loader_installer,
        loader_catalog=loader_catalog,
        launch_service=launch_service,
        process_service=process_service,
        environment_service=environment_service,
    )
    gui_components = ui_runtime.initialize_gui()
    ui_runtime.apply_hover_border()
    log("Запускаем сетевые потоки...")
    threading.Thread(target=java_runtime_service.get_available_major_versions, daemon=True).start()
    threading.Thread(target=ui_runtime.thread_load_versions, daemon=True).start()
    threading.Thread(target=gui_components["skin_controller"].set_skin, daemon=True).start()
    gui_components["loader_controller"].load_catalogs()
    gui_components["root"].mainloop()
