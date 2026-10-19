"""Main CLI entry point for SkillForge."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from skillforge import __version__
from skillforge.composition.engine import CompositionError, SkillComposition
from skillforge.core.loader import SkillLoader, SkillLoadError
from skillforge.core.models import Skill, SkillVersion
from skillforge.registry.store import SkillRegistry
from skillforge.sandbox.executor import SkillSandbox

console = Console()


def _force_utf8() -> None:
    """Make CLI output safe on Windows cp1252 terminals.

    Without this, glyphs like ``✓`` raise UnicodeEncodeError inside rich's
    legacy Windows renderer and crash commands such as ``doctor``.
    """
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


_force_utf8()


def emit_json(data: Any) -> None:
    """Print machine-readable output and exit successfully."""
    click.echo(json.dumps(data, indent=2, default=str))


def get_registry() -> SkillRegistry:
    return SkillRegistry()


def get_loader() -> SkillLoader:
    return SkillLoader()


@click.group()
@click.version_option(version=__version__, prog_name="skillforge")
def cli() -> None:
    """SkillForge - The Universal AI Agent Skill Registry & Composition Engine.

    Discover, compose, and manage AI agent skills across any framework.
    """
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--name", "-n", help="Skill name override")
@click.option("--author", "-a", help="Author name")
@click.option("--framework", "-f", default="universal", help="Target framework")
@click.option(
    "--template",
    "-t",
    "template_name",
    default=None,
    help="Scaffold from a built-in template instead of a blank skill",
)
def init(
    path: str,
    name: str | None,
    author: str | None,
    framework: str,
    template_name: str | None,
) -> None:
    """Initialize a new skill project."""
    from skillforge.core.models import SkillFramework

    dir_path = Path(path)
    skill_name = name or dir_path.name

    if template_name:
        ctx = click.get_current_context()
        ctx.invoke(templates_use, template_name=template_name, target_dir=str(dir_path))
        return

    if not author:
        if sys.stdin.isatty():
            author = click.prompt("Author name")
        else:
            author = "anonymous"

    try:
        fw = SkillFramework(framework)
    except ValueError:
        fw = SkillFramework.UNIVERSAL

    skill_yaml = f"""metadata:
  name: {skill_name}
  version: 0.1.0
  description: "A new SkillForge skill"
  author: {author}
  framework: {fw.value}
  capability: tool
  tags: []

config:
  env_vars: {{}}
  requires_permissions: []
  max_execution_time_seconds: 300
  sandbox_required: false

content: {{}}
"""

    config_path = dir_path / "skillforge.yaml"
    if config_path.exists():
        console.print(f"[yellow]Warning:[/yellow] {config_path} already exists")
        if not click.confirm("Overwrite?"):
            return

    config_path.write_text(skill_yaml, encoding="utf-8")
    console.print(f"[green]Created[/green] {config_path}")

    skill_md = f"""# {skill_name}

A new SkillForge skill.

**Author:** {author}
**Version:** 0.1.0
**Framework:** {fw.value}
**Capability:** tool

## Instructions

Add your skill instructions here.
"""
    md_path = dir_path / "SKILL.md"
    md_path.write_text(skill_md, encoding="utf-8")
    console.print(f"[green]Created[/green] {md_path}")

    console.print(
        Panel(
            f"[bold green]Skill project initialized![/bold green]\n\n"
            f"  Name: {skill_name}\n"
            f"  Author: {author}\n"
            f"  Framework: {fw.value}\n\n"
            f"Next steps:\n"
            f"  1. Edit SKILL.md with your skill instructions\n"
            f"  2. Run [bold]skillforge validate .[/bold] to check your skill\n"
            f"  3. Run [bold]skillforge publish .[/bold] to publish to registry",
            title="SkillForge Init",
        )
    )


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--strict", is_flag=True, help="Enable strict validation")
@click.option("--json", "as_json", is_flag=True, help="Output results as JSON")
def validate(path: str, strict: bool, as_json: bool) -> None:
    """Validate a skill project. Exits non-zero when validation fails."""
    loader = get_loader()
    sandbox = SkillSandbox()

    try:
        skill_path = Path(path)
        if skill_path.is_dir():
            skill = loader.load_from_directory(skill_path)
        else:
            skill = loader.load_from_file(skill_path)

        result = sandbox.validate_skill(skill)
        failed = strict and bool(result.warnings)

        if as_json:
            emit_json(
                {
                    "name": skill.metadata.name,
                    "version": str(skill.metadata.version),
                    "valid": not failed,
                    "strict": strict,
                    "warnings": list(result.warnings),
                }
            )
            sys.exit(1 if failed else 0)

        table = Table(title=f"Validation: {skill.metadata.name}")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")

        table.add_row("Name", "OK", skill.metadata.name)
        table.add_row("Version", "OK", str(skill.metadata.version))
        table.add_row("Description", "OK", skill.metadata.description[:50])
        table.add_row("Author", "OK", skill.metadata.author)
        table.add_row("Framework", "OK", skill.metadata.framework.value)
        table.add_row("Capability", "OK", skill.metadata.capability.value)

        for warning in result.warnings:
            style = "red" if strict else "yellow"
            table.add_row("Warning", f"[{style}]WARN[/{style}]", warning)

        console.print(table)

        if failed:
            console.print(
                f"\n[red]Validation failed with {len(result.warnings)} warnings[/red]"
            )
            sys.exit(1)
        if result.warnings:
            console.print(
                f"\n[yellow]Validation passed with {len(result.warnings)} warnings[/yellow]"
            )
        else:
            console.print("\n[green]Validation passed![/green]")

    except SkillLoadError as e:
        if as_json:
            emit_json({"valid": False, "strict": strict, "error": str(e)})
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--version", "-v", help="Specific version to publish")
def publish(path: str, version: str | None) -> None:
    """Publish a skill to the local registry."""
    loader = get_loader()
    registry = get_registry()

    try:
        skill_path = Path(path)
        if skill_path.is_dir():
            skill = loader.load_from_directory(skill_path)
        else:
            skill = loader.load_from_file(skill_path)

        if version:
            skill.metadata.version = SkillVersion.parse(version)

        skill_id = registry.publish(skill)

        console.print(
            Panel(
                f"[bold green]Published![/bold green]\n\n"
                f"  Skill: {skill.metadata.name}\n"
                f"  Version: {skill.metadata.version}\n"
                f"  ID: {skill_id}\n\n"
                f"The skill is now available in your local registry.",
                title="SkillForge Publish",
            )
        )

    except SkillLoadError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.option("--version", "-v", help="Specific version to install")
def install(name: str, version: str | None) -> None:
    """Install a skill from the registry."""
    registry = get_registry()

    skill = registry.get_skill(name, version)
    if skill is None:
        console.print(f"[red]Skill not found:[/red] {name}")
        sys.exit(1)

    resolver = registry.get_resolver()
    resolution = resolver.resolve(skill)

    if not resolution.success:
        console.print("[red]Dependency resolution failed:[/red]")
        for conflict in resolution.conflicts:
            console.print(f"  - {conflict}")
        for missing in resolution.missing:
            console.print(f"  - Missing: {missing}")
        sys.exit(1)

    console.print(
        f"[green]Installed[/green] {skill.metadata.name} v{skill.metadata.version}"
    )

    if resolution.resolved:
        console.print("Dependencies resolved:")
        for dep in resolution.resolved:
            console.print(f"  - {dep.name} v{dep.version}")


@cli.command()
@click.argument("name", required=False)
@click.option("--version", "-v", help="Specific version")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def info(name: str | None, version: str | None, as_json: bool) -> None:
    """Show information about a skill."""
    registry = get_registry()

    if name:
        skill = registry.get_skill(name, version)
        if skill is None:
            console.print(f"[red]Skill not found:[/red] {name}")
            sys.exit(1)

        if as_json:
            emit_json(skill.model_dump(mode="json"))
            return

        table = Table(title=f"Skill: {skill.metadata.name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("Name", skill.metadata.name)
        table.add_row("Version", str(skill.metadata.version))
        table.add_row("Description", skill.metadata.description)
        table.add_row("Author", skill.metadata.author)
        table.add_row("Framework", skill.metadata.framework.value)
        table.add_row("Capability", skill.metadata.capability.value)
        table.add_row("Tags", ", ".join(skill.metadata.tags))
        table.add_row("License", skill.metadata.license)

        if skill.metadata.dependencies:
            deps = "\n".join(
                f"{d.name} {d.version_constraint}" for d in skill.metadata.dependencies
            )
            table.add_row("Dependencies", deps)

        console.print(table)
    else:
        skills = registry.list_skills()
        if as_json:
            emit_json(skills)
            return
        if not skills:
            console.print("[yellow]No skills in registry[/yellow]")
            return

        table = Table(title="Registry Skills")
        table.add_column("Name", style="cyan")
        table.add_column("Author")
        table.add_column("Version")
        table.add_column("Description")

        for s in skills:
            table.add_row(
                s["name"],
                s["author"],
                s["version"],
                s["description"][:50],
            )

        console.print(table)


@cli.command()
@click.argument("query", required=False)
@click.option("--tags", "-t", help="Filter by tags (comma-separated)")
@click.option("--capability", "-c", help="Filter by capability")
@click.option("--framework", "-f", help="Filter by framework")
@click.option("--limit", "-l", default=20, help="Max results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search(
    query: str | None,
    tags: str | None,
    capability: str | None,
    framework: str | None,
    limit: int,
    as_json: bool,
) -> None:
    """Search for skills in the registry."""
    registry = get_registry()

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    results = registry.search(
        query=query or "",
        tags=tag_list,
        capability=capability,
        framework=framework,
        limit=limit,
    )

    if as_json:
        emit_json(results)
        return

    if not results:
        console.print("[yellow]No skills found[/yellow]")
        return

    table = Table(title=f"Search Results ({len(results)} found)")
    table.add_column("Name", style="cyan")
    table.add_column("Author")
    table.add_column("Version")
    table.add_column("Capability")
    table.add_column("Description")

    for r in results:
        table.add_row(
            r["name"],
            r["author"],
            r["version"],
            r["capability"],
            r["description"][:40],
        )

    console.print(table)


@cli.command()
@click.argument("name")
@click.option("--version", "-v", help="Version to delete")
@click.option("--all", "delete_all", is_flag=True, help="Delete all versions")
def delete(name: str, version: str | None, delete_all: bool) -> None:
    """Delete a skill from the registry."""
    registry = get_registry()

    if delete_all:
        success = registry.delete_skill(name)
    else:
        if not version:
            version = click.prompt("Version to delete")
        success = registry.delete_skill(name, version)

    if success:
        console.print(f"[green]Deleted[/green] {name}" + (f" v{version}" if version else ""))
    else:
        console.print(f"[red]Not found:[/red] {name}")
        sys.exit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--timeout", "-t", default=60, help="Test timeout in seconds")
@click.option("--command", "-c", help="Custom test command")
def test(path: str, timeout: int, command: str | None) -> None:
    """Test a skill in a sandbox."""
    loader = get_loader()
    sandbox = SkillSandbox()

    try:
        skill_path = Path(path)
        if skill_path.is_dir():
            skill = loader.load_from_directory(skill_path)
        else:
            skill = loader.load_from_file(skill_path)

        console.print(f"Testing [cyan]{skill.metadata.name}[/cyan]...")

        result = sandbox.test_skill(skill, test_command=command, timeout=timeout)

        if result.success:
            console.print(
                Panel(
                    f"[bold green]Test passed![/bold green]\n\n"
                    f"Duration: {result.duration_seconds:.2f}s\n"
                    f"Output:\n{result.output[:500]}",
                    title="Test Result",
                )
            )
        else:
            console.print(
                Panel(
                    f"[bold red]Test failed![/bold red]\n\n"
                    f"Error:\n{result.error[:500]}",
                    title="Test Result",
                )
            )

        if result.warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for w in result.warnings:
                console.print(f"  - {w}")

        if not result.success:
            sys.exit(1)

    except SkillLoadError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    finally:
        sandbox.cleanup()


@cli.command()
@click.argument("skills", nargs=-1, required=True)
@click.option("--name", "-n", default="composed-workflow", help="Composition name")
@click.option(
    "--type",
    "comp_type",
    type=click.Choice(["auto", "chain", "parallel"]),
    default="auto",
)
@click.option(
    "--format",
    "-f",
    "out_format",
    type=click.Choice(["yaml", "json", "mermaid"]),
    default="yaml",
)
def compose(skills: tuple[str, ...], name: str, comp_type: str, out_format: str) -> None:
    """Compose multiple skills into a workflow."""
    registry = get_registry()
    composition = SkillComposition()
    missing = 0

    for skill_name in skills:
        skill = registry.get_skill(skill_name)
        if skill:
            composition.register_skill(skill)
        else:
            missing += 1
            console.print(f"[yellow]Warning:[/yellow] Skill {skill_name} not in registry, skipping")

    try:
        if comp_type == "chain":
            plan = composition.chain(list(skills), name=name)
        elif comp_type == "parallel":
            plan = composition.parallel(list(skills), name=name)
        else:
            plan = composition.compose(list(skills), name=name)

        analysis = composition.analyze(plan)

        output = composition.export_plan(plan, output_format=out_format)
        console.print(output)

        console.print(
            Panel(
                f"[bold]Composition Analysis[/bold]\n\n"
                f"Total steps: {analysis['total_steps']}\n"
                f"Total skills: {analysis['total_skills']}\n"
                f"Critical path length: {analysis['critical_path_length']}\n"
                f"Parallel groups: {len(analysis['parallel_groups'])}",
                title="Analysis",
            )
        )

        if analysis["potential_issues"]:
            console.print("\n[yellow]Potential issues:[/yellow]")
            for issue in analysis["potential_issues"]:
                console.print(f"  - {issue}")

        if missing:
            sys.exit(1)

    except CompositionError as e:
        console.print(f"[red]Composition error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def stats(as_json: bool) -> None:
    """Show registry statistics."""
    registry = get_registry()
    stats = registry.get_stats()

    if as_json:
        emit_json(stats)
        return

    table = Table(title="Registry Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value")

    table.add_row("Total Skills", str(stats["total_skills"]))
    table.add_row("Total Versions", str(stats["total_versions"]))

    console.print(table)

    if stats["capabilities"]:
        console.print("\n[bold]By Capability:[/bold]")
        for cap, count in stats["capabilities"].items():
            console.print(f"  {cap}: {count}")

    if stats["frameworks"]:
        console.print("\n[bold]By Framework:[/bold]")
        for fw, count in stats["frameworks"].items():
            console.print(f"  {fw}: {count}")

    if stats["top_tags"]:
        console.print("\n[bold]Top Tags:[/bold]")
        for tag, count in stats["top_tags"].items():
            console.print(f"  {tag}: {count}")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", "-o", default="skillforge-export", help="Export directory")
def export(path: str, output: str) -> None:
    """Export a skill as a distributable package."""
    loader = get_loader()

    try:
        skill_path = Path(path)
        if skill_path.is_dir():
            skill = loader.load_from_directory(skill_path)
        else:
            skill = loader.load_from_file(skill_path)

        export_dir = Path(output)
        export_dir.mkdir(parents=True, exist_ok=True)

        skill_md = skill.to_skill_md()
        (export_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

        import json

        skill_data = skill.model_dump(mode="json")
        (export_dir / "skill.json").write_text(
            json.dumps(skill_data, indent=2), encoding="utf-8"
        )

        for filename, content in skill.files.items():
            file_path = export_dir / "files" / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        console.print(
            f"[green]Exported[/green] {skill.metadata.name} to {export_dir}"
        )

    except SkillLoadError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("skill_name")
def tree(skill_name: str) -> None:
    """Show dependency tree for a skill."""
    registry = get_registry()
    skill = registry.get_skill(skill_name)

    if skill is None:
        console.print(f"[red]Skill not found:[/red] {skill_name}")
        sys.exit(1)

    dep_tree = Tree(f"[bold]{skill.metadata.name}[/bold] v{skill.metadata.version}")

    def add_deps(s: Skill, parent: Tree) -> None:
        for dep in s.metadata.dependencies:
            dep_skill = registry.get_skill(dep.name)
            if dep_skill:
                child = parent.add(
                    f"[cyan]{dep.name}[/cyan] {dep.version_constraint}"
                )
                add_deps(dep_skill, child)
            else:
                parent.add(f"[red]{dep.name}[/red] {dep.version_constraint} (not found)")

    add_deps(skill, dep_tree)
    console.print(dep_tree)


@cli.command()
@click.argument("name", required=False)
@click.option(
    "--format",
    "-f",
    "out_format",
    type=click.Choice(["mermaid", "tree", "json"]),
    default="mermaid",
    help="Output format",
)
@click.option("--json", "as_json", is_flag=True, help="Shortcut for --format json")
def graph(name: str | None, out_format: str, as_json: bool) -> None:
    """Visualize the skill dependency graph (whole registry or one skill)."""
    registry = get_registry()
    entries = registry.list_skills()

    if as_json:
        out_format = "json"

    nodes: list[str] = []
    edges: list[tuple[str, str]] = []
    for entry in entries:
        skill = registry.get_skill(entry["name"])
        if skill is None:
            continue
        if name and skill.metadata.name != name:
            continue
        nodes.append(skill.metadata.name)
        for dep in skill.metadata.dependencies:
            edges.append((skill.metadata.name, dep.name))

    if name and not nodes:
        console.print(f"[red]Skill not found:[/red] {name}")
        sys.exit(1)

    if not nodes:
        console.print("[yellow]No skills in registry[/yellow]")
        return

    if out_format == "json":
        emit_json(
            {
                "nodes": sorted(set(nodes)),
                "edges": [{"from": a, "to": b} for a, b in edges],
            }
        )
        return

    if out_format == "mermaid":
        console.print("graph TD")
        emitted: set[tuple[str, str]] = set()
        for a, b in edges:
            if (a, b) not in emitted:
                emitted.add((a, b))
                console.print(f"    {a} --> {b}")
        linked = {n for a, b in edges for n in (a, b)}
        for n in sorted(set(nodes)):
            if n not in linked:
                console.print(f"    {n}")
        return

    # tree format
    dep_tree = Tree("[bold]Skill Graph[/bold]")
    rendered: set[str] = set()

    def add_node(skill_name: str, parent: Tree) -> None:
        if skill_name in rendered:
            parent.add(f"{skill_name} (see above)")
            return
        rendered.add(skill_name)
        child = parent.add(f"[cyan]{skill_name}[/cyan]")
        for a, b in edges:
            if a == skill_name:
                add_node(b, child)

    roots = [n for n in nodes if not any(n == b for _, b in edges)]
    for root in roots or nodes:
        add_node(root, dep_tree)
    console.print(dep_tree)


@cli.command()
@click.argument("skill_a")
@click.argument("skill_b")
@click.option("--json", "as_json", is_flag=True, help="Output comparison as JSON")
def compare(skill_a: str, skill_b: str, as_json: bool) -> None:
    """Compare two skills side by side (metadata + quality score)."""
    from dataclasses import asdict

    from skillforge.quality.scorer import SkillScorer

    registry = get_registry()
    a = registry.get_skill(skill_a)
    b = registry.get_skill(skill_b)
    if a is None:
        console.print(f"[red]Skill not found:[/red] {skill_a}")
        sys.exit(1)
    if b is None:
        console.print(f"[red]Skill not found:[/red] {skill_b}")
        sys.exit(1)

    scorer = SkillScorer()

    def score_of(skill: Skill):  # type: ignore[no-untyped-def]
        return scorer.score(
            {
                "name": skill.metadata.name,
                "version": str(skill.metadata.version),
                "description": skill.metadata.description,
                "author": skill.metadata.author,
                "framework": skill.metadata.framework.value,
                "capability": skill.metadata.capability.value,
                "tags": skill.metadata.tags or [],
                "content": skill.content,
            }
        )

    sa = score_of(a)
    sb = score_of(b)

    if as_json:
        emit_json(
            {
                skill_a: {
                    "metadata": a.model_dump(mode="json"),
                    "score": asdict(sa),
                },
                skill_b: {
                    "metadata": b.model_dump(mode="json"),
                    "score": asdict(sb),
                },
                "winner": (
                    skill_a
                    if sa.overall > sb.overall
                    else skill_b if sb.overall > sa.overall else "tie"
                ),
            }
        )
        return

    table = Table(title=f"Compare: {skill_a} vs {skill_b}")
    table.add_column("Field", style="cyan")
    table.add_column(skill_a)
    table.add_column(skill_b)
    rows = [
        ("Version", str(a.metadata.version), str(b.metadata.version)),
        ("Description", a.metadata.description[:60], b.metadata.description[:60]),
        ("Author", a.metadata.author, b.metadata.author),
        ("Framework", a.metadata.framework.value, b.metadata.framework.value),
        ("Capability", a.metadata.capability.value, b.metadata.capability.value),
        ("Tags", ", ".join(a.metadata.tags), ", ".join(b.metadata.tags)),
        (
            "Dependencies",
            str(len(a.metadata.dependencies)),
            str(len(b.metadata.dependencies)),
        ),
        (
            "Quality score",
            f"{sa.overall:.1f} ({scorer.get_grade(sa.overall)})",
            f"{sb.overall:.1f} ({scorer.get_grade(sb.overall)})",
        ),
    ]
    for row in rows:
        table.add_row(*row)
    console.print(table)

    if sa.overall > sb.overall:
        console.print(f"\n[green]Winner:[/green] {skill_a}")
    elif sb.overall > sa.overall:
        console.print(f"\n[green]Winner:[/green] {skill_b}")
    else:
        console.print("\n[yellow]It's a tie![/yellow]")


@cli.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_command(as_json: bool) -> None:
    """List all installed skills."""
    registry = get_registry()
    skills = registry.list_skills()

    if as_json:
        emit_json(skills)
        return

    if not skills:
        console.print("[yellow]No skills in registry[/yellow]")
        return

    table = Table(title="Installed Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Author")
    table.add_column("Version")
    table.add_column("Description")

    for s in skills:
        table.add_row(
            s["name"],
            s["author"],
            s["version"],
            s["description"][:50],
        )

    console.print(table)


@cli.command()
@click.argument("names", nargs=-1, required=True)
def batch(names: tuple[str, ...]) -> None:
    """Install multiple skills at once."""
    registry = get_registry()

    console.print(f"[bold]Installing {len(names)} skills...[/bold]\n")

    success = 0
    failed = 0

    for name in names:
        skill = registry.get_skill(name)
        if skill:
            console.print(f"  [green]✓[/green] {name} v{skill.metadata.version}")
            success += 1
        else:
            console.print(f"  [red]✗[/red] {name} not found")
            failed += 1

    console.print(
        f"\n[bold]Result:[/bold] {success} installed, {failed} failed"
    )
    if failed:
        sys.exit(1)


@cli.command()
@click.argument("names", nargs=-1, required=True)
def pack(names: tuple[str, ...]) -> None:
    """Bundle multiple skills into a distributable pack."""
    import json

    registry = get_registry()
    pack_data = {"name": "skill-pack", "version": "1.0.0", "skills": []}

    for name in names:
        skill = registry.get_skill(name)
        if skill:
            pack_data["skills"].append(skill.model_dump(mode="json"))
            console.print(f"  [green]✓[/green] Added {name}")
        else:
            console.print(f"  [red]✗[/red] {name} not found")

    pack_file = Path("skill-pack.json")
    pack_file.write_text(json.dumps(pack_data, indent=2), encoding="utf-8")
    console.print(f"\n[green]Pack created:[/green] {pack_file}")
    if not pack_data["skills"]:
        sys.exit(1)


@cli.command()
@click.argument("pack_file", type=click.Path(exists=True))
def unpack(pack_file: str) -> None:
    """Unbundle a skill pack."""
    import json

    data = json.loads(Path(pack_file).read_text(encoding="utf-8"))
    registry = get_registry()

    for skill_data in data.get("skills", []):
        skill = Skill.model_validate(skill_data)
        registry.publish(skill)
        console.print(f"  [green]✓[/green] Installed {skill.metadata.name}")

    console.print(
        f"\n[green]Installed {len(data.get('skills', []))} skills from pack[/green]"
    )


@cli.command()
@click.argument("name")
@click.option(
    "--to",
    "-t",
    type=click.Choice(["claude", "cursor", "cline", "opencode"]),
    default=None,
    help="Export to format: claude, cursor, cline, opencode",
)
def convert(name: str, to: str | None) -> None:
    """Convert a skill to another framework format."""
    registry = get_registry()
    skill = registry.get_skill(name)

    if skill is None:
        console.print(f"[red]Skill not found:[/red] {name}")
        sys.exit(1)

    if to == "claude":
        output = skill.to_skill_md()
        filename = "SKILL.md"
    elif to == "cursor":
        output = _to_cursor_format(skill)
        filename = ".cursorrules"
    elif to == "cline":
        output = _to_cline_format(skill)
        filename = ".clinerules"
    elif to == "opencode":
        output = _to_opencode_format(skill)
        filename = "AGENTS.md"
    else:
        output = skill.to_skill_md()
        filename = "SKILL.md"

    Path(filename).write_text(output, encoding="utf-8")
    console.print(f"[green]Exported to {filename}[/green]")


def _to_cursor_format(skill: Skill) -> str:
    """Convert skill to Cursor format."""
    lines = [
        f"# {skill.metadata.name}",
        "",
        skill.metadata.description,
        "",
        "## Rules",
        "",
    ]
    if "instructions" in skill.content:
        lines.append(skill.content["instructions"])
    return "\n".join(lines)


def _to_cline_format(skill: Skill) -> str:
    """Convert skill to Cline format."""
    lines = [
        f"# {skill.metadata.name}",
        "",
        skill.metadata.description,
        "",
    ]
    if "instructions" in skill.content:
        lines.append(skill.content["instructions"])
    return "\n".join(lines)


def _to_opencode_format(skill: Skill) -> str:
    """Convert skill to an OpenCode AGENTS.md / agent-instructions file."""
    meta = skill.metadata
    lines = [
        f"# {meta.name}",
        "",
        meta.description,
        "",
        f"- Version: {meta.version}",
        f"- Author: {meta.author}",
        f"- Framework: {meta.framework.value}",
        f"- Capability: {meta.capability.value}",
    ]
    if meta.tags:
        lines.append(f"- Tags: {', '.join(meta.tags)}")
    if meta.dependencies:
        deps = ", ".join(f"{d.name} {d.version_constraint}" for d in meta.dependencies)
        lines.append(f"- Dependencies: {deps}")
    lines.append("")
    if "instructions" in skill.content:
        lines.append(str(skill.content["instructions"]))
    else:
        lines.append("## Instructions")
        lines.append("")
        lines.append("Add your skill instructions here.")
    return "\n".join(lines) + "\n"


@cli.group()
def templates() -> None:
    """Manage skill templates."""


@templates.command("list")
def templates_list() -> None:
    """List available skill templates."""
    from skillforge.templates.registry import get_template_details, list_templates

    names = list_templates()

    table = Table(title="Available Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Version")

    for name in names:
        details = get_template_details(name)
        if details:
            table.add_row(
                details["name"],
                details["description"][:60],
                details["version"],
            )

    console.print(table)


@templates.command("use")
@click.argument("template_name")
@click.option("--target-dir", "-d", default=".", help="Directory to create skill in")
def templates_use(template_name: str, target_dir: str) -> None:
    """Create a new skill from a template."""
    from skillforge.templates.registry import get_template

    template = get_template(template_name)
    if not template:
        console.print(f"[red]Template not found:[/red] {template_name}")
        sys.exit(1)

    out_dir = Path(target_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    skill_md = f"""# {template['name']}

{template['instructions']}
"""
    (out_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    import yaml

    skillforge_yaml = {
        "name": template["name"],
        "version": template["version"],
        "description": template["description"],
        "author": template["author"],
        "framework": template["framework"],
        "capability": template["capability"],
        "tags": ["generated", "template"],
    }
    (out_dir / "skillforge.yaml").write_text(
        yaml.dump(skillforge_yaml, default_flow_style=False), encoding="utf-8"
    )

    console.print(f"[green]Created skill from template '{template_name}' in {target_dir}/[/green]")


@templates.command("inspect")
@click.argument("template_name")
def templates_inspect(template_name: str) -> None:
    """Show full template content."""
    from skillforge.templates.registry import get_template

    template = get_template(template_name)
    if not template:
        console.print(f"[red]Template not found:[/red] {template_name}")
        sys.exit(1)

    console.print(Panel(template["instructions"], title=template_name))


@cli.command()
@click.option(
    "--all",
    "-a",
    "all_versions",
    is_flag=True,
    help="Show all available skills with versions",
)
def updates(all_versions: bool) -> None:
    """Check for skill updates."""
    registry = get_registry()
    skills = registry.list_skills()

    if not skills:
        console.print("[yellow]No skills in registry[/yellow]")
        return

    table = Table(title="Installed Skills - Version Status")
    table.add_column("Name", style="cyan")
    table.add_column("Installed")
    table.add_column("Status")

    for s in skills:
        name = s["name"]
        version = s["version"]
        skill = registry.get_skill(name)

        if skill and version != "0.1.0":
            table.add_row(name, version, "[green]Up to date[/green]")
        else:
            table.add_row(name, version, "[yellow]Check for updates[/yellow]")

    console.print(table)
    console.print(
        "\n[dim]Note: Remote registry coming soon. "
        "For now, publish skills to share with your team.[/dim]"
    )


@cli.command()
@click.argument("skill_name")
def history(skill_name: str) -> None:
    """Show version history of a skill."""
    registry = get_registry()
    skill = registry.get_skill(skill_name)

    if skill is None:
        console.print(f"[red]Skill not found:[/red] {skill_name}")
        sys.exit(1)

    console.print(
        Panel(
            f"[cyan]{skill.metadata.name}[/cyan] v{skill.metadata.version}\n"
            f"Author: {skill.metadata.author}\n"
            f"Published: Local registry",
            title="Version History",
        )
    )


@cli.command()
@click.argument("skill_name")
@click.option("--output", "-o", default="mcp-servers.json", help="Output file")
def mcp(skill_name: str, output: str) -> None:
    """Generate MCP server config for a skill."""
    import json

    registry = get_registry()
    skill = registry.get_skill(skill_name)

    if skill is None:
        console.print(f"[red]Skill not found:[/red] {skill_name}")
        sys.exit(1)

    mcp_config = {
        "name": skill.metadata.name,
        "description": skill.metadata.description,
        "type": "stdio",
        "command": "skillforge",
        "args": ["test", "."],
        "env": {"SKILL_NAME": skill.metadata.name},
    }

    Path(output).write_text(json.dumps(mcp_config, indent=2), encoding="utf-8")
    console.print(f"[green]MCP config written to {output}[/green]")


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output diagnostics as JSON")
def doctor(as_json: bool) -> None:
    """Check SkillForge installation, dependencies and registry health."""

    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, result: str) -> None:
        checks.append({"check": name, "ok": ok, "result": result})

    # Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    add("Python version", sys.version_info >= (3, 10), py_ver)

    # Dependencies
    deps = ["click", "rich", "pydantic", "yaml", "platformdirs"]
    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
            add(f"Dependency: {dep}", True, "installed")
        except ImportError:
            add(f"Dependency: {dep}", False, "missing")

    # SkillForge package
    add("SkillForge version", True, __version__)

    # Registry health
    try:
        registry = get_registry()
        count = len(registry.list_skills())
        add("Local registry", True, f"{count} skills")
        add("Registry path", registry.registry_path.exists(), str(registry.registry_path))
        writable = os.access(registry.registry_path, os.W_OK)
        add("Registry writable", writable, "writable" if writable else "read-only")
    except Exception as exc:  # noqa: BLE001 - doctor must survive any registry error
        add("Local registry", False, f"error: {exc}")

    # Built-in templates
    try:
        from skillforge.templates.registry import list_templates

        templates_count = len(list_templates())
        add("Templates available", templates_count > 0, f"{templates_count} templates")
    except Exception as exc:  # noqa: BLE001
        add("Templates available", False, f"error: {exc}")

    passed = sum(1 for c in checks if c["ok"])
    total = len(checks)
    healthy = passed == total

    if as_json:
        emit_json(
            {
                "healthy": healthy,
                "passed": passed,
                "total": total,
                "checks": checks,
            }
        )
        sys.exit(0 if healthy else 1)

    console.print("[bold]SkillForge Doctor[/bold]\n")

    table = Table(title="Diagnostic Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Result")

    for check in checks:
        status = "[green]OK[/green]" if check["ok"] else "[red]FAIL[/red]"
        table.add_row(check["check"], status, str(check["result"]))

    console.print(table)

    if healthy:
        console.print(f"\n[green]All {total} checks passed![/green]")
    else:
        console.print(
            f"\n[yellow]{passed}/{total} checks passed. "
            f"Fix the issues above.[/yellow]"
        )
        sys.exit(1)


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish", "powershell"]))
def completion(shell: str) -> None:
    """Print a shell completion script (e.g. `skillforge completion bash`)."""
    from click.shell_completion import get_completion_class

    cls = get_completion_class(shell)
    if cls is None:
        raise click.ClickException(f"Unsupported shell: {shell}")
    complete = cls(cli, {}, "skillforge", "_SKILLFORGE_COMPLETE")
    click.echo(complete.source())


@cli.command()
@click.argument("path", default=".")
@click.option("--json", "as_json", is_flag=True, help="Output score as JSON")
def score(path: str, as_json: bool) -> None:
    """Calculate quality score for a skill."""
    from skillforge.quality.scorer import SkillScorer

    loader = get_loader()
    try:
        skill = loader.load(Path(path))
    except Exception as e:
        console.print(f"[red]Failed to load skill:[/red] {e}")
        sys.exit(1)

    scorer = SkillScorer()
    data = {
        "name": skill.metadata.name,
        "version": str(skill.metadata.version),
        "description": skill.metadata.description,
        "author": skill.metadata.author,
        "framework": skill.metadata.framework.value if skill.metadata.framework else "",
        "capability": skill.metadata.capability.value if skill.metadata.capability else "",
        "tags": skill.metadata.tags or [],
        "content": skill.content,
    }

    result = scorer.score(data)
    grade = scorer.get_grade(result.overall)
    badge = scorer.get_badge(result.overall)

    if as_json:
        from dataclasses import asdict

        payload = asdict(result)
        payload.update(
            {
                "name": skill.metadata.name,
                "version": str(skill.metadata.version),
                "grade": grade,
                "badge": badge,
            }
        )
        emit_json(payload)
        return

    table = Table(title=f"Quality Score: {skill.metadata.name}")
    table.add_column("Dimension", style="cyan")
    table.add_column("Score")
    table.add_column("Grade")

    table.add_row("Overall", f"{result.overall:.1f}/100", f"{badge} {grade}")
    table.add_row("Metadata", f"{result.metadata:.1f}", scorer.get_grade(result.metadata))
    doc_grade = scorer.get_grade(result.documentation)
    table.add_row("Documentation", f"{result.documentation:.1f}", doc_grade)
    table.add_row("Structure", f"{result.structure:.1f}", scorer.get_grade(result.structure))
    comp_grade = scorer.get_grade(result.completeness)
    table.add_row("Completeness", f"{result.completeness:.1f}", comp_grade)

    console.print(table)

    if result.issues:
        console.print("\n[bold red]Issues:[/bold red]")
        for issue in result.issues:
            console.print(f"  [red]✗[/red] {issue}")

    if result.suggestions:
        console.print("\n[bold yellow]Suggestions:[/bold yellow]")
        for s in result.suggestions:
            console.print(f"  [yellow]→[/yellow] {s}")


@cli.command()
@click.argument("path", default=".")
def changelog(path: str) -> None:
    """Generate a changelog for a skill."""
    loader = get_loader()
    try:
        skill = loader.load(Path(path))
    except Exception as e:
        console.print(f"[red]Failed to load skill:[/red] {e}")
        sys.exit(1)

    lines = [
        f"# Changelog for {skill.metadata.name}",
        "",
        f"## [{skill.metadata.version}] - {__import__('datetime').date.today().isoformat()}",
        "",
        "### Added",
        "- Initial release",
        "",
        "### Features",
        f"- {skill.metadata.description}",
        "",
    ]

    if skill.metadata.tags:
        lines.append("### Tags")
        for tag in skill.metadata.tags:
            lines.append(f"- {tag}")
        lines.append("")

    output = "\n".join(lines)
    changelog_file = Path(path) / "CHANGELOG.md"
    changelog_file.write_text(output, encoding="utf-8")
    console.print(f"[green]Changelog generated:[/green] {changelog_file}")


@cli.command()
@click.argument("path", default=".")
@click.option("--output", "-o", default="SKILL.md", help="Output file")
def docs(path: str, output: str) -> None:
    """Generate documentation for a skill."""
    loader = get_loader()
    try:
        skill = loader.load(Path(path))
    except Exception as e:
        console.print(f"[red]Failed to load skill:[/red] {e}")
        sys.exit(1)

    framework = (
        skill.metadata.framework.value
        if skill.metadata.framework else "universal"
    )

    lines = [
        f"# {skill.metadata.name}",
        "",
        f"**Version:** {skill.metadata.version}",
        f"**Author:** {skill.metadata.author}",
        f"**Framework:** {framework}",
        "",
        "## Description",
        "",
        skill.metadata.description,
        "",
    ]

    if skill.metadata.tags:
        lines.append("## Tags")
        lines.append("")
        for tag in skill.metadata.tags:
            lines.append(f"- `{tag}`")
        lines.append("")

    if skill.content and "instructions" in skill.content:
        lines.append("## Instructions")
        lines.append("")
        lines.append(skill.content["instructions"])
        lines.append("")

    if skill.metadata.dependencies:
        lines.append("## Dependencies")
        lines.append("")
        for dep in skill.metadata.dependencies:
            lines.append(f"- `{dep.name}` {dep.version_constraint}")
        lines.append("")

    lines.extend([
        "## Installation",
        "",
        "```bash",
        f"skillforge install {skill.metadata.name}",
        "```",
        "",
        "## Usage",
        "",
        "```bash",
        f"skillforge info {skill.metadata.name}",
        f"skillforge test ./{skill.metadata.name}",
        "```",
        "",
    ])

    output_file = Path(path) / output
    output_file.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]Documentation generated:[/green] {output_file}")


@cli.command()
@click.argument("path", default=".")
def recommend(path: str) -> None:
    """Get skill recommendations based on current skill."""
    loader = get_loader()
    try:
        skill = loader.load(Path(path))
    except Exception as e:
        console.print(f"[red]Failed to load skill:[/red] {e}")
        sys.exit(1)

    from skillforge.templates.registry import TEMPLATES

    recommendations = []
    current_tags = set(skill.metadata.tags or [])
    current_framework = skill.metadata.framework.value if skill.metadata.framework else "universal"

    for name, template in TEMPLATES.items():
        if name == skill.metadata.name:
            continue

        score = 0
        if template.get("framework") == current_framework:
            score += 2

        if current_tags and any(t in (template.get("tags", []) or []) for t in current_tags):
            score += 1

        if score > 0:
            recommendations.append((name, template.get("description", ""), score))

    recommendations.sort(key=lambda x: x[2], reverse=True)

    if not recommendations:
        console.print("[yellow]No recommendations found[/yellow]")
        return

    table = Table(title="Recommended Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Relevance")

    for name, desc, score in recommendations[:5]:
        relevance = "*" * min(score, 3)
        table.add_row(name, desc[:50], relevance)

    console.print(table)


@cli.command()
@click.argument("path", default=".")
@click.option("--output", "-o", default=None, help="Output file")
def compress(path: str, output: str | None) -> None:
    """Compress a skill into a minimal bundle."""
    import base64
    import json

    loader = get_loader()
    try:
        skill = loader.load(Path(path))
    except Exception as e:
        console.print(f"[red]Failed to load skill:[/red] {e}")
        sys.exit(1)

    bundle = {
        "name": skill.metadata.name,
        "version": str(skill.metadata.version),
        "description": skill.metadata.description,
        "author": skill.metadata.author,
        "content": skill.content,
    }

    compressed = base64.b64encode(json.dumps(bundle).encode()).decode()

    output_file = output or f"{skill.metadata.name}.bundle"
    Path(output_file).write_text(compressed, encoding="utf-8")
    console.print(f"[green]Skill compressed:[/green] {output_file}")


@cli.command()
@click.argument("bundle_file")
@click.option("--output", "-o", default=".", help="Output directory")
def decompress(bundle_file: str, output: str) -> None:
    """Decompress a skill bundle."""
    import base64
    import json

    compressed = Path(bundle_file).read_text(encoding="utf-8")
    data = json.loads(base64.b64decode(compressed.encode()))

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    import yaml

    skillforge_yaml = {
        "name": data["name"],
        "version": data["version"],
        "description": data["description"],
        "author": data["author"],
    }
    (out_dir / "skillforge.yaml").write_text(
        yaml.dump(skillforge_yaml, default_flow_style=False), encoding="utf-8"
    )

    if data.get("content"):
        content = data["content"]
        if "instructions" in content:
            (out_dir / "SKILL.md").write_text(
                f"# {data['name']}\n\n{content['instructions']}", encoding="utf-8"
            )

    console.print(f"[green]Skill decompressed to:[/green] {output}")


@cli.command()
@click.argument("path", default=".")
def inspect(path: str) -> None:
    """Deep inspect a skill with detailed analysis."""
    loader = get_loader()
    try:
        skill = loader.load(Path(path))
    except Exception as e:
        console.print(f"[red]Failed to load skill:[/red] {e}")
        sys.exit(1)

    framework_val = skill.metadata.framework.value
    cap_val = skill.metadata.capability.value
    fw_display = framework_val if skill.metadata.framework else 'universal'
    cap_display = cap_val if skill.metadata.capability else 'tool'

    panel_content = f"""[bold cyan]{skill.metadata.name}[/bold cyan] v{skill.metadata.version}

[bold]Author:[/bold] {skill.metadata.author}
[bold]Framework:[/bold] {fw_display}
[bold]Capability:[/bold] {cap_display}
[bold]Tags:[/bold] {', '.join(skill.metadata.tags or ['none'])}
[bold]Dependencies:[/bold] {len(skill.metadata.dependencies or [])}

[bold]Fingerprint:[/bold] {skill.fingerprint[:16]}...
[bold]Full Name:[/bold] {skill.full_name}
"""

    if skill.content:
        content_size = len(str(skill.content))
        panel_content += f"\n[bold]Content Size:[/bold] {content_size} bytes"

    console.print(Panel(panel_content, title="Skill Inspector", border_style="blue"))


if __name__ == "__main__":
    cli()
