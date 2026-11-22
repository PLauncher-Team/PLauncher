# This file is part of minecraft-launcher-lib (https://codeberg.org/JakobDev/minecraft-launcher-lib)
# SPDX-FileCopyrightText: Copyright (c) 2019-2024 JakobDev <jakobdev@gmx.de> and contributors
# SPDX-License-Identifier: BSD-2-Clause
"runtime provides information about Minecraft version requirements."
from ._helper import get_client_json
from .types import VersionRuntimeInformation
import os


def get_version_runtime_information(version: str, minecraft_directory: str | os.PathLike) -> VersionRuntimeInformation | None:
    """
    Returns information about the runtime used by a version

    Example:

    .. code:: python

        minecraft_version = "1.20"
        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        information = minecraft_launcher_lib.runtime.get_version_runtime_information(minecraft_version, minecraft_directory)
        print("Name: " + information["name"])
        print("Java version: " + str(information["javaMajorVersion"]))

    :param minecraft_directory: The path to your Minecraft directory
    :raises VersionNotFound: The Minecraft version was not found
    :return: A Dict with Information. None if the version has no runtime information.
    """
    data = get_client_json(version, minecraft_directory)

    if "javaVersion" not in data:
        return None

    return {
        "name": data["javaVersion"]["component"],
        "javaMajorVersion": data["javaVersion"]["majorVersion"]
    }
