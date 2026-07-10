from ._helper import get_requests_response_cache
from .utils import get_github_tags
import subprocess
import os

def get_all_minecraft_versions():
    return get_github_tags("CleanroomMC", "Cleanroom")[:-3]

def download_and_run(version: str, path: str = "cleanroom-installer.jar", path_minecraft: str = "", java: str = ""):
    response = get_requests_response_cache(f"https://github.com/CleanroomMC/Cleanroom/releases/download/{version}/cleanroom-{version}-installer.jar")
    with open(path, "wb") as file:
        file.write(response.content)
    
    subprocess.run([java, "-jar", path, f"--installClient={path_minecraft}"], creationflags=134217728)

    os.remove(path)
