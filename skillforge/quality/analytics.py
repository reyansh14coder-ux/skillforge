"""Skill analytics and statistics tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class SkillAnalytics:
    """Analytics data for a skill."""

    name: str
    publish_count: int = 0
    download_count: int = 0
    search_count: int = 0
    install_count: int = 0
    test_count: int = 0
    last_published: str = ""
    last_accessed: str = ""
    versions: list[str] = field(default_factory=list)
    tags_used: list[str] = field(default_factory=list)
    frameworks_used: list[str] = field(default_factory=list)


class AnalyticsTracker:
    """Tracks analytics across all skills."""

    def __init__(self) -> None:
        self._analytics: dict[str, SkillAnalytics] = {}

    def track_publish(self, skill_name: str, version: str, tags: list[str] | None = None) -> None:
        if skill_name not in self._analytics:
            self._analytics[skill_name] = SkillAnalytics(name=skill_name)

        a = self._analytics[skill_name]
        a.publish_count += 1
        a.last_published = datetime.now().isoformat()
        if version not in a.versions:
            a.versions.append(version)
        if tags:
            for tag in tags:
                if tag not in a.tags_used:
                    a.tags_used.append(tag)

    def track_access(self, skill_name: str, access_type: str = "view") -> None:
        if skill_name not in self._analytics:
            self._analytics[skill_name] = SkillAnalytics(name=skill_name)

        a = self._analytics[skill_name]
        a.last_accessed = datetime.now().isoformat()

        if access_type == "download":
            a.download_count += 1
        elif access_type == "search":
            a.search_count += 1
        elif access_type == "install":
            a.install_count += 1
        elif access_type == "test":
            a.test_count += 1

    def get_analytics(self, skill_name: str) -> SkillAnalytics | None:
        return self._analytics.get(skill_name)

    def get_all_analytics(self) -> list[SkillAnalytics]:
        return list(self._analytics.values())

    def get_top_skills(self, limit: int = 10) -> list[SkillAnalytics]:
        skills = sorted(
            self._analytics.values(),
            key=lambda x: x.download_count + x.install_count,
            reverse=True,
        )
        return skills[:limit]

    def get_recent(self, days: int = 7) -> list[SkillAnalytics]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = []
        for a in self._analytics.values():
            if a.last_accessed:
                try:
                    accessed = datetime.fromisoformat(a.last_accessed)
                    if accessed.tzinfo is None:
                        accessed = accessed.replace(tzinfo=timezone.utc)
                    if accessed > cutoff:
                        result.append(a)
                except (ValueError, TypeError):
                    pass
        return result

    def get_summary(self) -> dict:
        all_skills = list(self._analytics.values())
        total_downloads = sum(s.download_count for s in all_skills)
        total_installs = sum(s.install_count for s in all_skills)
        total_searches = sum(s.search_count for s in all_skills)

        return {
            "total_skills": len(all_skills),
            "total_downloads": total_downloads,
            "total_installs": total_installs,
            "total_searches": total_searches,
            "active_skills": len(self.get_recent(7)),
            "top_skill": all_skills[0].name if all_skills else None,
        }
