"""
VERSION 1.51
Python 3.13
By Code_po_vene team
"""
from time import perf_counter, time
start_time = perf_counter()

import json
import os
import re
import ctypes
import traceback
import hashlib
import sys
from io import BytesIO
from locale import getdefaultlocale
from random import choice, randint
from shutil import copy, copytree, rmtree
from socket import create_connection
from subprocess import (
    CalledProcessError,
    PIPE,
    Popen,
    STDOUT,
    TimeoutExpired,
    run,
    CREATE_NO_WINDOW,
)
from datetime import datetime
import threading
from tkinter import filedialog, messagebox, TclError
from uuid import uuid4

import minecraft_launcher_lib as mcl
import customtkinter as ctk
import requests
import hPyT
import win32con
import win32api
from bs4 import BeautifulSoup
from CTkMessagebox import CTkMessagebox
from CTkScrollableDropdown import CTkScrollableDropdown
from optipy import getVersion, getVersionList
from packaging.version import Version
from PIL import Image
from psutil import virtual_memory
from pywinstyles import set_opacity
from ratelimit import rate_limited


def log(message, level='INFO'):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    output = f"[{timestamp} - {level}] - {message}"
    with log_lock:
        print(output)
        with open("launcher.log", "a", encoding="utf-8") as f:
            f.write(output + "\n")


EXPECTED_HASHES = {}

def compute_sha256(path: str) -> str:
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def execute_module(module_name: str):
    module_path = os.path.join("modules", f"{module_name}.py")
    
    if EXPECTED_HASHES:
        expected = EXPECTED_HASHES.get(module_name)
        actual = compute_sha256(module_path)
        if actual != expected:
            sys.exit(1)

    try:
        with open(module_path, encoding="utf-8") as file:
            code = file.read()
        exec(code, globals())
    except Exception:
        log(f"В модуле {module_name} найдена ошибка, завершаем работу...", "ERROR")
        excepthook(*sys.exc_info())
        os._exit(0)


def excepthook(exc_type, exc_value, exc_tb):
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
    
    minecraft_log_file = None

    sys.excepthook = excepthook
    log("Добро пожаловать в debug...")
    
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    

    for module in ["utils", "launcher_core", "loaders", "profiles", "window_utils", "skin", "translator", "java", "crash", "feedback", "settings_gui"]:
        execute_module(module)
    
    log("Импортирование модулей завершено")

    launcher_path = os.path.join(os.getenv('APPDATA'), "pylauncher")

    IS_INTERNET = check_internet_connection()
    FPS = get_max_refresh_rate()
    MAX_MEMORY_GB = get_available_memory()
    FORM_VIEW_URL = "https://docs.google.com/forms/d/e/1FAIpQLScHheNuuIixaus6D_2iNRMNIMrbJWmiq-Rc7XKNf5lBo0f3NA/viewform"
    FORM_SUBMIT_URL = "https://docs.google.com/forms/d/e/1FAIpQLScHheNuuIixaus6D_2iNRMNIMrbJWmiq-Rc7XKNf5lBo0f3NA/formResponse"
    
    TARGET_FIELD_CONFIG = {
        "Email": {"label_in_form_data": "Email", "payload_key": "email_payload"},
        "Subject": {"label_in_form_data": "Тема ", "payload_key": "subject_payload"},
        "Description": {"label_in_form_data": "Описание проблемы / предложения", "payload_key": "description_payload"}
    }
    
    EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

    is_running = False

    minecraft_process = None
    loader_process = None
    step = None
    progress = None
    total_files = 0
    select_page = None
    versions = []
    old_types_versions = []

    log(f"Наивысшая частота монитора: {FPS}гц")
    log(f"Статус интернета: {IS_INTERNET}")
    log(f"Размер ОЗУ: {MAX_MEMORY_GB}ГБ")

    default_config = {
        "name": "Steve",
        "debug": False,
        "release": True,
        "snapshot": False,
        "old_beta": False,
        "old_alpha": False,
        "check_files": True,
        "theme_type": "default",
        "random_theme": True,
        "selected_theme": 1,
        "custom_theme": "",
        "hide": False,
        "mine_path": "",
        "default": True,
        "memory_args": str(max(get_available_memory() * 1024 // 2, 512)),
        "custom_args": "",
        "ely_by": False,
        "custom_skin": "",
        "default_skin": True,
        "language": "",
        "default_path": True,
        "java_paths": {},
        "java": None
    }

    if os.path.isfile("data.json"):
        with open("data.json") as f:
            config = json.load(f)
        for t in default_config:
            if t not in config:
                log(f"Новый параметр настроек: {t}={default_config[t]}")
                config[t] = default_config[t]
        if config["custom_skin"] and not os.path.isfile(config["custom_skin"]):
            log("Файл скина не найден", "ERROR")
            config["custom_skin"] = default_config["custom_skin"]
        config = dict(sorted(config.items()))
        save_config(config)
        log("Файл data.json найден, параметры загружены")
    else:
        config = default_config
        save_config(config)
        log("Файл data.json не найден, создан новый")

    if not config["mine_path"] or config["default_path"] or not os.path.isdir(config["mine_path"]):
        minecraft_path = os.path.join(os.getenv('APPDATA'), ".minecraft")
        config["mine_path"] = ""
        save_config(config)
        if not os.path.isdir(minecraft_path):
            os.makedirs(minecraft_path)
    else:
        minecraft_path = config["mine_path"]

    if config["java_paths"]:
        for key, value in list(config["java_paths"].items()):
            if not check_java(value):
                if config["java"] == key:
                    config["java"] = default_config["java"]
                config["java_paths"].pop(key)
                log(f"{key} не найдена или не работает", "ERROR")
    

    default_version = {
        "download": [],
        "not_comp": [],
        "version": "",
        "profile": False
    }

    version_file = os.path.join(minecraft_path, "version.json")
    if os.path.isfile(version_file):
        with open(version_file) as f:
            version = json.load(f)
        for t in default_version:
            if t not in version:
                log(f"Новый параметр настроек: {t}={default_config[t]}")
                version[t] = default_version[t]
        save_version(version)
        log("Файл version.json найден, параметры загружены")
    else:
        version = default_version
        save_version(version)
        log("Файл version.json не найден, создан новый")

    language_manager = Translator(config["language"])
    language = language_manager.language
    log(f"Язык лаунчера: {language}")
    
    ai_language = "ru" if language == "be" else language
    SYSTEM_PROMPT = (f"Ты — ассистент-эксперт по разбору лог-файлов Minecraft, который отвечает на этом языке: {ai_language}\n"
                     "Твоя задача —\n"
                     "1) Кратко (в одном предложении) описать причину краша\n"
                     "2) Предложить только те решения, которые напрямую связаны с обнаруженной причиной\n\n"
                     "Формат ответа:\n"
                     "Причина 1 предложением\n"
                     "Решения пронумерованы, каждое с новой строки>\n"
                     "Решения пишутся для рядового пользователя лаунчеров по майнкрафту\n"
                     "Не добавляй общих или универсальных советов, если они не имеют прямого отношения к выявленной причине.\n\n"
                     "Если входные данные не являются логами Minecraft, ответь ровно `None`(без дополнительного текста).\n"
                     "Если в логах нет информации, позволяющей однозначно определить причину, ответь ровно `None` (без дополнительного текста).")
    
    mods_path = os.path.join(minecraft_path, "mods")
    if version["profile"]:
        if not os.path.isdir(os.path.join(minecraft_path, "profiles", "profile_" + version["profile"])):
            log("Папка профиля не найдена", "ERROR")
            version["profile"] = False
            save_version(version)
        if os.path.isdir(mods_path):
            rmtree(mods_path)

    create_minecraft_environment()

    log(f"Приступаем к инициализации интерфейса...")
    execute_module("gui")
    root.mainloop()