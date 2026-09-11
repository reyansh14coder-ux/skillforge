"""Skill loader and parser for various skill formats."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from skillforge.core.models import (
    Skill,
    SkillCapability,
    SkillConfig,
    SkillDependency,
    SkillFramework,
    SkillMetadata,
    SkillVersion,
)


class SkillLoadError(Exception):
    """Raised when a skill cannot be loaded."""

    pass


class SkillLoader:
    """Loads skills from various formats and locations."""

    SUPPORTED_CONFIGS = [
        "skillforge.yaml",
        "skillforge.yml",
        "skillforge.json",
        "skill.md",
        "SKILL.md",
    ]

    def load_from_file(self, path: Path) -> Skill:
        """Load a skill from a file."""
        if not path.exists():
            raise SkillLoadError(f"File not found: {path}")

        if path.suffix in (".yaml", ".yml"):
            return self._load_yaml(path)
        elif path.suffix == ".json":
            return self._load_json(path)
        elif path.suffix == ".md":
            return self._load_markdown(path)
        else:
            raise SkillLoadError(f"Unsupported file type: {path.suffix}")

    def load_from_directory(self, directory: Path) -> Skill:
        """Load a skill from a directory containing skill files."""
        if not directory.is_dir():
            raise SkillLoadError(f"Not a directory: {directory}")

        for config_name in self.SUPPORTED_CONFIGS:
            config_path = directory / config_name
            if config_path.exists():
                return self.load_from_file(config_path)

        skill_files = list(directory.glob("*.md"))
        if skill_files:
            return self._load_markdown(skill_files[0])

        raise SkillLoadError(f"No skill configuration found in {directory}")

    def load_from_skill_md(self, content: str) -> Skill:
        """Parse a SKILL.md file into a Skill object."""
        return self._parse_skill_md(content)

    def _load_yaml(self, path: Path) -> Skill:
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SkillLoadError(f"Invalid YAML in {path}: {e}") from e
        return self._dict_to_skill(data, path.parent)

    def _load_json(self, path: Path) -> Skill:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise SkillLoadError(f"Invalid JSON in {path}: {e}") from e
        return self._dict_to_skill(data, path.parent)

    def _load_markdown(self, path: Path) -> Skill:
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            raise SkillLoadError(f"Cannot read {path}: {e}") from e
        return self._parse_skill_md(content)

    def _parse_skill_md(self, content: str) -> Skill:
        """Parse a SKILL.md markdown file into a Skill object."""
        lines = content.strip().split("\n")
        metadata: dict[str, Any] = {}
        current_section = "header"
        section_content: list[str] = []

        for line in lines:
            if line.startswith("# "):
                if current_section != "header" and section_content:
                    metadata[current_section] = "\n".join(section_content).strip()
                current_section = "header"
                metadata["name"] = line[2:].strip()
                section_content = []
            elif line.startswith("## "):
                if current_section != "header" and section_content:
                    metadata[current_section] = "\n".join(section_content).strip()
                current_section = line[3:].strip().lower().replace(" ", "_")
                section_content = []
            elif line.startswith("**") and "**:" in line:
                match = re.match(r"\*\*(.+?)\*\*:\s*(.+)", line)
                if match:
                    key = match.group(1).strip().lower().replace(" ", "_")
                    value = match.group(2).strip()
                    metadata[key] = value
            else:
                section_content.append(line)

        if section_content:
            metadata[current_section] = "\n".join(section_content).strip()

        name = metadata.get("name", "unnamed")
        description = metadata.get("description", metadata.get("header", ""))
        if not description or len(description) < 10:
            description = f"Skill: {name}"

        version_str = metadata.get("version", "0.1.0")
        try:
            version = SkillVersion.parse(version_str)
        except ValueError:
            version = SkillVersion()

        framework_str = metadata.get("framework", "universal")
        try:
            framework = SkillFramework(framework_str)
        except ValueError:
            framework = SkillFramework.UNIVERSAL

        capability_str = metadata.get("capability", "tool")
        try:
            capability = SkillCapability(capability_str)
        except ValueError:
            capability = SkillCapability.TOOL

        tags_str = metadata.get("tags", "")
        if isinstance(tags_str, str):
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        else:
            tags = tags_str if isinstance(tags_str, list) else []

        dependencies: list[SkillDependency] = []
        deps_raw = metadata.get("dependencies", "")
        if isinstance(deps_raw, str) and deps_raw:
            for dep_line in deps_raw.split("\n"):
                dep_line = dep_line.strip().lstrip("- ").strip()
                if dep_line:
                    parts = dep_line.split()
                    if len(parts) >= 2:
                        dependencies.append(
                            SkillDependency(
                                name=parts[0],
                                version_constraint=parts[1],
                            )
                        )
                    elif len(parts) == 1:
                        dependencies.append(SkillDependency(name=parts[0]))

        content_dict: dict[str, Any] = {}
        instructions = metadata.get("instructions", "")
        if instructions:
            content_dict["instructions"] = instructions

        for key in ["usage", "examples", "notes", "header"]:
            if key in metadata and key != "instructions":
                content_dict[key] = metadata[key]

        return Skill(
            metadata=SkillMetadata(
                name=name,
                version=version,
                description=description[:500],
                author=metadata.get("author", "unknown"),
                framework=framework,
                capability=capability,
                tags=tags,
                dependencies=dependencies,
            ),
            content=content_dict,
        )

    def _dict_to_skill(self, data: dict[str, Any], base_path: Path) -> Skill:
        """Convert a dictionary to a Skill object."""
        meta = data.get("metadata", data)

        name = meta.get("name", "unnamed")
        description = meta.get("description", f"Skill: {name}")

        version_str = meta.get("version", "0.1.0")
        if isinstance(version_str, str):
            version = SkillVersion.parse(version_str)
        elif isinstance(version_str, dict):
            version = SkillVersion(**version_str)
        else:
            version = SkillVersion()

        framework_str = meta.get("framework", "universal")
        try:
            framework = SkillFramework(framework_str)
        except ValueError:
            framework = SkillFramework.UNIVERSAL

        capability_str = meta.get("capability", "tool")
        try:
            capability = SkillCapability(capability_str)
        except ValueError:
            capability = SkillCapability.TOOL

        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]

        dependencies: list[SkillDependency] = []
        for dep in meta.get("dependencies", []):
            if isinstance(dep, str):
                parts = dep.split()
                dependencies.append(
                    SkillDependency(
                        name=parts[0],
                        version_constraint=parts[1] if len(parts) > 1 else ">=0.1.0",
                    )
                )
            elif isinstance(dep, dict):
                dependencies.append(SkillDependency(**dep))

        content = data.get("content", {})
        config_data = data.get("config", {})
        config = SkillConfig(**config_data) if config_data else SkillConfig()

        files: dict[str, str] = {}
        files_dir = base_path / "files"
        if files_dir.is_dir():
            for f in files_dir.rglob("*"):
                if f.is_file():
                    rel = str(f.relative_to(files_dir))
                    try:
                        files[rel] = f.read_text(encoding="utf-8")
                    except OSError:
                        pass

        entry_point = data.get("entry_point")

        return Skill(
            metadata=SkillMetadata(
                name=name,
                version=version,
                description=description[:500],
                author=meta.get("author", "unknown"),
                framework=framework,
                capability=capability,
                tags=tags,
                dependencies=dependencies,
                homepage=meta.get("homepage"),
                repository=meta.get("repository"),
            ),
            config=config,
            content=content,
            files=files,
            entry_point=entry_point,
        )
