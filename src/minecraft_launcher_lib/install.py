# This file is part of minecraft-launcher-lib (https://codeberg.org/JakobDev/minecraft-launcher-lib)
# SPDX-FileCopyrightText: Copyright (c) 2019-2024 JakobDev <jakobdev@gmx.de> and contributors
# SPDX-License-Identifier: BSD-2-Clause
"install allows you to install minecraft."
from ._helper import download_file, parse_rule_list, inherit_json, empty, get_user_agent, check_path_inside_minecraft_directory
from ._internal_types.shared_types import ClientJson, ClientJsonLibrary
from .natives import extract_natives_file, get_natives
from ._internal_types.install_types import AssetsJson
from concurrent.futures import ThreadPoolExecutor
from .runtime import install_jvm_runtime
from .exceptions import VersionNotFound
from .types import CallbackDict
import requests
import shutil
import json
import os

__all__ = ["install_minecraft_version"]
headers = {"user-agent": get_user_agent()}

def _calculate_total_tasks(versionid: str, path: str, url: str | None = None, sha1: str | None = None) -> int:
    """
    Предварительно подсчитывает общее количество файлов для загрузки,
    чтобы задать реальный setMax до начала установки.
    """
    total = 0
    v_file = os.path.join(path, "versions", versionid, f"{versionid}.json")

    if not os.path.isfile(v_file):
        if url:
            download_file(url, v_file, {}, sha1=sha1, minecraft_directory=path)
        else:
            v_list = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json", headers=headers).json()
            for i in v_list["versions"]:
                if i["id"] == versionid:
                    download_file(i["url"], v_file, {}, sha1=i["sha1"], minecraft_directory=path)
                    break
            else:
                raise VersionNotFound(versionid)

    with open(v_file, "r", encoding="utf-8") as f:
        vdata = json.load(f)

    if "inheritsFrom" in vdata:
        try:
            total += _calculate_total_tasks(vdata["inheritsFrom"], path)
        except VersionNotFound:
            pass
        vdata = inherit_json(vdata, path)

    # Библиотеки
    libs = vdata.get("libraries", [])
    total += len([lib for lib in libs if "rules" not in lib or parse_rule_list(lib["rules"], {})])

    # Ассеты (Ресурсы)
    if "assetIndex" in vdata:
        idx_path = os.path.join(path, "assets", "indexes", vdata["assets"] + ".json")
        if not os.path.isfile(idx_path):
            download_file(vdata["assetIndex"]["url"], idx_path, {}, sha1=vdata["assetIndex"]["sha1"], minecraft_directory=path)
        with open(idx_path, "r", encoding="utf-8") as f:
            adata = json.load(f)
        total += len(set(val["hash"] for val in adata["objects"].values()))

    # Файл клиента
    if "downloads" in vdata and "client" in vdata["downloads"]:
        total += 1

    # Логи
    if "logging" in vdata and len(vdata["logging"]) != 0:
        total += 1

    return total


def install_libraries(
        id: str,
        libraries: list[ClientJsonLibrary],
        path: str, callback: CallbackDict,
        max_workers: int | None = None,) -> None:
    """
    Install all libraries
    """
    session = requests.session()
    callback.get("setStatus", empty)("download_libraries")

    # Сообщаем обтекающему трекеру, сколько файлов в этой подзадаче
    callback.get("setMax", empty)(len(libraries))

    # Тихий коллбэк, чтобы download_file не сбрасывал прогресс байтами
    silent_cb = callback.get("_silent", callback)

    def download_library(
            i: ClientJsonLibrary,) -> None:
        """Download the single library."""
        if "rules" in i and not parse_rule_list(i["rules"], {}):
            return

        current_path = os.path.join(path, "libraries")
        if "url" in i:
            if i["url"].endswith("/"):
                download_url = i["url"][:-1]
            else:
                download_url = i["url"]
        else:
            download_url = "https://libraries.minecraft.net"

        try:
            lib_path, name, version = i["name"].split(":")[0:3]
        except ValueError:
            return

        for lib_part in lib_path.split("."):
            current_path = os.path.join(current_path, lib_part)
            download_url = f"{download_url}/{lib_part}"

        try:
            version, fileend = version.split("@")
        except ValueError:
            fileend = "jar"

        jar_filename = f"{name}-{version}.{fileend}"
        download_url = f"{download_url}/{name}/{version}"
        current_path = os.path.join(current_path, name, version)
        native = get_natives(i)

        if native != "":
            jar_filename_native = f"{name}-{version}-{native}.jar"
        jar_filename = f"{name}-{version}.{fileend}"
        download_url = f"{download_url}/{jar_filename}"

        try:
            download_file(download_url, os.path.join(current_path, jar_filename), callback=silent_cb, session=session, minecraft_directory=path)
        except Exception:
            pass

        if "downloads" not in i:
            if "extract" in i:
                extract_natives_file(os.path.join(current_path, jar_filename_native), os.path.join(path, "versions", id, "natives"), i["extract"])
            return

        if "artifact" in i["downloads"] and i["downloads"]["artifact"]["url"] != "" and "path" in i["downloads"]["artifact"]:
            download_file(i["downloads"]["artifact"]["url"], os.path.join(path, "libraries", i["downloads"]["artifact"]["path"]), silent_cb, sha1=i["downloads"]["artifact"]["sha1"], session=session, minecraft_directory=path)
        if native != "":
            download_file(i["downloads"]["classifiers"][native]["url"], os.path.join(current_path, jar_filename_native), silent_cb, sha1=i["downloads"]["classifiers"][native]["sha1"], session=session, minecraft_directory=path)  # type: ignore
            extract_natives_file(os.path.join(current_path, jar_filename_native), os.path.join(path, "versions", id, "natives"), i.get("extract", {"exclude": []}))

    count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_library, i) for i in libraries]
        for future in futures:
            future.result()
            count += 1
            callback.get("setProgress", empty)(count)


def install_assets(
        data: ClientJson,
        path: str,
        callback: CallbackDict,
        max_workers: int | None = None,) -> None:
    """
    Install all assets
    """
    if "assetIndex" not in data:
        return

    callback.get("setStatus", empty)("download_assets")
    session = requests.session()
    silent_cb = callback.get("_silent", callback)

    download_file(data["assetIndex"]["url"], os.path.join(path, "assets", "indexes", data["assets"] + ".json"), silent_cb, sha1=data["assetIndex"]["sha1"], session=session)
    with open(os.path.join(path, "assets", "indexes", data["assets"] + ".json")) as f:
        assets_data: AssetsJson = json.load(f)

    assets = set(val["hash"] for val in assets_data["objects"].values())
    callback.get("setMax", empty)(len(assets))
    count = 0

    def download_asset(filehash: str) -> None:
        """Download the single asset file."""
        download_file("https://resources.download.minecraft.net/" + filehash[:2] + "/" + filehash, os.path.join(path, "assets", "objects", filehash[:2], filehash), silent_cb, sha1=filehash, session=session, minecraft_directory=path)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_asset, filehash) for filehash in assets]
        for future in futures:
            future.result()
            count += 1
            callback.get("setProgress", empty)(count)


def do_version_install(versionid: str, path: str, callback: CallbackDict, url: str | None = None, sha1: str | None = None) -> None:
    """
    Installs the given version
    """
    silent_cb = callback.get("_silent", callback)

    if url:
        download_file(url, os.path.join(path, "versions", versionid, versionid + ".json"), silent_cb, sha1=sha1, minecraft_directory=path)

    with open(os.path.join(path, "versions", versionid, versionid + ".json"), "r", encoding="utf-8") as f:
        versiondata: ClientJson = json.load(f)

    if "inheritsFrom" in versiondata:
        try:
            install_minecraft_version(versiondata["inheritsFrom"], path, callback=callback)
        except VersionNotFound:
            pass
        versiondata = inherit_json(versiondata, path)

    install_libraries(versiondata["id"], versiondata["libraries"], path, callback)
    install_assets(versiondata, path, callback)

    if "logging" in versiondata:
        if len(versiondata["logging"]) != 0:
            logger_file = os.path.join(path, "assets", "log_configs", versiondata["logging"]["client"]["file"]["id"])
            callback.get("setMax", empty)(1)
            download_file(versiondata["logging"]["client"]["file"]["url"], logger_file, silent_cb, sha1=versiondata["logging"]["client"]["file"]["sha1"], minecraft_directory=path)
            callback.get("setProgress", empty)(1)

    if "downloads" in versiondata:
        callback.get("setMax", empty)(1)
        download_file(versiondata["downloads"]["client"]["url"], os.path.join(path, "versions", versiondata["id"], versiondata["id"] + ".jar"), silent_cb, sha1=versiondata["downloads"]["client"]["sha1"], minecraft_directory=path)
        callback.get("setProgress", empty)(1)

    if not os.path.isfile(os.path.join(path, "versions", versiondata["id"], versiondata["id"] + ".jar")) and "inheritsFrom" in versiondata:
        inherits_from = versiondata["inheritsFrom"]
        inherit_path = os.path.join(path, "versions", inherits_from, f"{inherits_from}.jar")
        check_path_inside_minecraft_directory(path, inherit_path)
        shutil.copyfile(os.path.join(path, "versions", versiondata["id"], versiondata["id"] + ".jar"), inherit_path)

    if "javaVersion" in versiondata:
        callback.get("setStatus", empty)("install_java_runtime")
        install_jvm_runtime(versiondata["javaVersion"]["component"], path, callback=callback)

    callback.get("setStatus", empty)("installation_complete")


def install_minecraft_version(versionid: str, minecraft_directory: str | os.PathLike, callback: CallbackDict | None = None) -> None:
    if isinstance(minecraft_directory, os.PathLike):
        minecraft_directory = str(minecraft_directory)
    if callback is None:
        callback = {}

    # Инициализация единого трекера прогресса на самом верхнем уровне
    if "_progress_state" not in callback:
        callback.get("setStatus", empty)("calculating_tasks")

        try:
            total_files = _calculate_total_tasks(versionid, minecraft_directory)
        except Exception:
            total_files = 0

        state = {
            "global_max": total_files,
            "global_progress": 0,
            "original_setMax": callback.get("setMax", empty),
            "original_setProgress": callback.get("setProgress", empty),
            "last_sub_progress": 0
        }

        if total_files > 0:
            state["original_setMax"](total_files)

        def unified_setMax(val):
            state["last_sub_progress"] = 0
            if state["global_max"] == 0 or val < 150:
                state["global_max"] += val
                state["original_setMax"](state["global_max"])

        def unified_setProgress(val):
            delta = val - state["last_sub_progress"]
            if delta < 0:
                delta = val
            state["last_sub_progress"] = val
            state["global_progress"] += delta
            state["original_setProgress"](state["global_progress"])

        callback["_progress_state"] = state
        callback["setMax"] = unified_setMax
        callback["setProgress"] = unified_setProgress

        callback["_silent"] = callback.copy()
        callback["_silent"]["setMax"] = empty
        callback["_silent"]["setProgress"] = empty

    if os.path.isfile(os.path.join(minecraft_directory, "versions", versionid, f"{versionid}.json")):
        do_version_install(versionid, minecraft_directory, callback)
        return

    version_list = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json", headers=headers).json()
    for i in version_list["versions"]:
        if i["id"] == versionid:
            do_version_install(versionid, minecraft_directory, callback, url=i["url"], sha1=i["sha1"])
            return

    raise VersionNotFound(versionid)