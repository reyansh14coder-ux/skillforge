"""CLI-level tests for SkillForge (click's CliRunner)."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from skillforge.cli.main import cli
from skillforge.core.models import (
    Skill,
    SkillDependency,
    SkillMetadata,
    SkillVersion,
)
from skillforge.registry.store import SkillRegistry


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def isolated_registry(
    tmp_path, monkeypatch  # noqa: ANN001
) -> SkillRegistry:
    """Point the CLI's registry at a throw-away directory."""
    registry = SkillRegistry(registry_path=tmp_path / "registry")
    monkeypatch.setattr(
        "skillforge.cli.main.get_registry",
        lambda: SkillRegistry(registry_path=registry.registry_path),
    )
    return registry


def make_skill(name: str, deps: list[str] | None = None) -> Skill:
    return Skill(
        metadata=SkillMetadata(
            name=name,
            version=SkillVersion(major=0, minor=2, patch=0),
            description=f"Skill {name} used by CLI tests",
            author="cli-tests",
            dependencies=[
                SkillDependency(name=d, version_constraint=">=0.1.0")
                for d in (deps or [])
            ],
        ),
    )


def test_help_lists_new_commands(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    for cmd in ("graph", "compare", "completion", "doctor", "validate"):
        assert cmd in result.output


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0


def test_init_non_interactive_and_validate(runner: CliRunner, tmp_path) -> None:  # noqa: ANN001
    result = runner.invoke(
        cli,
        ["init", str(tmp_path), "--name", "t-skill", "--author", "tester"],
    )
    assert result.exit_code == 0
    assert (tmp_path / "skillforge.yaml").exists()
    assert (tmp_path / "SKILL.md").exists()

    result = runner.invoke(cli, ["validate", str(tmp_path)])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["validate", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["valid"] is True
    assert payload["name"] == "t-skill"


def test_validate_strict_fails_on_warnings(
    runner: CliRunner, tmp_path  # noqa: ANN001
) -> None:
    runner.invoke(
        cli, ["init", str(tmp_path), "--name", "t2", "--author", "tester"]
    )
    result = runner.invoke(cli, ["validate", str(tmp_path), "--strict"])
    # Fresh skills always carry warnings (default version, no tags, ...)
    assert result.exit_code == 1


def test_validate_invalid_directory_fails(
    runner: CliRunner, tmp_path  # noqa: ANN001
) -> None:
    result = runner.invoke(cli, ["validate", str(tmp_path)])
    assert result.exit_code == 1
    result = runner.invoke(cli, ["validate", str(tmp_path), "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["valid"] is False


def test_init_from_template(runner: CliRunner, tmp_path) -> None:  # noqa: ANN001
    result = runner.invoke(
        cli,
        ["init", str(tmp_path), "--template", "code-review"],
    )
    assert result.exit_code == 0
    assert (tmp_path / "SKILL.md").exists()
    assert (tmp_path / "skillforge.yaml").exists()


def test_init_unknown_template_fails(
    runner: CliRunner, tmp_path  # noqa: ANN001
) -> None:
    result = runner.invoke(
        cli, ["init", str(tmp_path), "--template", "no-such-template-xyz"]
    )
    assert result.exit_code == 1


def test_templates_list_and_inspect(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["templates", "list"])
    assert result.exit_code == 0
    assert "code-review" in result.output

    result = runner.invoke(cli, ["templates", "inspect", "code-review"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["templates", "inspect", "nope-xyz"])
    assert result.exit_code == 1


def test_completion_scripts(runner: CliRunner) -> None:
    for shell in ("bash", "zsh", "fish", "powershell"):
        result = runner.invoke(cli, ["completion", shell])
        assert result.exit_code == 0, f"{shell}: {result.output}"
        assert len(result.output) > 20


def test_completion_unknown_shell(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["completion", "tcsh"])
    assert result.exit_code == 2


def test_doctor_json(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["doctor", "--json"])
    assert result.exit_code in (0, 1)
    payload = json.loads(result.output)
    assert "checks" in payload
    assert payload["total"] >= 5
    assert any(c["check"] == "Python version" for c in payload["checks"])


def test_list_and_stats_json(
    runner: CliRunner, isolated_registry: SkillRegistry  # noqa: ARG001
) -> None:
    isolated_registry.publish(make_skill("alpha"))
    isolated_registry.publish(make_skill("beta"))

    result = runner.invoke(cli, ["list", "--json"])
    assert result.exit_code == 0
    names = {s["name"] for s in json.loads(result.output)}
    assert names == {"alpha", "beta"}

    result = runner.invoke(cli, ["stats", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["total_skills"] == 2


def test_search_json(
    runner: CliRunner, isolated_registry: SkillRegistry  # noqa: ARG001
) -> None:
    isolated_registry.publish(make_skill("findme"))

    result = runner.invoke(cli, ["search", "findme", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert any(s["name"] == "findme" for s in payload)

    result = runner.invoke(cli, ["search", "nothing-matches", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output) == []


def test_info_json(
    runner: CliRunner, isolated_registry: SkillRegistry  # noqa: ARG001
) -> None:
    isolated_registry.publish(make_skill("infome"))

    result = runner.invoke(cli, ["info", "infome", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["metadata"]["name"] == "infome"

    result = runner.invoke(cli, ["info", "ghost-skill", "--json"])
    assert result.exit_code == 1


def test_install_missing_fails(
    runner: CliRunner, isolated_registry: SkillRegistry  # noqa: ARG001
) -> None:
    result = runner.invoke(cli, ["install", "ghost-skill"])
    assert result.exit_code == 1


def test_graph_json_with_edges(
    runner: CliRunner, isolated_registry: SkillRegistry  # noqa: ARG001
) -> None:
    isolated_registry.publish(make_skill("base"))
    isolated_registry.publish(make_skill("app", deps=["base"]))

    result = runner.invoke(cli, ["graph", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert set(payload["nodes"]) == {"app", "base"}
    assert payload["edges"] == [{"from": "app", "to": "base"}]

    result = runner.invoke(cli, ["graph", "app", "--format", "mermaid"])
    assert result.exit_code == 0
    assert "app --> base" in result.output

    result = runner.invoke(cli, ["graph", "ghost", "--json"])
    assert result.exit_code == 1


def test_compare(
    runner: CliRunner, isolated_registry: SkillRegistry  # noqa: ARG001
) -> None:
    isolated_registry.publish(make_skill("left"))
    isolated_registry.publish(make_skill("right"))

    result = runner.invoke(cli, ["compare", "left", "right", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["winner"] in ("left", "right", "tie")
    assert payload["left"]["score"]["overall"] >= 0

    result = runner.invoke(cli, ["compare", "left", "ghost"])
    assert result.exit_code == 1


def test_convert_opencode(
    runner: CliRunner, isolated_registry: SkillRegistry, tmp_path  # noqa: ARG001
) -> None:
    from pathlib import Path

    isolated_registry.publish(make_skill("portable"))

    old_cwd = Path.cwd()
    try:
        import os

        os.chdir(tmp_path)
        result = runner.invoke(cli, ["convert", "portable", "--to", "opencode"])
        assert result.exit_code == 0
        text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "portable" in text
    finally:
        os.chdir(old_cwd)

    result = runner.invoke(cli, ["convert", "portable", "--to", "kubernetes"])
    assert result.exit_code == 2


def test_score_json(runner: CliRunner, tmp_path) -> None:  # noqa: ANN001
    runner.invoke(cli, ["init", str(tmp_path), "--name", "sc", "--author", "t"])
    result = runner.invoke(cli, ["score", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert 0 <= payload["overall"] <= 100
    assert "grade" in payload


def test_updates_runs(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["updates"])
    assert result.exit_code == 0


def test_batch_missing_fails(
    runner: CliRunner, isolated_registry: SkillRegistry  # noqa: ARG001
) -> None:
    result = runner.invoke(cli, ["batch", "ghost-a", "ghost-b"])
    assert result.exit_code == 1
