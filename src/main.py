# Import standard library modules
from time import perf_counter, time
start_time = perf_counter()  # Start performance counter for measuring initialization time

import json
import os
import re
import ctypes
import traceback
import hashlib
import sys
import shutil
import random
import webbrowser
import subprocess
import threading
from io import BytesIO
from locale import getdefaultlocale
from socket import create_connection
from datetime import datetime
from uuid import uuid4
from tkinter import filedialog

# Import third-party modules
import minecraft_launcher_lib as mcl
import customtkinter as ctk
import requests
import packaging
import hPyT
import bs4
import win32job
import win32con
import win32api
import optipy
import PIL
from CTkMessagebox import CTkMessagebox
from CTkScrollableDropdownPP import CTkScrollableDropdown
from psutil import virtual_memory
from pywinstyles import set_opacity
from ratelimit import rate_limited


def log(message: str, level: str = 'INFO', source: str = 'main') -> None:
    """Log messages with timestamp, level, source, and thread information.
    
    Args:
        message: The message to log
        level: Log level (INFO, ERROR, etc.)
        source: Source module of the log message
    """
    caller_name = sys._getframe(1).f_code.co_name  # Get calling function name
    thread_name = threading.current_thread().name  # Get current thread name

    # Format timestamp with milliseconds
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    output = f"[{timestamp} - {level} - {source}.{caller_name} - {thread_name}] - {message}"

    # Thread-safe logging
    with log_lock:
        print(output)
        with open("launcher.log", "a", encoding="utf-8") as f:
            f.write(output + "\n")


# Dictionary to store expected file hashes for verification
EXPECTED_HASHES = {}

def compute_sha256(path: str) -> str:
    """Compute SHA256 hash of a file.
    
    Args:
        path: Path to the file to hash
        
    Returns:
        Hexadecimal string representation of the SHA256 hash
    """
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def execute_module(module_name: str) -> None:
    """Execute a Python module with hash verification.
    
    Args:
        module_name: Name of the module to execute (without .py extension)
    """
    module_path = os.path.join("modules", f"{module_name}.py")

    # Verify file hash if expected hashes are available
    if EXPECTED_HASHES:
        expected = EXPECTED_HASHES.get(module_name)
        actual = compute_sha256(module_path)
        if actual != expected:
            log(f"Hash mismatch for module '{module_name}'.", level="ERROR")
            sys.exit(1)

    try:
        with open(module_path, encoding="utf-8") as file:
            code = file.read()
        exec(code, globals())  # Execute the module code in global namespace
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
    # Create mutex to ensure single instance of launcher
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, "PLauncher")
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        os._exit(0)

    log_lock = threading.Lock()  # Lock for thread-safe logging

    # Clear previous log file if exists
    if os.path.isfile("launcher.log"):
        os.remove("launcher.log")

    minecraft_log_file = None  # Will store path to Minecraft log file

    # Set custom exception handler
    sys.excepthook = excepthook
    log("Welcome to debug...")

    # Try to set DPI awareness for proper scaling on high-DPI displays
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    # Load all required modules
    for module in ["utils", "launcher_core", "loaders", "profiles", "window_utils", "skin", "translator", "java", "crash", "feedback", "settings_gui"]:
        execute_module(module)

    log("Module import completed")

    # Path constants
    launcher_path = os.path.join(os.getenv('APPDATA'), "pylauncher")

    # Configuration constants
    IS_INTERNET = check_internet_connection()
    CURRENT_VERSION = "v1.0.0"
    FPS = get_refresh_rate()
    MAX_MEMORY_GB = get_available_memory()
    FORM_VIEW_URL = "https://docs.google.com/forms/d/e/1FAIpQLScHheNuuIixaus6D_2iNRMNIMrbJWmiq-Rc7XKNf5lBo0f3NA/viewform"
    FORM_SUBMIT_URL = "https://docs.google.com/forms/d/e/1FAIpQLScHheNuuIixaus6D_2iNRMNIMrbJWmiq-Rc7XKNf5lBo0f3NA/formResponse"

    # Form field configuration
    TARGET_FIELD_CONFIG = {
        "Email": {"label_in_form_data": "Email", "payload_key": "email_payload"},
        "Subject": {"label_in_form_data": "Тема ", "payload_key": "subject_payload"},
        "Description": {"label_in_form_data": "Описание проблемы / предложения", "payload_key": "description_payload"}
    }

    # Regular expression for email validation
    EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

    # Runtime state variables
    is_running = False
    minecraft_process = None
    loader_process = None
    step = None
    progress = None
    total_files = 0
    select_page = None
    versions = []
    old_types_versions = []

    # Log initial configuration
    log(f"Version: {CURRENT_VERSION}")
    log(f"Monitor refresh rate: {FPS} Hz")
    log(f"Internet status: {IS_INTERNET}")
    log(f"RAM size: {MAX_MEMORY_GB} GB")

    # Default configuration values
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
        "memory_args": str(min(max(MAX_MEMORY_GB * 1024 // 2, 512), 4096)),
        "custom_args": "",
        "ely_by": False,
        "custom_skin": "",
        "default_skin": True,
        "language": "",
        "default_path": True,
        "java_paths": {},
        "java": None
    }

    # Load or create configuration file
    if os.path.isfile("data.json"):
        with open("data.json") as f:
            config = json.load(f)
        # Add any missing default values
        for t in default_config:
            if t not in config:
                log(f"New settings parameter: {t}={default_config[t]}")
                config[t] = default_config[t]
        # Validate skin file path
        if config["custom_skin"] and not os.path.isfile(config["custom_skin"]):
            log("Skin file not found", "ERROR")
            config["custom_skin"] = default_config["custom_skin"]
        config = dict(sorted(config.items()))
        save_config(config)
        log("data.json file found, settings loaded")
    else:
        config = default_config
        save_config(config)
        log("data.json file not found, a new one has been created")

    # Set up Minecraft directory path
    if not config["mine_path"] or config["default_path"] or not os.path.isdir(config["mine_path"]):
        minecraft_path = os.path.join(os.getenv('APPDATA'), ".minecraft")
        config["mine_path"] = ""
        save_config(config)
        if not os.path.isdir(minecraft_path):
            os.makedirs(minecraft_path)
    else:
        minecraft_path = config["mine_path"]

    # Validate Java paths in configuration
    if config["java_paths"]:
        for key, value in list(config["java_paths"].items()):
            if not check_java(value):
                if config["java"] == key:
                    config["java"] = default_config["java"]
                config["java_paths"].pop(key)
                log(f"{key} not found or not working", "ERROR")

    # Default version configuration
    default_version = {
        "download": [],
        "not_comp": [],
        "version": "",
        "profile": False
    }

    # Load or create version file
    version_file = os.path.join(minecraft_path, "version.json")
    if os.path.isfile(version_file):
        with open(version_file) as f:
            version = json.load(f)
        # Add any missing default values
        for t in default_version:
            if t not in version:
                log(f"New settings parameter: {t}={default_config[t]}")
                version[t] = default_version[t]
        save_version(version)
        log("version.json file found, settings loaded")
    else:
        version = default_version
        save_version(version)
        log("version.json file not found, a new one has been created")

    # Initialize language manager
    language_manager = Translator(config["language"])
    language = language_manager.language
    log(f"Launcher language: {language}")

    # Set up language for AI responses
    ai_language = "ru" if language == "be" else language
    SYSTEM_PROMPT = (f"You are an expert assistant in analyzing Minecraft log files who responds in this language: {ai_language}\n"
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

    # Check the existence of profile
    if version["profile"]:
        if not os.path.isdir(os.path.join(minecraft_path, "profiles", "profile_" + version["profile"])):
            log("Profile folder not found", "ERROR")
            version["profile"] = False
            save_version(version)

    # Create required Minecraft directories
    create_minecraft_environment()
    
    # Migrate old profile system to new one if needed
    for profile in [os.path.join(minecraft_path, "profiles", name) for name in os.listdir(os.path.join(minecraft_path, "profiles")) if os.path.isdir(os.path.join(os.path.join(minecraft_path, "profiles"), name))]:
        items = os.listdir(profile)

        # Check if profile uses old system (mods directly in profile folder)
        for item in items:
            full_path = os.path.join(profile, item)
            if not os.path.isfile(full_path) or not item.lower().endswith('.jar'):
                break
        else:
            if items:
                log(f"Profile \"{profile}\" is using the old system. Switching to the new one...")
                mods_folder = os.path.join(profile, "mods")
                if not os.path.exists(mods_folder):
                    os.mkdir(mods_folder)

                # Move mod files to mods subdirectory
                for item in items:
                    src = os.path.join(profile, item)
                    dst = os.path.join(mods_folder, item)
                    shutil.move(src, dst)

    # Create required Minecraft directories
    create_minecraft_environment()

    # Initialize GUI
    log(f"Starting interface initialization...")
    execute_module("gui")
    root.mainloop()  # Start main application loop