"""Main CLI entry point for SkillForge."""

from __future__ import annotations

from pathlib import Path

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
def init(path: str, name: str | None, author: str | None, framework: str) -> None:
    """Initialize a new skill project."""
    from skillforge.core.models import SkillFramework

    dir_path = Path(path)
    skill_name = name or dir_path.name

    if not author:
        author = click.prompt("Author name")

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
def validate(path: str, strict: bool) -> None:
    """Validate a skill project."""
    loader = get_loader()
    sandbox = SkillSandbox()

    try:
        skill_path = Path(path)
        if skill_path.is_dir():
            skill = loader.load_from_directory(skill_path)
        else:
            skill = loader.load_from_file(skill_path)

        result = sandbox.validate_skill(skill)

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

        if strict and result.warnings:
            console.print(
                f"\n[red]Validation failed with {len(result.warnings)} warnings[/red]"
            )
        else:
            console.print("\n[green]Validation passed![/green]")

    except SkillLoadError as e:
        console.print(f"[red]Error:[/red] {e}")


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


@cli.command()
@click.argument("name")
@click.option("--version", "-v", help="Specific version to install")
def install(name: str, version: str | None) -> None:
    """Install a skill from the registry."""
    registry = get_registry()

    skill = registry.get_skill(name, version)
    if skill is None:
        console.print(f"[red]Skill not found:[/red] {name}")
        return

    resolver = registry.get_resolver()
    resolution = resolver.resolve(skill)

    if not resolution.success:
        console.print("[red]Dependency resolution failed:[/red]")
        for conflict in resolution.conflicts:
            console.print(f"  - {conflict}")
        for missing in resolution.missing:
            console.print(f"  - Missing: {missing}")
        return

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
def info(name: str | None, version: str | None) -> None:
    """Show information about a skill."""
    registry = get_registry()

    if name:
        skill = registry.get_skill(name, version)
        if skill is None:
            console.print(f"[red]Skill not found:[/red] {name}")
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
def search(
    query: str | None,
    tags: str | None,
    capability: str | None,
    framework: str | None,
    limit: int,
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

    except SkillLoadError as e:
        console.print(f"[red]Error:[/red] {e}")
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

    for skill_name in skills:
        skill = registry.get_skill(skill_name)
        if skill:
            composition.register_skill(skill)
        else:
            console.print(f"[yellow]Warning:[/yellow] Skill {skill_name} not in registry, skipping")

    try:
        if comp_type == "chain":
            plan = composition.chain(list(skills), name=name)
        elif comp_type == "parallel":
            plan = composition.parallel(list(skills), name=name)
        else:
            plan = composition.compose(list(skills), name=name)

        analysis = composition.analyze(plan)

        output = composition.export_plan(plan, format=out_format)
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

    except CompositionError as e:
        console.print(f"[red]Composition error:[/red] {e}")


@cli.command()
def stats() -> None:
    """Show registry statistics."""
    registry = get_registry()
    stats = registry.get_stats()

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


@cli.command()
@click.argument("skill_name")
def tree(skill_name: str) -> None:
    """Show dependency tree for a skill."""
    registry = get_registry()
    skill = registry.get_skill(skill_name)

    if skill is None:
        console.print(f"[red]Skill not found:[/red] {skill_name}")
        return

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
def list_command() -> None:
    """List all installed skills."""
    registry = get_registry()
    skills = registry.list_skills()

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


if __name__ == "__main__":
    cli()
