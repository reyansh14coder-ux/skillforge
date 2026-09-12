"""Core data models for SkillForge skills and compositions."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SkillFramework(str, Enum):
    """Supported AI agent frameworks."""

    CLAUDE_CODE = "claude-code"
    CODEX = "codex"
    CURSOR = "cursor"
    CLINE = "cline"
    OPENCODE = "opencode"
    UNIVERSAL = "universal"


class SkillCapability(str, Enum):
    """What a skill can do."""

    TOOL = "tool"
    WORKFLOW = "workflow"
    AGENT = "agent"
    HOOK = "hook"
    RULE = "rule"
    PROMPT = "prompt"
    DATASET = "dataset"


class SkillVersion(BaseModel):
    """Semantic version of a skill."""

    major: int = 0
    minor: int = 1
    patch: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, version_str: str) -> SkillVersion:
        parts = version_str.strip().lstrip("v").split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version: {version_str}")
        return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))

    def satisfies(self, constraint: str) -> bool:
        """Check if this version satisfies a constraint like '>=1.0.0' or '^1.0.0'."""
        constraint = constraint.strip()
        if constraint.startswith(">="):
            required = SkillVersion.parse(constraint[2:])
            return self >= required
        elif constraint.startswith("^"):
            required = SkillVersion.parse(constraint[1:])
            return self.major == required.major and self >= required
        elif constraint.startswith("~"):
            required = SkillVersion.parse(constraint[1:])
            return (
                self.major == required.major
                and self.minor == required.minor
                and self >= required
            )
        else:
            return self == SkillVersion.parse(constraint)

    def __ge__(self, other: SkillVersion) -> bool:
        return (self.major, self.minor, self.patch) >= (
            other.major,
            other.minor,
            other.patch,
        )

    def __gt__(self, other: SkillVersion) -> bool:
        return (self.major, self.minor, self.patch) > (
            other.major,
            other.minor,
            other.patch,
        )

    def __le__(self, other: SkillVersion) -> bool:
        return (self.major, self.minor, self.patch) <= (
            other.major,
            other.minor,
            other.patch,
        )

    def __lt__(self, other: SkillVersion) -> bool:
        return (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        )


class SkillDependency(BaseModel):
    """A dependency on another skill."""

    name: str
    version_constraint: str = ">=0.1.0"
    optional: bool = False
    framework: SkillFramework | None = None

    @property
    def is_satisfied_by(self) -> str:
        """Human-readable constraint description."""
        return f"{self.name} {self.version_constraint}"


class SkillMetadata(BaseModel):
    """Metadata about a skill."""

    name: str = Field(..., min_length=1, max_length=100)
    version: SkillVersion = Field(default_factory=SkillVersion)
    description: str = Field(..., min_length=10, max_length=500)
    author: str = Field(..., min_length=1)
    license: str = "MIT"
    framework: SkillFramework = SkillFramework.UNIVERSAL
    capability: SkillCapability = SkillCapability.TOOL
    tags: list[str] = Field(default_factory=list)
    dependencies: list[SkillDependency] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    homepage: str | None = None
    repository: str | None = None
    icon: str | None = None

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: list[str] | str | None) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [tag.lower().strip() for tag in v.split(",") if tag.strip()]
        return [tag.lower().strip() for tag in v if isinstance(tag, str) and tag.strip()]


class SkillConfig(BaseModel):
    """Runtime configuration for a skill."""

    env_vars: dict[str, str] = Field(default_factory=dict)
    requires_permissions: list[str] = Field(default_factory=list)
    max_execution_time_seconds: int = 300
    sandbox_required: bool = False
    isolated: bool = False


class Skill(BaseModel):
    """A complete skill definition."""

    metadata: SkillMetadata
    config: SkillConfig = Field(default_factory=SkillConfig)
    content: dict[str, Any] = Field(default_factory=dict)
    files: dict[str, str] = Field(default_factory=dict)
    entry_point: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def fingerprint(self) -> str:
        """Generate a content fingerprint for integrity checking."""
        import json

        content_str = json.dumps(
            {
                "name": self.metadata.name,
                "version": str(self.metadata.version),
                "content": self.content,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    @property
    def full_name(self) -> str:
        """Fully qualified skill name."""
        return f"{self.metadata.author}/{self.metadata.name}"

    def to_skill_md(self) -> str:
        """Export skill as a Claude Code compatible SKILL.md."""
        lines = [
            f"# {self.metadata.name}",
            "",
            self.metadata.description,
            "",
            f"**Author:** {self.metadata.author}",
            f"**Version:** {self.metadata.version}",
            f"**Framework:** {self.metadata.framework.value}",
            f"**Capability:** {self.metadata.capability.value}",
            "",
        ]

        if self.metadata.tags:
            lines.append(f"**Tags:** {', '.join(self.metadata.tags)}")
            lines.append("")

        if self.metadata.dependencies:
            lines.append("## Dependencies")
            lines.append("")
            for dep in self.metadata.dependencies:
                optional = " (optional)" if dep.optional else ""
                lines.append(f"- {dep.name} {dep.version_constraint}{optional}")
            lines.append("")

        if self.config.env_vars:
            lines.append("## Environment Variables")
            lines.append("")
            for var, desc in self.config.env_vars.items():
                lines.append(f"- `{var}`: {desc}")
            lines.append("")

        if self.content:
            lines.append("## Instructions")
            lines.append("")
            for key, value in self.content.items():
                if isinstance(value, str):
                    lines.append(f"### {key}")
                    lines.append("")
                    lines.append(value)
                    lines.append("")

        return "\n".join(lines)


class InstalledSkill(BaseModel):
    """A skill that has been installed locally."""

    skill: Skill
    installed_at: datetime = Field(default_factory=datetime.utcnow)
    installed_version: SkillVersion | None = None
    source: str = "registry"
    enabled: bool = True

    @property
    def needs_update(self) -> bool:
        """Check if an update is available."""
        if self.installed_version is None:
            return False
        return self.skill.metadata.version > self.installed_version


class CompositionStep(BaseModel):
    """A single step in a skill composition."""

    skill_name: str
    skill_version: SkillVersion
    action: str
    params: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    condition: str | None = None
    timeout: int = 300


class CompositionPlan(BaseModel):
    """A plan for composing multiple skills together."""

    name: str
    description: str = ""
    steps: list[CompositionStep] = Field(default_factory=list)
    skills_used: list[str] = Field(default_factory=list)
    estimated_duration_seconds: int = 0

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def skill_count(self) -> int:
        return len(self.skills_used)
