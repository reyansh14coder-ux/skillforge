"""Skill registry for storing and discovering skills."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from skillforge.core.models import Skill, SkillVersion
from skillforge.core.resolver import DependencyResolver


class SkillRegistry:
    """Local skill registry for storing, searching, and managing skills."""

    def __init__(self, registry_path: Path | None = None):
        from platformdirs import user_data_dir

        self.registry_path = registry_path or Path(user_data_dir("skillforge")) / "registry"
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self._index_path = self.registry_path / "index.json"
        self._skills_dir = self.registry_path / "skills"
        self._skills_dir.mkdir(exist_ok=True)
        self._index: dict[str, Any] = self._load_index()

    def _load_index(self) -> dict[str, Any]:
        if self._index_path.exists():
            try:
                with open(self._index_path, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {"skills": {}, "updated_at": None}
        return {"skills": {}, "updated_at": None}

    def _save_index(self) -> None:
        self._index["updated_at"] = datetime.utcnow().isoformat()
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2)

    def publish(self, skill: Skill) -> str:
        """Publish a skill to the registry."""
        skill_id = skill.full_name.replace("/", "_").replace("\\", "_")
        version_str = str(skill.metadata.version)

        skill_dir = self._skills_dir / skill_id
        skill_dir.mkdir(exist_ok=True)

        version_dir = skill_dir / version_str
        version_dir.mkdir(exist_ok=True)

        skill_data = skill.model_dump(mode="json")
        skill_data["published_at"] = datetime.utcnow().isoformat()

        with open(version_dir / "skill.json", "w", encoding="utf-8") as f:
            json.dump(skill_data, f, indent=2)

        skill_md = skill.to_skill_md()
        with open(version_dir / "SKILL.md", "w", encoding="utf-8") as f:
            f.write(skill_md)

        for filename, content in skill.files.items():
            file_path = version_dir / "files" / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        if skill_id not in self._index["skills"]:
            self._index["skills"][skill_id] = {
                "name": skill.metadata.name,
                "author": skill.metadata.author,
                "versions": [],
                "latest": version_str,
                "description": skill.metadata.description,
                "tags": skill.metadata.tags,
                "capability": skill.metadata.capability.value,
                "framework": skill.metadata.framework.value,
            }

        versions = self._index["skills"][skill_id]["versions"]
        if version_str not in versions:
            versions.append(version_str)
            versions.sort(
                key=lambda v: SkillVersion.parse(v),
                reverse=True,
            )

        self._index["skills"][skill_id]["latest"] = versions[0]
        self._save_index()

        return f"{skill_id}@{version_str}"

    def get_skill(self, name: str, version: str | None = None) -> Skill | None:
        """Retrieve a skill from the registry."""
        skill_id = name.replace("/", "_").replace("\\", "_")

        if skill_id not in self._index["skills"]:
            for sid, info in self._index["skills"].items():
                if info["name"] == name:
                    skill_id = sid
                    break
            else:
                return None

        skill_info = self._index["skills"][skill_id]

        if version is None:
            version = skill_info["latest"]

        version_dir = self._skills_dir / skill_id / version
        skill_json = version_dir / "skill.json"

        if not skill_json.exists():
            return None

        with open(skill_json, encoding="utf-8") as f:
            data = json.load(f)

        return Skill.model_validate(data)

    def search(
        self,
        query: str = "",
        tags: list[str] | None = None,
        capability: str | None = None,
        framework: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search for skills in the registry."""
        results: list[dict[str, Any]] = []

        for skill_id, info in self._index["skills"].items():
            if len(results) >= limit:
                break

            if query:
                query_lower = query.lower()
                name_match = query_lower in info["name"].lower()
                desc_match = query_lower in info.get("description", "").lower()
                tag_match = any(query_lower in t.lower() for t in info.get("tags", []))
                if not (name_match or desc_match or tag_match):
                    continue

            if tags:
                skill_tags = set(info.get("tags", []))
                if not set(tags).intersection(skill_tags):
                    continue

            if capability and info.get("capability") != capability:
                continue

            if framework and info.get("framework") != framework:
                continue

            results.append(
                {
                    "name": info["name"],
                    "author": info["author"],
                    "version": info["latest"],
                    "description": info.get("description", ""),
                    "tags": info.get("tags", []),
                    "capability": info.get("capability", ""),
                    "framework": info.get("framework", ""),
                    "skill_id": skill_id,
                }
            )

        return results

    def list_skills(self) -> list[dict[str, Any]]:
        """List all skills in the registry."""
        return [
            {
                "name": info["name"],
                "author": info["author"],
                "version": info["latest"],
                "description": info.get("description", ""),
                "versions": info.get("versions", []),
            }
            for info in self._index["skills"].values()
        ]

    def delete_skill(self, name: str, version: str | None = None) -> bool:
        """Delete a skill from the registry."""
        skill_id = name.replace("/", "_").replace("\\", "_")

        actual_id = skill_id
        if skill_id not in self._index["skills"]:
            for sid, info in self._index["skills"].items():
                if info["name"] == name:
                    actual_id = sid
                    break
            else:
                return False

        if version:
            version_dir = self._skills_dir / actual_id / version
            if version_dir.exists():
                import shutil

                shutil.rmtree(version_dir)

            versions = self._index["skills"][actual_id]["versions"]
            if version in versions:
                versions.remove(version)

            if not versions:
                del self._index["skills"][actual_id]
                skill_dir = self._skills_dir / actual_id
                if skill_dir.exists():
                    import shutil

                    shutil.rmtree(skill_dir)
            else:
                self._index["skills"][actual_id]["latest"] = versions[0]
        else:
            skill_dir = self._skills_dir / actual_id
            if skill_dir.exists():
                import shutil

                shutil.rmtree(skill_dir)
            del self._index["skills"][actual_id]

        self._save_index()
        return True

    def get_resolver(self) -> DependencyResolver:
        """Get a dependency resolver with all registry skills loaded."""
        resolver = DependencyResolver()
        for _skill_id, info in self._index["skills"].items():
            skill = self.get_skill(info["name"], info["latest"])
            if skill:
                resolver.register_skill(skill)
        return resolver

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        total_skills = len(self._index["skills"])
        total_versions = sum(
            len(info.get("versions", []))
            for info in self._index["skills"].values()
        )

        capabilities: dict[str, int] = {}
        frameworks: dict[str, int] = {}
        all_tags: dict[str, int] = {}

        for info in self._index["skills"].values():
            cap = info.get("capability", "unknown")
            capabilities[cap] = capabilities.get(cap, 0) + 1

            fw = info.get("framework", "unknown")
            frameworks[fw] = frameworks.get(fw, 0) + 1

            for tag in info.get("tags", []):
                all_tags[tag] = all_tags.get(tag, 0) + 1

        top_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_skills": total_skills,
            "total_versions": total_versions,
            "capabilities": capabilities,
            "frameworks": frameworks,
            "top_tags": dict(top_tags),
        }
