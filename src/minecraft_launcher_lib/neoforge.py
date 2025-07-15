import re
import os
import subprocess
from typing import Dict
from ._helper import get_requests_response_cache

base_url = "http://maven.neoforged.net/releases/net/neoforged/neoforge/"

def get_versions() -> Dict[str, str]:
    """
    Get available NeoForge versions and return them as a dictionary.
    
    :return: Dictionary in the format {MC version: Full version}.
    """
    response = get_requests_response_cache(f"{base_url}maven-metadata.xml", timeout=5)

    versions = re.findall(r"<version>(.*?)</version>", response.text)

    latest_versions = {}
    for version in versions:
        parts = version.split(".")
        if len(parts) < 3:
            continue

        mc_version = parts[0:2]
        loader_version = parts[2]
        mc_version_key = f"{mc_version[0]}.{mc_version[1]}"

        if not re.match(r'^[0-9.]+$', mc_version_key):
            continue  # skip if mc_version_key is not just numbers and dots

        loader_version_num = (
            int(loader_version.split("-")[0])
            if "-beta" in loader_version
            else int(loader_version))

        if mc_version_key not in latest_versions or latest_versions[mc_version_key][1] < loader_version_num:
            latest_versions[mc_version_key] = (version, loader_version_num)

    return {
        f"1.{mc_version}": full_version
        for mc_version, (full_version, _) in latest_versions.items()
    }

def download_and_run(version: str, path: str = "neoforge-installer.jar", path_minecraft: str = "", java: str = ""):
    """
    Download the JAR file of the specified version and run it.
    
    :param version: Full version to download.
    :param path: Output file path.
    :param path_minecraft: Minecraft path
    :param java: Java path
    """
    response = get_requests_response_cache(f"{base_url}{version}/neoforge-{version}-installer.jar")

    with open(path, "wb") as file:
        file.write(response.content)

    subprocess.run([java, "-jar", path, f"--installClient={path_minecraft}"], creationflags=134217728)
    
    os.remove(path)
