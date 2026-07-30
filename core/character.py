"""可替换角色包加载器（支持 pixel / anime 画风变体）。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CharacterPack:
    """一个可热切换的角色模型包。"""

    id: str
    name: str
    title: str
    root: Path
    personality: str
    system_prompt: str
    bubble_lines: list[str]
    greetings: list[str]
    moe_hooks: dict[str, list[str]]
    colors: dict[str, str]
    skeleton: dict[str, Any]
    animations: dict[str, Any]
    scale: float = 1.0
    about: str = ""
    aliases: list[str] = field(default_factory=list)
    art_style: str = "anime"
    variants: list[str] = field(default_factory=lambda: ["anime"])
    clipboard_reactions: dict[str, list[str]] = field(default_factory=dict)
    schedule_lines: dict[str, list[str]] = field(default_factory=dict)

    @property
    def parts_dir(self) -> Path:
        variant_dir = self.root / "variants" / self.art_style / "parts"
        if variant_dir.is_dir():
            return variant_dir
        legacy = self.root / "parts"
        return legacy

    def with_art_style(self, style: str) -> "CharacterPack":
        if style not in self.variants and style != self.art_style:
            style = self.variants[0] if self.variants else self.art_style
        # skeleton may be variant-specific
        skel_path = self.root / "variants" / style / "skeleton.json"
        skeleton = (
            json.loads(skel_path.read_text(encoding="utf-8"))
            if skel_path.exists()
            else self.skeleton
        )
        return CharacterPack(
            id=self.id,
            name=self.name,
            title=self.title,
            root=self.root,
            personality=self.personality,
            system_prompt=self.system_prompt,
            bubble_lines=self.bubble_lines,
            greetings=self.greetings,
            moe_hooks=self.moe_hooks,
            colors=self.colors,
            skeleton=skeleton,
            animations=self.animations,
            scale=self.scale,
            about=self.about,
            aliases=self.aliases,
            art_style=style,
            variants=list(self.variants),
            clipboard_reactions=dict(self.clipboard_reactions),
            schedule_lines=dict(self.schedule_lines),
        )


def characters_root(base: Path | None = None) -> Path:
    base = base or Path(__file__).resolve().parent.parent
    return base / "characters"


def list_characters(base: Path | None = None) -> list[dict[str, str]]:
    root = characters_root(base)
    result: list[dict[str, str]] = []
    if not root.is_dir():
        return result
    for path in sorted(root.iterdir()):
        meta = path / "character.json"
        if not meta.exists():
            continue
        data = json.loads(meta.read_text(encoding="utf-8"))
        result.append(
            {
                "id": data.get("id", path.name),
                "name": data.get("name", path.name),
                "title": data.get("title", ""),
            }
        )
    return result


def load_character(
    character_id: str,
    base: Path | None = None,
    art_style: str | None = None,
) -> CharacterPack:
    root = characters_root(base) / character_id
    meta_path = root / "character.json"
    if not meta_path.exists():
        available = ", ".join(c["id"] for c in list_characters(base)) or "(无)"
        raise FileNotFoundError(f"角色包不存在: {character_id}；可用: {available}")

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    variants = list(data.get("variants", ["anime"]))
    style = art_style or data.get("default_variant") or (variants[0] if variants else "anime")
    if style not in variants and (root / "variants" / style).exists():
        variants.append(style)
    if style not in variants:
        style = variants[0]

    skel_variant = root / "variants" / style / "skeleton.json"
    skel_root = root / "skeleton.json"
    if skel_variant.exists():
        skeleton = json.loads(skel_variant.read_text(encoding="utf-8"))
    else:
        skeleton = json.loads(skel_root.read_text(encoding="utf-8"))

    animations = json.loads((root / "animations.json").read_text(encoding="utf-8"))

    return CharacterPack(
        id=data.get("id", character_id),
        name=data.get("name", character_id),
        title=data.get("title", ""),
        root=root,
        personality=data.get("personality", ""),
        system_prompt=data.get("system_prompt", ""),
        bubble_lines=list(data.get("bubble_lines", [])),
        greetings=list(data.get("greetings", [])),
        moe_hooks=dict(data.get("moe_hooks", {})),
        colors=dict(data.get("colors", {})),
        skeleton=skeleton,
        animations=animations,
        scale=float(data.get("scale", 1.0)),
        about=data.get("about", ""),
        aliases=list(data.get("aliases", [])),
        art_style=style,
        variants=variants,
        clipboard_reactions=dict(data.get("clipboard_reactions", {})),
        schedule_lines=dict(data.get("schedule_lines", {})),
    )
