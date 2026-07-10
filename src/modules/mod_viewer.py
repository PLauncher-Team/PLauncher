from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


class ModManager:
    def __init__(self, mods_path="mods"):
        self.mods_path = mods_path
        self.files_name = {}
        self.results = {}
        self.hashes = []
        self.session = CachedSession(
            cache_name="modrinth-cache",
            backend="sqlite",
            expire_after=604800,
            allowable_methods=('GET', 'POST'),
            timeout=10
        )
        self.session.headers.update({
            "User-Agent": LauncherConfig.USER_AGENT
        })

    def _get_pil_image_from_url(self, url):
        if url is None:
            return None
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return PIL.Image.open(BytesIO(response.content))
        except:
            return None
    
    def check_version_compatibility(self):
        for hash, result in self.results.items():
            if not self.check_version("1.20.1", result["game_versions"]):
                print("ERROR", result["name"])
        
    def get_mods_info(self):
        self.hashes = self._get_mods_hashes()
        self.results = self.get_info_from_modrinth()
        projects_infos = {}
        for sha1 in self.results:
            mod_info = self.results[sha1]
            mod_info["version"] = mod_info["version_number"]
            projects_infos[mod_info["project_id"]] = mod_info

        for project in self._get_projects_info(list(projects_infos.keys())):
            mod_info = projects_infos[project["id"]]
            mod_info["description"] = project["description"]
            mod_info["name"] = project["title"]
            mod_info["icon"] = self.create_rounded_icon(self._get_pil_image_from_url(project.get("icon_url")))
            sha1_for_mod = next(sha1 for sha1, info in self.results.items() if info["project_id"] == project["id"])
            mod_info["jar_name"] = self.files_name[sha1_for_mod]
        
        unfound_mods = self.hashes - self.results.keys()
        for hash in unfound_mods:
            self.results[hash] = self.get_info_from_jar(hash)

        self.results = dict(sorted(self.results.items(), key=lambda item: (item[1].get("name") or "").casefold()))
        return self.results

    def _get_mods_hashes(self):
        def _get_sha1(mod_path):
            sha1 = hashlib.sha1(open(os.path.join(self.mods_path, mod_path), "rb").read()).hexdigest()
            self.files_name[sha1] = mod_path
            return sha1

        mods = [
            i for i in os.listdir(self.mods_path)
            if os.path.isfile(os.path.join(self.mods_path, i)) and (i.endswith(".jar") or i.endswith(".jar.disabled"))
        ]
    
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return set(executor.map(_get_sha1, mods))

    def _get_projects_info(self, ids):
        request = self.session.get("https://api.modrinth.com/v2/projects", params={"ids": json.dumps(ids)})
        return request.json()

    def get_info_from_modrinth(self):
        request = self.session.post("https://api.modrinth.com/v2/version_files", json={"algorithm": "sha1", "hashes": list(self.hashes)})
        return request.json()

    def get_info_from_jar(self, mod_sha1):
        mod_path = os.path.join(self.mods_path, self.files_name[mod_sha1])
        try:
            with zipfile.ZipFile(mod_path) as zf:
                namelist = zf.namelist()
                mod_name = os.path.basename(mod_path)
                self.results[mod_sha1] = {
                    "name": mod_name,
                    "description": None,
                    "version": None,
                    "loaders": [],
                    "game_versions": [],
                    "jar_name": mod_name,
                    "icon": None,
                    "dependencies": []
                }
                info = self.results[mod_sha1]
                def load_root_png_if_needed():
                    if info["icon"]:
                        return
                    root_pngs = [name for name in namelist if "/" not in name and "\\" not in name and name.lower().endswith(".png")]
                    if root_pngs:
                        try:
                            with zf.open(root_pngs[0]) as imgf:
                                info["icon"] = PIL.Image.open(BytesIO(imgf.read()))
                        except:
                            pass

                def add_game_versions(versions):
                    if isinstance(versions, str):
                        if versions:
                            info["game_versions"].append(versions)
                    elif isinstance(versions, list):
                        for v in versions:
                            if isinstance(v, str) and v:
                                info["game_versions"].append(v)

                if "fabric.mod.json" in namelist:
                    info["loaders"].append("Fabric")
                    with zf.open("fabric.mod.json") as f:
                        data = json.load(f)
                        info["name"] = data.get("name") or info["name"]
                        info["description"] = data.get("description") or info["description"]
                        info["version"] = data.get("version") or info["version"]
                        depends = data.get("depends", {})
                        if isinstance(depends, dict):
                            mc = depends.get("minecraft")
                            add_game_versions(mc)
                            for dep_id in depends.keys():
                                if dep_id != "minecraft" and dep_id not in info["dependencies"]:
                                    info["dependencies"].append(dep_id)
                        icon_path = data.get("icon")
                        if icon_path and icon_path in namelist:
                            try:
                                with zf.open(icon_path) as imgf:
                                    info["icon"] = PIL.Image.open(BytesIO(imgf.read()))
                            except:
                                pass
                    load_root_png_if_needed()

                if "quilt.mod.json" in namelist:
                    info["loaders"].append("Quilt")
                    with zf.open("quilt.mod.json") as f:
                        data = json.load(f)
                        loader_data = data.get("quilt_loader", {})
                        metadata = loader_data.get("metadata", {})
                        info["name"] = metadata.get("name") or loader_data.get("id") or info["name"]
                        info["description"] = metadata.get("description") or info["description"]
                        info["version"] = loader_data.get("version") or info["version"]

                        quilt_deps = loader_data.get("depends", {})
                        if isinstance(quilt_deps, dict):
                            mc = quilt_deps.get("minecraft")
                            add_game_versions(mc)
                            for dep_id in quilt_deps.keys():
                                if dep_id != "minecraft" and dep_id not in info["dependencies"]:
                                    info["dependencies"].append(dep_id)
                        elif isinstance(quilt_deps, list):
                            for dep in quilt_deps:
                                if isinstance(dep, dict):
                                    d_id = dep.get("id")
                                    if d_id == "minecraft":
                                        add_game_versions(dep.get("version"))
                                    elif d_id and d_id not in info["dependencies"]:
                                        info["dependencies"].append(d_id)
                                elif isinstance(dep, str):
                                    if dep != "minecraft" and dep not in info["dependencies"]:
                                        info["dependencies"].append(dep)

                        icon_path = metadata.get("icon")
                        if icon_path and icon_path in namelist:
                            try:
                                with zf.open(icon_path) as imgf:
                                    info["icon"] = PIL.Image.open(BytesIO(imgf.read()))
                            except:
                                pass
                    load_root_png_if_needed()

                if "META-INF/neoforge.mods.toml" in namelist:
                    info["loaders"].append("NeoForge")
                    with zf.open("META-INF/neoforge.mods.toml") as f:
                        toml_data = tomllib.load(f)
                        for mod_data in toml_data.get("mods", []):
                            info["name"] = mod_data.get("displayName") or mod_data.get("modId") or info["name"]
                            info["description"] = mod_data.get("description") or info["description"]
                            info["version"] = mod_data.get("version") or info["version"]
                            logo = mod_data.get("logoFile")
                            if logo and logo in namelist:
                                try:
                                    with zf.open(logo) as imgf:
                                        info["icon"] = PIL.Image.open(BytesIO(imgf.read()))
                                except:
                                    pass
                            break
                        dependencies = toml_data.get("dependencies", {})
                        for dep_list in dependencies.values():
                            for dep in dep_list:
                                d_id = dep.get("modId")
                                if d_id == "minecraft":
                                    version_range = str(dep.get("versionRange", "")).strip()
                                    if version_range:
                                        add_game_versions(version_range)
                                elif d_id and d_id not in info["dependencies"]:
                                    info["dependencies"].append(d_id)
                    load_root_png_if_needed()

                if "META-INF/mods.toml" in namelist:
                    info["loaders"].append("Forge")
                    with zf.open("META-INF/mods.toml") as f:
                        toml_data = tomllib.load(f)
                        for mod_data in toml_data.get("mods", []):
                            info["name"] = mod_data.get("displayName") or mod_data.get("modId") or info["name"]
                            info["description"] = mod_data.get("description") or info["description"]
                            info["version"] = mod_data.get("version") or info["version"]
                            logo = mod_data.get("logoFile")
                            if logo and logo in namelist:
                                try:
                                    with zf.open(logo) as imgf:
                                        info["icon"] = PIL.Image.open(BytesIO(imgf.read()))
                                except:
                                    pass
                            break
                        dependencies = toml_data.get("dependencies", {})
                        for dep_list in dependencies.values():
                            for dep in dep_list:
                                d_id = dep.get("modId")

                                is_mandatory = dep.get("mandatory", True)
                                if not is_mandatory:
                                    continue

                                if d_id == "minecraft":
                                    version_range = dep.get("versionRange", "")
                                    if version_range:
                                        add_game_versions(version_range)
                                elif d_id and d_id not in info["dependencies"]:
                                    info["dependencies"].append(d_id)
                    load_root_png_if_needed()

                if "mcmod.info" in namelist:
                    if "Forge" not in info["loaders"]:
                        info["loaders"].append("Forge (Legacy)")
                    with zf.open("mcmod.info") as f:
                        data = json.load(f)
                        if isinstance(data, list) and data:
                            main_mod = data[0]
                        else:
                            main_mod = data if isinstance(data, dict) else {}
                        info["name"] = main_mod.get("name") or info["name"]
                        info["description"] = main_mod.get("description") or info["description"]
                        info["version"] = main_mod.get("version") or info["version"]
                        mc_ver = main_mod.get("mcversion") or main_mod.get("mcVersion")
                        add_game_versions(mc_ver)
                        deps = main_mod.get("dependencies", [])
                        if isinstance(deps, list):
                            for d in deps:
                                if d and d != "minecraft" and d not in info["dependencies"]:
                                    info["dependencies"].append(str(d))
                        logo = main_mod.get("logoFile")
                        if logo and logo in namelist:
                            try:
                                with zf.open(logo) as imgf:
                                    info["icon"] = PIL.Image.open(BytesIO(imgf.read()))
                            except:
                                pass
                    load_root_png_if_needed()

                if not info["loaders"]:
                    root_infos = [
                        name for name in namelist
                        if "/" not in name and "\\" not in name and ("info" in name.lower() or name.lower().endswith(".info"))
                    ]
                    for info_file in root_infos:
                        try:
                            with zf.open(info_file) as f:
                                raw_content = f.read().decode('utf-8')
                                repaired_content = repair_json(raw_content)
                                data = json.loads(repaired_content)
                                if isinstance(data, list) and data:
                                    data = data[0]
                                if isinstance(data, dict):
                                    info["loaders"].append("Forge (Legacy)")
                                    info["name"] = data.get("name") or data.get("displayName") or data.get("modid") or data.get("id") or info["name"]
                                    info["description"] = data.get("description") or info["description"]
                                    info["version"] = data.get("version") or info["version"]
                                    mc_ver = data.get("mcversion") or data.get("mcVersion")
                                    add_game_versions(mc_ver)
                                    deps = data.get("dependencies") or data.get("depends")
                                    if isinstance(deps, list):
                                        for d in deps:
                                            if d and d != "minecraft" and d not in info["dependencies"]:
                                                info["dependencies"].append(str(d))
                                    elif isinstance(deps, dict):
                                        for k in deps.keys():
                                            if k != "minecraft" and k not in info["dependencies"]:
                                                info["dependencies"].append(str(k))
                                    logo = data.get("logoFile") or data.get("icon")
                                    if logo and logo in namelist:
                                        try:
                                            with zf.open(logo) as imgf:
                                                info["icon"] = PIL.Image.open(BytesIO(imgf.read()))
                                        except:
                                            pass
                                    break
                        except:
                            continue

                ver = info.get("version", "")
                if not ver or ver.startswith("${"):
                    info["version"] = None

                if "META-INF/MANIFEST.MF" in namelist:
                    try:
                        with zf.open("META-INF/MANIFEST.MF") as f:
                            manifest = f.read().decode("utf-8", errors="ignore")
                            for line in manifest.splitlines():
                                if line.startswith("Implementation-Version"):
                                    parts = line.split(": ")[1].split("-")
                                    if len(parts) >= 2:
                                        if not info["game_versions"]:
                                            add_game_versions(parts[0])
                                        if not info["version"]:
                                            info["version"] = "-".join(parts[1:])
                                    elif len(parts) == 1:
                                        if not info["version"]:
                                            info["version"] = parts[0]
                                elif line.startswith("Fabric-Minecraft-Version"):
                                    if not info["game_versions"]:
                                        add_game_versions(line.split(": ")[1])
                                elif line.startswith("Built-On-Minecraft") or line.startswith("Build-On-Minecraft"):
                                    if not info["game_versions"]:
                                        add_game_versions(line.split(": ")[1])
                                elif line.startswith("Specification-Version"):
                                    spec_version = line.split(": ")[1]
                                    if spec_version == "1":
                                        continue
                                    if not info["version"]:
                                        info["version"] = spec_version
                    except:
                        pass

                if not info["icon"]:
                    load_root_png_if_needed()
                if info["icon"]:
                    info["icon"] = self.create_rounded_icon(info["icon"])

                if info["game_versions"]:
                    info["game_versions"] = list(dict.fromkeys(info["game_versions"]))
                
                return info
        except Exception:
            excepthook(*sys.exc_info())
            mod_name = os.path.basename(mod_path)
            return {
                "name": mod_name,
                "description": None,
                "version": None,
                "loaders": [],
                "game_versions": [],
                "jar_name": mod_name,
                "icon": None,
                "dependencies": []
            }

    @staticmethod
    def create_rounded_icon(pil_image, size=78):
        if pil_image is None:
            return None
        original_width, original_height = pil_image.size
        ratio = original_width / original_height
        if ratio > 1:
            new_width = size
            new_height = int(size / ratio)
        else:
            new_height = size
            new_width = int(size * ratio)
        resized = pil_image.resize((new_width, new_height), PIL.Image.Resampling.LANCZOS)
        square = PIL.Image.new("RGBA", (size, size), (0, 0, 0, 0))
        paste_x = (size - new_width) // 2
        paste_y = (size - new_height) // 2
        square.paste(resized, (paste_x, paste_y), resized if resized.mode == "RGBA" else None)
        mask = PIL.Image.new("L", (size, size))
        draw = PIL.ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, size, size), radius=18, fill=255)
        square.putalpha(mask)
        return square
    
    @staticmethod
    def check_version(version, constraints) -> bool:
        try:
            ver = packaging.version.Version(version)
        except packaging.version.InvalidVersion:
            return False
    
        if isinstance(constraints, str):
            constraints = [constraints]
    
        for constraint in constraints:
            constraint = constraint.strip().replace(" ", "")
    
            match = re.match(r'^([><=!]=?)(.+)$', constraint)
            if match:
                op, ver_str = match.groups()
                try:
                    target = packaging.version.Version(ver_str)
                except packaging.version.InvalidVersion:
                    continue
    
                if op == ">=" and ver >= target:
                    return True
                elif op == "<=" and ver <= target:
                    return True
                elif op == ">" and ver > target:
                    return True
                elif op == "<" and ver < target:
                    return True
                elif op == "==" and ver == target:
                    return True
                elif op == "!=" and ver != target:
                    return True
                continue
    
            reverse_match = re.match(r'^(.+?)([><=!]=)$', constraint)
            if reverse_match:
                ver_str, op = reverse_match.groups()
                try:
                    target = packaging.version.Version(ver_str)
                except packaging.version.InvalidVersion:
                    continue
    
                if op == ">=" and target >= ver:
                    return True
                elif op == "<=" and target <= ver:
                    return True
                elif op == ">" and target > ver:
                    return True
                elif op == "<" and target < ver:
                    return True
                continue
    
            bracket_match = re.match(r'^([\[(])([^,\]]*)(?:,([^])]*))?([])])$', constraint)
            if bracket_match:
                left_bracket, left_str, right_str, right_bracket = bracket_match.groups()
                try:
                    left_ok = right_ok = True
    
                    if left_str:
                        left_ver = packaging.version.Version(left_str)
                        if left_bracket == "[":
                            left_ok = ver >= left_ver
                        else:
                            left_ok = ver > left_ver
                    if right_str:
                        right_ver = packaging.version.Version(right_str)
                        if right_bracket == "]":
                            right_ok = ver <= right_ver
                        else:
                            right_ok = ver < right_ver
                    elif right_str is None and left_str:
                        if left_bracket == "[" and right_bracket == "]":
                            if ver == left_ver:
                                return True
                            else:
                                continue
                        elif left_bracket == "(" and right_bracket == ")":
                            if ver != left_ver:
                                return True
                            else:
                                continue
                        else:
                            if left_ok:
                                return True
                            else:
                                continue
                    elif not left_str and right_str:
                        if right_ok:
                            return True
                        else:
                            continue
    
                    if left_ok and right_ok:
                        return True
                except packaging.version.InvalidVersion:
                    continue
    
            else:
                try:
                    if ver == packaging.version.Version(constraint):
                        return True
                except packaging.version.InvalidVersion:
                    continue
    
        return False