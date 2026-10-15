"""Collect the loose files the Divinity agent model changer needs into ./csgo.

Reads each agent .mdl for its material names and search paths, follows the
.vmt files to every texture and include they reference, and copies only files
that exist loose in the game folder and are not already inside pak01 (every
2018 install already has those). Extract ./csgo over a game's csgo folder.

Usage: python pack_agents.py [path\\to\\csgo] [--zip]
"""

import shutil
import struct
import sys
from pathlib import Path

AGENTS = [
    "ctm_diver_varianta", "ctm_diver_variantb", "ctm_diver_variantc",
    "ctm_fbi_variantb", "ctm_fbi_variantf", "ctm_fbi_variantg", "ctm_fbi_varianth",
    "ctm_gendarmerie_varianta", "ctm_gendarmerie_variantb", "ctm_gendarmerie_variantc",
    "ctm_gendarmerie_variantd", "ctm_gendarmerie_variante",
    "ctm_sas_variantf", "ctm_sas_variantg",
    "ctm_st6_variante", "ctm_st6_variantg", "ctm_st6_varianti", "ctm_st6_variantj",
    "ctm_st6_variantk", "ctm_st6_variantl", "ctm_st6_variantm", "ctm_st6_variantn",
    "ctm_swat_variante", "ctm_swat_variantf", "ctm_swat_variantg", "ctm_swat_varianth",
    "ctm_swat_varianti", "ctm_swat_variantj", "ctm_swat_variantk",
    "tm_balkan_variantf", "tm_balkan_variantg", "tm_balkan_varianth", "tm_balkan_varianti",
    "tm_balkan_variantj", "tm_balkan_variantk", "tm_balkan_variantl",
    "tm_jungle_raider_varianta", "tm_jungle_raider_variantb", "tm_jungle_raider_variantb2",
    "tm_jungle_raider_variantc", "tm_jungle_raider_variantd", "tm_jungle_raider_variante",
    "tm_jungle_raider_variantf", "tm_jungle_raider_variantf2",
    "tm_leet_variantf", "tm_leet_variantg", "tm_leet_varianth", "tm_leet_varianti",
    "tm_leet_variantj",
    "tm_phoenix_variantf", "tm_phoenix_variantg", "tm_phoenix_varianth", "tm_phoenix_varianti",
    "tm_professional_varf", "tm_professional_varf1", "tm_professional_varf2",
    "tm_professional_varf3", "tm_professional_varf4", "tm_professional_varf5",
    "tm_professional_varg", "tm_professional_varh", "tm_professional_vari",
    "tm_professional_varj",
]

MODEL_DIR = "models/player/custom_player/legacy"
DEFAULT_GAME = Path(r"C:\Users\greyz\Documents\!2018 stuff\2018\csgo 2018\csgo 2018 (supremacy)\csgo")


def read_vpk_paths(vpk: Path) -> set[str]:
    data = vpk.read_bytes()
    _, version, tree_size = struct.unpack_from("<III", data, 0)
    offset = 12 if version == 1 else 28
    end = offset + tree_size
    paths: set[str] = set()

    def read_string() -> str:
        nonlocal offset
        stop = data.index(b"\0", offset)
        text = data[offset:stop].decode("latin1")
        offset = stop + 1
        return text

    while offset < end:
        extension = read_string()
        if not extension:
            break
        while True:
            directory = read_string()
            if not directory:
                break
            while True:
                name = read_string()
                if not name:
                    break
                preload = struct.unpack_from("<IHHIIH", data, offset)[1]
                offset += 18 + preload
                folder = "" if directory == " " else directory + "/"
                paths.add(f"{folder}{name}.{extension}".lower())
    return paths


def c_string(data: bytes, offset: int) -> str:
    stop = data.index(b"\0", offset)
    return data[offset:stop].decode("latin1")


def mdl_references(data: bytes) -> tuple[list[str], list[str], list[str]]:
    texture_count, texture_index, search_count, search_index = struct.unpack_from("<iiii", data, 0xCC)
    include_count, include_index = struct.unpack_from("<ii", data, 0x150)

    textures = []
    for index in range(texture_count):
        entry = texture_index + index * 64
        textures.append(c_string(data, entry + struct.unpack_from("<i", data, entry)[0]))

    search_paths = []
    for index in range(search_count):
        search_paths.append(c_string(data, struct.unpack_from("<i", data, search_index + index * 4)[0]))

    includes = []
    for index in range(include_count):
        entry = include_index + index * 8
        includes.append(c_string(data, entry + struct.unpack_from("<i", data, entry + 4)[0]))

    return textures, search_paths, includes


def normalize(path: str) -> str:
    return "/".join(part for part in path.replace("\\", "/").lower().split("/") if part)


def vmt_tokens(text: str) -> list[str]:
    tokens, current, quoted = [], [], False
    for character in text:
        if character == '"':
            if quoted:
                tokens.append("".join(current))
                current = []
            quoted = not quoted
        elif quoted:
            current.append(character)
        elif character.isspace() or character in "{}":
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(character)
    if current:
        tokens.append("".join(current))
    return tokens


class Collector:
    def __init__(self, game: Path):
        self.game = game
        self.packed = read_vpk_paths(game / "pak01_dir.vpk")
        self.loose = {normalize(str(path.relative_to(game))): path
                      for root in ("models", "materials")
                      for path in (game / root).rglob("*") if path.is_file()}
        self.wanted: dict[str, Path] = {}
        self.missing: set[str] = set()
        self.seen: set[str] = set()

    def needed(self, relative: str) -> bool:
        return relative in self.loose and relative not in self.packed

    def add(self, relative: str) -> None:
        if self.needed(relative):
            self.wanted[relative] = self.loose[relative]

    def model(self, relative: str) -> None:
        relative = normalize(relative)
        if relative in self.seen:
            return
        self.seen.add(relative)
        if relative not in self.loose:
            if relative not in self.packed:
                self.missing.add(relative)
            return

        stem = relative[: -len(".mdl")]
        for path, source in self.loose.items():
            if path.startswith(stem + ".") or path == relative:
                self.add(path)

        textures, search_paths, includes = mdl_references(self.loose[relative].read_bytes())
        for include in includes:
            self.model(include)
        for texture in textures:
            found = False
            for search in search_paths or [""]:
                candidate = normalize(f"materials/{search}/{texture}.vmt")
                if candidate in self.loose or candidate in self.packed:
                    self.material(candidate)
                    found = True
                    break
            if not found:
                self.missing.add(f"materials/<{'|'.join(search_paths)}>/{texture}.vmt")

    def material(self, relative: str) -> None:
        if relative in self.seen:
            return
        self.seen.add(relative)
        self.add(relative)
        if relative not in self.loose:
            return

        text = self.loose[relative].read_text("latin1", errors="ignore")
        for token in vmt_tokens(text):
            token = normalize(token)
            if not token or token.startswith("$") or token.startswith("%"):
                continue
            for candidate in (token, f"materials/{token}"):
                for extension in ("", ".vtf", ".vmt"):
                    path = normalize(candidate + extension)
                    if path.endswith(".vmt") and (path in self.loose or path in self.packed):
                        self.material(path)
                    elif path.endswith(".vtf"):
                        self.add(path)


def main() -> None:
    arguments = [argument for argument in sys.argv[1:] if not argument.startswith("--")]
    game = Path(arguments[0]) if arguments else DEFAULT_GAME
    output = Path(__file__).resolve().parent / "csgo"

    collector = Collector(game)
    for agent in AGENTS:
        collector.model(f"{MODEL_DIR}/{agent}.mdl")

    if output.exists():
        shutil.rmtree(output)
    total = 0
    for relative, source in sorted(collector.wanted.items()):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        total += source.stat().st_size

    print(f"{len(collector.wanted)} files, {total / 1048576:.1f} MB -> {output}")
    for path in sorted(collector.missing):
        print(f"missing: {path}")

    if "--zip" in sys.argv:
        archive = shutil.make_archive(str(output.parent / "divinity-agents"), "zip", output.parent, "csgo")
        print(f"zip: {archive}")


if __name__ == "__main__":
    main()
