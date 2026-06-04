from typing import TYPE_CHECKING, Optional, Literal

if TYPE_CHECKING:
    from context import *
import time
start_time = time.perf_counter()  

import json
import os
import re
import ctypes
import traceback
import sys
import shutil
import random
import webbrowser
import subprocess
import zipfile
import threading
from io import BytesIO
from locale import getdefaultlocale
from socket import create_connection
from datetime import datetime
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
from CTkScrollableDropdownPP import CTkScrollableDropdown
from psutil import virtual_memory
from pywinstyles import set_opacity
from ratelimit import rate_limited

ctk.deactivate_automatic_dpi_awareness()

def log(message: str, level: str = 'INFO', source: str = 'main') -> None:
    caller_name = sys._getframe(1).f_code.co_name  
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    output = f"[{timestamp} - {level} - {source}.{caller_name}] - {message}"

    with log_lock:
        print(output)
        with open("launcher.log", "a", encoding="utf-8") as f:
            f.write(output + "\n")


def execute_module(module_name: str) -> None:
    module_path = os.path.join("modules", f"{module_name}.py")

    try:
        with open(module_path, "rb") as f:
            code_bytes = f.read()
        exec(compile(code_bytes, module_path, "exec"), globals())

    except Exception:
        log(f"Error found in module {module_name}, exiting...", "ERROR")
        excepthook(*sys.exc_info())
        os._exit(0)


def excepthook(exc_type, exc_value, exc_tb) -> None:
    """Custom exception handler to log uncaught exceptions."""
    with log_lock:
        traceback.print_exception(exc_type, exc_value, exc_tb)
        with open("launcher.log", "a", encoding="utf-8") as f:
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)


if __name__ == "__main__":
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, "PLauncher")
    if kernel32.GetLastError() == 183:  
        os._exit(0)
    
    log_lock = threading.Lock()  
    if os.path.isfile("launcher.log"):
        os.remove("launcher.log")

    sys.excepthook = excepthook
    log("Добро пожаловать в дебаг...")

    for module in ["utils", "launcher_core", "loaders", "profiles", "window_utils", "skin", "translator", "java", "crash", "feedback", "settings_gui",
                   "notifications", "definitions"]:
        execute_module(module)

    log("Импортирование модулей завершено")

    TARGET_FIELD_CONFIG = {
        "Email": {"label_in_form_data": "Email", "payload_key": "email_payload"},
        "Subject": {"label_in_form_data": "Тема ", "payload_key": "subject_payload"},
        "Description": {"label_in_form_data": "Описание проблемы / предложения", "payload_key": "description_payload"}
    }

    EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

    log(f"Версия: {LauncherConfig.CURRENT_VERSION}")
    log(f"Частота обновления монитора: {LauncherConfig.FPS} Hz")
    log(f"Интернет статус: {LauncherConfig.IS_INTERNET}, Ping: {LauncherConfig.ping}")
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
            log("Файл изображения не найден", "ERROR")
            LauncherConfig.config["custom_image"] = default_config["custom_image"]
        
        if LauncherConfig.config["custom_skin"] and not os.path.isfile(LauncherConfig.config["custom_skin"]):
            log("Файл скина не найден", "ERROR")
            LauncherConfig.config["custom_skin"] = default_config["custom_skin"]
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

    ai_language = "ru" if language == "be" else language
    SYSTEM_PROMPT = (f"You are an expert assistant in analyzing Minecraft log files who responds only in this language: {ai_language}\n"
                     "Your task is:\n"
                     "1) Briefly (in one sentence) describe the cause of the crash\n"
                     "2) Suggest only those solutions that are directly related to the identified cause\n\n"
                     "Response format:\n"
                     "Cause in one sentence\n"
                     "Solutions numbered, each on a new line starting with >\n"
                     "Solutions should be written for an average Minecraft launcher user\n"
                     "Do not include general or universal advice unless it is directly related to the identified cause.\n\n"
                     "If the input is not a Minecraft log, respond exactly with `None` (without any additional text).\n"
                     "If the logs do not contain enough information to clearly determine the cause, respond exactly with `None` (without any additional text).")
    
    if LauncherConfig.version["profile"]:
        if not os.path.isdir(os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + LauncherConfig.version["profile"])):
            log("Папка профиля не найдена", "ERROR")
            LauncherConfig.version["profile"] = False
            save_version()
    
    create_minecraft_environment()

    log(f"Запускаем инициализацию интерфейса")
    execute_module("gui")
    root.mainloop()