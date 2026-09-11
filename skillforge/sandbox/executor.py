"""Sandbox execution environment for skills."""

from __future__ import annotations

import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from skillforge.core.models import Skill


@dataclass
class SandboxResult:
    """Result of running a skill in a sandbox."""

    success: bool
    output: str = ""
    error: str = ""
    duration_seconds: float = 0.0
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SkillSandbox:
    """Provides isolated execution environments for skills."""

    def __init__(self, sandbox_dir: Path | None = None):
        self.sandbox_dir = sandbox_dir or Path(tempfile.mkdtemp(prefix="skillforge_"))
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

    def prepare(self, skill: Skill) -> Path:
        """Prepare a sandbox environment for a skill."""
        skill_dir = self.sandbox_dir / skill.metadata.name
        skill_dir.mkdir(exist_ok=True)

        skill_md = skill.to_skill_md()
        (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

        for filename, content in skill.files.items():
            file_path = skill_dir / "files" / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        if skill.content:
            import json

            with open(skill_dir / "skill_content.json", "w", encoding="utf-8") as f:
                json.dump(skill.content, f, indent=2)

        return skill_dir

    def run_command(
        self,
        command: list[str],
        cwd: Path | None = None,
        timeout: int = 300,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        """Run a command in the sandbox."""
        start_time = time.time()

        import os

        sandbox_env = os.environ.copy()
        if env:
            sandbox_env.update(env)

        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.sandbox_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=sandbox_env,
            )
            duration = time.time() - start_time

            return SandboxResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                duration_seconds=duration,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                error=f"Command timed out after {timeout} seconds",
                duration_seconds=time.time() - start_time,
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    def validate_skill(self, skill: Skill) -> SandboxResult:
        """Validate a skill in the sandbox."""
        warnings: list[str] = []

        skill_dir = self.prepare(skill)

        if not skill.metadata.description:
            warnings.append("No description provided")

        if len(skill.metadata.tags) == 0:
            warnings.append("No tags provided")

        if not skill.metadata.author or skill.metadata.author == "unknown":
            warnings.append("Author not specified")

        if skill.metadata.version == skill.metadata.version.__class__():
            warnings.append("Version is 0.1.0 (default)")

        skill_md_content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        if len(skill_md_content) < 50:
            warnings.append("SKILL.md content is very short")

        return SandboxResult(
            success=True,
            output=f"Validation passed for {skill.metadata.name}",
            duration_seconds=0.0,
            warnings=warnings,
        )

    def test_skill(
        self,
        skill: Skill,
        test_command: str | None = None,
        timeout: int = 60,
    ) -> SandboxResult:
        """Test a skill with a test command."""
        skill_dir = self.prepare(skill)

        if test_command:
            return self.run_command(
                ["bash", "-c", test_command],
                cwd=skill_dir,
                timeout=timeout,
            )

        if skill.entry_point:
            return self.run_command(
                ["python", skill.entry_point],
                cwd=skill_dir,
                timeout=timeout,
            )

        return SandboxResult(
            success=True,
            output="No test command specified, skill prepared successfully",
        )

    def diff(
        self,
        skill_before: Skill,
        skill_after: Skill,
    ) -> dict[str, Any]:
        """Compare two versions of a skill."""
        changes: dict[str, Any] = {
            "metadata_changed": False,
            "content_changed": False,
            "files_changed": [],
            "files_added": [],
            "files_removed": [],
        }

        if skill_before.metadata != skill_after.metadata:
            changes["metadata_changed"] = True

        if skill_before.content != skill_after.content:
            changes["content_changed"] = True

        before_files = set(skill_before.files.keys())
        after_files = set(skill_after.files.keys())

        changes["files_added"] = list(after_files - before_files)
        changes["files_removed"] = list(before_files - after_files)
        changes["files_changed"] = [
            f
            for f in before_files.intersection(after_files)
            if skill_before.files[f] != skill_after.files[f]
        ]

        return changes

    def cleanup(self) -> None:
        """Clean up the sandbox directory."""
        import shutil

        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir)
