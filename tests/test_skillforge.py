"""Test suite for SkillForge."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skillforge.composition.engine import CompositionError, SkillComposition
from skillforge.core.loader import SkillLoader, SkillLoadError
from skillforge.core.models import (
    Skill,
    SkillCapability,
    SkillDependency,
    SkillFramework,
    SkillMetadata,
    SkillVersion,
)
from skillforge.core.resolver import (
    CircularDependencyError,
    DependencyResolver,
)
from skillforge.registry.store import SkillRegistry
from skillforge.sandbox.executor import SkillSandbox

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_skill() -> Skill:
    return Skill(
        metadata=SkillMetadata(
            name="test-skill",
            version=SkillVersion(major=1, minor=0, patch=0),
            description="A test skill for unit testing",
            author="test-author",
            framework=SkillFramework.UNIVERSAL,
            capability=SkillCapability.TOOL,
            tags=["test", "example"],
        ),
        content={"instructions": "Test instructions"},
    )


@pytest.fixture
def skill_with_deps() -> Skill:
    return Skill(
        metadata=SkillMetadata(
            name="dependent-skill",
            version=SkillVersion(major=1, minor=0, patch=0),
            description="A skill with dependencies",
            author="test-author",
            dependencies=[
                SkillDependency(name="base-skill", version_constraint=">=0.1.0"),
            ],
        ),
    )


@pytest.fixture
def base_skill() -> Skill:
    return Skill(
        metadata=SkillMetadata(
            name="base-skill",
            version=SkillVersion(major=0, minor=2, patch=0),
            description="A base skill",
            author="test-author",
        ),
    )


@pytest.fixture
def registry(tmp_path: Path) -> SkillRegistry:
    return SkillRegistry(registry_path=tmp_path / "registry")


@pytest.fixture
def loader() -> SkillLoader:
    return SkillLoader()


@pytest.fixture
def sandbox(tmp_path: Path) -> SkillSandbox:
    return SkillSandbox(sandbox_dir=tmp_path / "sandbox")


# ── Model Tests ───────────────────────────────────────────────────────────────


class TestSkillVersion:
    def test_parse(self) -> None:
        v = SkillVersion.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_str(self) -> None:
        v = SkillVersion(major=1, minor=2, patch=3)
        assert str(v) == "1.2.3"

    def test_satisfies_exact(self) -> None:
        v = SkillVersion(major=1, minor=0, patch=0)
        assert v.satisfies("1.0.0")

    def test_satisfies_gte(self) -> None:
        v = SkillVersion(major=1, minor=2, patch=0)
        assert v.satisfies(">=1.0.0")
        assert v.satisfies(">=1.2.0")
        assert not v.satisfies(">=2.0.0")

    def test_satisfies_caret(self) -> None:
        v = SkillVersion(major=1, minor=2, patch=3)
        assert v.satisfies("^1.0.0")
        assert v.satisfies("^1.2.0")
        assert not v.satisfies("^2.0.0")

    def test_satisfies_tilde(self) -> None:
        v = SkillVersion(major=1, minor=2, patch=3)
        assert v.satisfies("~1.2.0")
        assert not v.satisfies("~1.1.0")
        assert not v.satisfies("~1.3.0")

    def test_comparison(self) -> None:
        v1 = SkillVersion(major=1, minor=0, patch=0)
        v2 = SkillVersion(major=1, minor=1, patch=0)
        assert v2 > v1
        assert v1 < v2
        assert v1 <= v2
        assert v2 >= v1


class TestSkill:
    def test_fingerprint(self, sample_skill: Skill) -> None:
        fp = sample_skill.fingerprint
        assert len(fp) == 16
        assert isinstance(fp, str)

    def test_full_name(self, sample_skill: Skill) -> None:
        assert sample_skill.full_name == "test-author/test-skill"

    def test_to_skill_md(self, sample_skill: Skill) -> None:
        md = sample_skill.to_skill_md()
        assert "# test-skill" in md
        assert "test-author" in md
        assert "1.0.0" in md


# ── Resolver Tests ────────────────────────────────────────────────────────────


class TestDependencyResolver:
    def test_resolve_no_deps(self, sample_skill: Skill) -> None:
        resolver = DependencyResolver()
        resolver.register_skill(sample_skill)
        result = resolver.resolve(sample_skill)
        assert result.success
        assert len(result.resolved) == 0

    def test_resolve_with_deps(
        self, skill_with_deps: Skill, base_skill: Skill
    ) -> None:
        resolver = DependencyResolver()
        resolver.register_skill(base_skill)
        resolver.register_skill(skill_with_deps)
        result = resolver.resolve(skill_with_deps)
        assert result.success
        assert len(result.resolved) == 1

    def test_resolve_missing_dep(self, skill_with_deps: Skill) -> None:
        resolver = DependencyResolver()
        result = resolver.resolve(skill_with_deps)
        assert not result.success
        assert len(result.missing) == 1

    def test_resolve_version_conflict(
        self, skill_with_deps: Skill
    ) -> None:
        old_base = Skill(
            metadata=SkillMetadata(
                name="base-skill",
                version=SkillVersion(major=0, minor=0, patch=1),
                description="Old base skill version for testing",
                author="test",
            ),
        )
        resolver = DependencyResolver()
        resolver.register_skill(old_base)
        result = resolver.resolve(skill_with_deps)
        assert not result.success

    def test_get_install_order(self) -> None:
        skill_a = Skill(
            metadata=SkillMetadata(
                name="a", description="Skill A for testing", author="test",
                dependencies=[SkillDependency(name="b")],
            ),
        )
        skill_b = Skill(
            metadata=SkillMetadata(name="b", description="Skill B for testing", author="test"),
        )
        resolver = DependencyResolver()
        resolver.register_skill(skill_a)
        resolver.register_skill(skill_b)

        order = resolver.get_install_order([skill_a, skill_b])
        names = [s.metadata.name for s in order]
        assert names.index("b") < names.index("a")

    def test_check_compatibility(self) -> None:
        skill_a = Skill(
            metadata=SkillMetadata(
                name="a",
                description="Skill A for testing compat",
                author="test",
                framework=SkillFramework.CLAUDE_CODE,
            ),
        )
        skill_b = Skill(
            metadata=SkillMetadata(
                name="b",
                description="Skill B for testing compat",
                author="test",
                framework=SkillFramework.CODEX,
            ),
        )
        resolver = DependencyResolver()
        compatible, issues = resolver.check_compatibility(skill_a, skill_b)
        assert not compatible

    def test_circular_dependency(self) -> None:
        skill_a = Skill(
            metadata=SkillMetadata(
                name="a", description="Skill A circular test", author="test",
                dependencies=[SkillDependency(name="b")],
            ),
        )
        skill_b = Skill(
            metadata=SkillMetadata(
                name="b", description="Skill B circular test", author="test",
                dependencies=[SkillDependency(name="a")],
            ),
        )
        resolver = DependencyResolver()
        resolver.register_skill(skill_a)
        resolver.register_skill(skill_b)

        with pytest.raises(CircularDependencyError):
            resolver.get_install_order([skill_a, skill_b])


# ── Loader Tests ──────────────────────────────────────────────────────────────


class TestSkillLoader:
    def test_load_from_yaml(self, tmp_path: Path, loader: SkillLoader) -> None:
        yaml_content = """metadata:
  name: yaml-skill
  version: 1.0.0
  description: A skill loaded from YAML
  author: test
"""
        yaml_file = tmp_path / "skill.yaml"
        yaml_file.write_text(yaml_content)

        skill = loader.load_from_file(yaml_file)
        assert skill.metadata.name == "yaml-skill"
        assert skill.metadata.version == SkillVersion(major=1, minor=0, patch=0)

    def test_load_from_json(self, tmp_path: Path, loader: SkillLoader) -> None:
        json_data = {
            "metadata": {
                "name": "json-skill",
                "version": "2.0.0",
                "description": "A skill loaded from JSON",
                "author": "test",
            }
        }
        json_file = tmp_path / "skill.json"
        json_file.write_text(json.dumps(json_data))

        skill = loader.load_from_file(json_file)
        assert skill.metadata.name == "json-skill"

    def test_load_from_markdown(self, tmp_path: Path, loader: SkillLoader) -> None:
        md_content = """# md-skill

A skill loaded from Markdown.

**Author:** test
**Version:** 1.0.0

## Instructions

Do something useful.
"""
        md_file = tmp_path / "SKILL.md"
        md_file.write_text(md_content)

        skill = loader.load_from_file(md_file)
        assert skill.metadata.name == "md-skill"

    def test_load_from_directory(self, tmp_path: Path, loader: SkillLoader) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "skillforge.yaml").write_text(
            "metadata:\n  name: dir-skill\n  description: From directory\n  author: test\n"
        )

        skill = loader.load_from_directory(skill_dir)
        assert skill.metadata.name == "dir-skill"

    def test_load_nonexistent(self, loader: SkillLoader) -> None:
        with pytest.raises(SkillLoadError):
            loader.load_from_file(Path("/nonexistent/file.yaml"))

    def test_load_unsupported_type(self, tmp_path: Path, loader: SkillLoader) -> None:
        unsupported = tmp_path / "skill.exe"
        unsupported.write_text("binary")
        with pytest.raises(SkillLoadError):
            loader.load_from_file(unsupported)


# ── Registry Tests ────────────────────────────────────────────────────────────


class TestSkillRegistry:
    def test_publish_and_get(
        self, registry: SkillRegistry, sample_skill: Skill
    ) -> None:
        skill_id = registry.publish(sample_skill)
        assert "@" in skill_id

        retrieved = registry.get_skill("test-skill")
        assert retrieved is not None
        assert retrieved.metadata.name == "test-skill"

    def test_publish_multiple_versions(
        self, registry: SkillRegistry, sample_skill: Skill
    ) -> None:
        registry.publish(sample_skill)

        v2_skill = sample_skill.model_copy()
        v2_skill.metadata.version = SkillVersion(major=1, minor=1, patch=0)
        registry.publish(v2_skill)

        skill = registry.get_skill("test-skill")
        assert skill is not None
        assert skill.metadata.version == SkillVersion(major=1, minor=1, patch=0)

    def test_search(self, registry: SkillRegistry, sample_skill: Skill) -> None:
        registry.publish(sample_skill)

        results = registry.search(query="test")
        assert len(results) == 1
        assert results[0]["name"] == "test-skill"

    def test_search_by_tags(self, registry: SkillRegistry, sample_skill: Skill) -> None:
        registry.publish(sample_skill)

        results = registry.search(tags=["test"])
        assert len(results) == 1

    def test_delete(self, registry: SkillRegistry, sample_skill: Skill) -> None:
        registry.publish(sample_skill)
        assert registry.delete_skill("test-skill")
        assert registry.get_skill("test-skill") is None

    def test_stats(self, registry: SkillRegistry, sample_skill: Skill) -> None:
        registry.publish(sample_skill)
        stats = registry.get_stats()
        assert stats["total_skills"] == 1

    def test_list_skills(self, registry: SkillRegistry, sample_skill: Skill) -> None:
        registry.publish(sample_skill)
        skills = registry.list_skills()
        assert len(skills) == 1


# ── Sandbox Tests ─────────────────────────────────────────────────────────────


class TestSkillSandbox:
    def test_prepare(self, sandbox: SkillSandbox, sample_skill: Skill) -> None:
        skill_dir = sandbox.prepare(sample_skill)
        assert skill_dir.exists()
        assert (skill_dir / "SKILL.md").exists()

    def test_validate(self, sandbox: SkillSandbox, sample_skill: Skill) -> None:
        result = sandbox.validate_skill(sample_skill)
        assert result.success

    def test_run_command(self, sandbox: SkillSandbox) -> None:
        import sys
        if sys.platform == "win32":
            result = sandbox.run_command(["cmd", "/c", "echo", "hello"])
        else:
            result = sandbox.run_command(["echo", "hello"])
        assert result.success
        assert "hello" in result.output

    def test_diff(self, sandbox: SkillSandbox) -> None:
        skill_v1 = Skill(
            metadata=SkillMetadata(
                name="diff-test",
                version=SkillVersion(major=1, minor=0, patch=0),
                description="Diff test skill version 1",
                author="test",
            ),
            content={"instructions": "old instructions"},
            files={"a.txt": "content1"},
        )
        skill_v2 = Skill(
            metadata=SkillMetadata(
                name="diff-test",
                version=SkillVersion(major=1, minor=1, patch=0),
                description="Diff test skill version 2",
                author="test",
            ),
            content={"instructions": "new instructions"},
            files={"a.txt": "content2", "b.txt": "new"},
        )

        changes = sandbox.diff(skill_v1, skill_v2)
        assert changes["metadata_changed"]
        assert changes["content_changed"]
        assert "b.txt" in changes["files_added"]
        assert "a.txt" in changes["files_changed"]


# ── Composition Tests ─────────────────────────────────────────────────────────


class TestSkillComposition:
    def test_compose(
        self, base_skill: Skill, skill_with_deps: Skill
    ) -> None:
        composition = SkillComposition()
        composition.register_skill(base_skill)
        composition.register_skill(skill_with_deps)

        plan = composition.compose(["base-skill", "dependent-skill"])
        assert plan.step_count > 0
        assert len(plan.skills_used) == 2

    def test_chain(self) -> None:
        skill_a = Skill(
            metadata=SkillMetadata(name="a", description="Skill A chain test", author="test"),
        )
        skill_b = Skill(
            metadata=SkillMetadata(name="b", description="Skill B chain test", author="test"),
        )

        composition = SkillComposition()
        composition.register_skill(skill_a)
        composition.register_skill(skill_b)

        plan = composition.chain(["a", "b"])
        assert plan.step_count == 2
        assert plan.skills_used == ["a", "b"]

    def test_parallel(self) -> None:
        skill_a = Skill(
            metadata=SkillMetadata(name="a", description="Skill A parallel test", author="test"),
        )
        skill_b = Skill(
            metadata=SkillMetadata(name="b", description="Skill B parallel test", author="test"),
        )

        composition = SkillComposition()
        composition.register_skill(skill_a)
        composition.register_skill(skill_b)

        plan = composition.parallel(["a", "b"])
        assert plan.step_count == 2
        for step in plan.steps:
            assert step.params.get("parallel") is True

    def test_compose_missing_skill(self) -> None:
        composition = SkillComposition()
        with pytest.raises(CompositionError):
            composition.compose(["nonexistent"])

    def test_analyze(self) -> None:
        skill_a = Skill(
            metadata=SkillMetadata(name="a", description="Skill A analyze test", author="test"),
        )

        composition = SkillComposition()
        composition.register_skill(skill_a)

        plan = composition.parallel(["a"])
        analysis = composition.analyze(plan)
        assert analysis["total_steps"] == 1
        assert analysis["total_skills"] == 1

    def test_export_yaml(self) -> None:
        skill_a = Skill(
            metadata=SkillMetadata(name="a", description="Skill A export yaml test", author="test"),
        )

        composition = SkillComposition()
        composition.register_skill(skill_a)

        plan = composition.parallel(["a"])
        output = composition.export_plan(plan, output_format="yaml")
        assert "a" in output

    def test_export_json(self) -> None:
        skill_a = Skill(
            metadata=SkillMetadata(name="a", description="Skill A export json test", author="test"),
        )

        composition = SkillComposition()
        composition.register_skill(skill_a)

        plan = composition.parallel(["a"])
        output = composition.export_plan(plan, output_format="json")
        parsed = json.loads(output)
        assert "steps" in parsed

    def test_export_mermaid(self) -> None:
        skill_a = Skill(
            metadata=SkillMetadata(
                name="a",
                description="Skill A export mermaid test",
                author="test",
            ),
        )

        composition = SkillComposition()
        composition.register_skill(skill_a)

        plan = composition.parallel(["a"])
        output = composition.export_plan(plan, output_format="mermaid")
        assert "graph TD" in output


# ── Template Tests ─────────────────────────────────────────────────────────────


class TestTemplates:
    def test_list_templates(self) -> None:
        from skillforge.templates.registry import list_templates

        templates = list_templates()
        assert "code-review" in templates
        assert "security-audit" in templates
        assert "test-generator" in templates

    def test_get_template(self) -> None:
        from skillforge.templates.registry import get_template

        t = get_template("code-review")
        assert t is not None
        assert t["name"] == "code-review"
        assert t["description"]

    def test_get_template_not_found(self) -> None:
        from skillforge.templates.registry import get_template

        t = get_template("nonexistent")
        assert t is None

    def test_get_template_details(self) -> None:
        from skillforge.templates.registry import get_template_details

        d = get_template_details("code-review")
        assert d is not None
        assert d["name"] == "code-review"
        assert d["version"] == "0.1.0"

    def test_template_count(self) -> None:
        from skillforge.templates.registry import list_templates

        templates = list_templates()
        assert len(templates) >= 6


# ── Conversion Tests ───────────────────────────────────────────────────────────


class TestConversion:
    def test_to_cursor_format(self) -> None:
        from skillforge.cli.main import _to_cursor_format

        skill = Skill(
            metadata=SkillMetadata(
                name="test-skill",
                description="A test skill",
                author="test",
            ),
            content={"instructions": "Do something useful"},
        )
        output = _to_cursor_format(skill)
        assert "test-skill" in output
        assert "Do something useful" in output

    def test_to_cline_format(self) -> None:
        from skillforge.cli.main import _to_cline_format

        skill = Skill(
            metadata=SkillMetadata(
                name="test-skill",
                description="A test skill",
                author="test",
            ),
            content={"instructions": "Do something useful"},
        )
        output = _to_cline_format(skill)
        assert "test-skill" in output
        assert "Do something useful" in output
