# This file is part of minecraft-launcher-lib (https://codeberg.org/JakobDev/minecraft-launcher-lib)
# SPDX-FileCopyrightText: Copyright (c) 2019-2024 JakobDev <jakobdev@gmx.de> and contributors
# SPDX-License-Identifier: BSD-2-Clause
"utils contains a few functions for helping you that doesn't fit in any other category"
from .types import MinecraftVersionInfo
from ._internal_types.shared_types import ClientJson, VersionListManifestJson
from ._helper import get_requests_response_cache
from datetime import datetime
import platform
import pathlib
import json
import os


def get_minecraft_directory() -> str:
    """
    Returns the default path to the .minecraft directory

    Example:

    .. code:: python

        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        print(f"The default minecraft directory is {minecraft_directory}")
    """
    if platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA", os.path.join(pathlib.Path.home(), "AppData", "Roaming")), ".minecraft")
    elif platform.system() == "Darwin":
        return os.path.join(str(pathlib.Path.home()), "Library", "Application Support", "minecraft")
    else:
        return os.path.join(str(pathlib.Path.home()), ".minecraft")


def get_version_list() -> list[MinecraftVersionInfo]:
    """
    Returns all versions that Mojang offers to download

    Example:

    .. code:: python

        for version in minecraft_launcher_lib.utils.get_version_list():
            print(version["id"])
    """
    vlist: VersionListManifestJson = get_requests_response_cache("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json").json()
    returnlist: list[MinecraftVersionInfo] = []
    for i in vlist["versions"]:
        returnlist.append({"id": i["id"], "type": i["type"], "releaseTime": datetime.fromisoformat(i["releaseTime"]), "complianceLevel": i["complianceLevel"]})
    return returnlist


def get_installed_versions(minecraft_directory: str | os.PathLike) -> list[MinecraftVersionInfo]:
    """
    Returns all installed versions

    Example:

    .. code:: python

        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        for version in minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory):
            print(version["id"])

    :param minecraft_directory: The path to your Minecraft directory
    """
    try:
        dir_list = os.listdir(os.path.join(minecraft_directory, "versions"))
    except FileNotFoundError:
        return []

    version_list: list[MinecraftVersionInfo] = []
    for i in dir_list:
        if not os.path.isfile(os.path.join(minecraft_directory, "versions", i, i + ".json")):
            continue

        with open(os.path.join(minecraft_directory, "versions", i, i + ".json"), "r", encoding="utf-8") as f:
            version_data: ClientJson = json.load(f)

        try:
            release_time = datetime.fromisoformat(version_data["releaseTime"])
        except ValueError:
            # In case some custom client has a invalid time
            release_time = datetime.fromtimestamp(0)

        version_list.append({"id": version_data["id"], "type": version_data["type"], "releaseTime": release_time, "complianceLevel": version_data.get("complianceLevel", 0)})
    return version_list


_version_cache = None


def get_library_version() -> str:
    return "7.1"


def is_version_valid(version: str, minecraft_directory: str | os.PathLike) -> bool:
    """
    Checks if the given version exists.
    This checks if the given version is installed or offered to download by Mojang.
    Basically you can use this tho check, if the given version can be used with :func:`~minecraft_launcher_lib.install.install_minecraft_version`.

    Example:

    .. code:: python

        version = "1.0"
        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        if minecraft_launcher_lib.utils.is_version_valid(version, minecraft_directory):
            print(f"{version} is a valid version")
        else:
            print(f"{version} is not a valid version")

    :param version: A Minecraft version
    :param minecraft_directory: The path to your Minecraft directory
    """
    if os.path.isdir(os.path.join(minecraft_directory, "versions", version)):
        return True
    for i in get_version_list():
        if i["id"] == version:
            return True
    return False


def get_github_tags(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/tags"

    response = get_requests_response_cache(url)
    response.raise_for_status()

    tags_data = response.json()

    all_tags = [tag["name"] for tag in tags_data]

    return all_tags