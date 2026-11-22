# This file is part of minecraft-launcher-lib (https://codeberg.org/JakobDev/minecraft-launcher-lib)
# SPDX-FileCopyrightText: Copyright (c) 2019-2024 JakobDev <jakobdev@gmx.de> and contributors
# SPDX-License-Identifier: BSD-2-Clause
"""
This module contains all Types for minecraft-launcher-lib. It may help your IDE. You don't need to use this module directly in your code.
If you are not interested in static typing just ignore it.
For more information about TypedDict see `PEP 589 <https://peps.python.org/pep-0589/>`_.
"""
from typing import TypedDict, Callable
import datetime


class MinecraftOptions(TypedDict, total=False):
    username: str
    uuid: str
    token: str
    executablePath: str
    defaultExecutablePath: str
    jvmArguments: list[str]
    launcherName: str
    launcherVersion: str
    gameDirectory: str
    demo: bool
    customResolution: bool
    resolutionWidth: str
    resolutionHeight: str
    server: str
    port: str
    nativesDirectory: str
    enableLoggingConfig: bool
    disableMultiplayer: bool
    disableChat: bool
    quickPlayPath: str | None
    quickPlaySingleplayer: str | None
    quickPlayMultiplayer: str | None
    quickPlayRealms: str | None


class CallbackDict(TypedDict, total=False):
    setStatus: Callable[[str], None]
    setProgress: Callable[[int], None]
    setMax: Callable[[int], None]


class LatestMinecraftVersions(TypedDict):
    release: str
    snapshot: str


class MinecraftVersionInfo(TypedDict):
    id: str
    type: str
    releaseTime: datetime.datetime
    complianceLevel: int


# fabric

class FabricMinecraftVersion(TypedDict):
    version: str
    stable: bool


class FabricLoader(TypedDict):
    separator: str
    build: int
    maven: str
    version: str
    stable: bool


# quilt

class QuiltMinecraftVersion(TypedDict):
    version: str
    stable: bool


class QuiltLoader(TypedDict):
    separator: str
    build: int
    maven: str
    version: str



# runtime

class VersionRuntimeInformation(TypedDict):
    name: str
    javaMajorVersion: int
