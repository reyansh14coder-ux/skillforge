"""Dependency resolution engine for SkillForge."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from skillforge.core.models import Skill, SkillVersion


class DependencyError(Exception):
    """Raised when dependency resolution fails."""

    pass


class CircularDependencyError(DependencyError):
    """Raised when a circular dependency is detected."""

    pass


class VersionConflictError(DependencyError):
    """Raised when version constraints conflict."""

    pass


class MissingDependencyError(DependencyError):
    """Raised when a required dependency is not found."""

    pass


@dataclass
class ResolvedDependency:
    """A resolved dependency with its version."""

    name: str
    version: SkillVersion
    constraint: str
    optional: bool = False


@dataclass
class ResolutionResult:
    """Result of dependency resolution."""

    resolved: list[ResolvedDependency] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.conflicts) == 0 and len(self.missing) == 0

    @property
    def flat_deps(self) -> dict[str, SkillVersion]:
        """Get a flat mapping of dependency names to versions."""
        return {dep.name: dep.version for dep in self.resolved}


class DependencyResolver:
    """Resolves skill dependencies using topological sort."""

    def __init__(self, available_skills: dict[str, Skill] | None = None):
        self.available_skills: dict[str, Skill] = available_skills or {}
        self._resolved_cache: dict[str, SkillVersion] = {}

    def register_skill(self, skill: Skill) -> None:
        """Register a skill as available for resolution."""
        name = skill.metadata.name
        if name in self.available_skills:
            existing = self.available_skills[name].metadata.version
            if skill.metadata.version > existing:
                self.available_skills[name] = skill
        else:
            self.available_skills[name] = skill

    def resolve(
        self,
        skill: Skill,
        constraints: dict[str, str] | None = None,
    ) -> ResolutionResult:
        """Resolve all dependencies for a skill."""
        result = ResolutionResult()
        visited: set[str] = set()
        in_stack: set[str] = set()
        constraint_map: dict[str, str] = {}

        if constraints:
            constraint_map.update(constraints)

        for dep in skill.metadata.dependencies:
            constraint_map[dep.name] = dep.version_constraint

        for dep in skill.metadata.dependencies:
            self._resolve_recursive(
                dep.name,
                constraint_map,
                result,
                visited,
                in_stack,
            )

        return result

    def _resolve_recursive(
        self,
        name: str,
        constraints: dict[str, str],
        result: ResolutionResult,
        visited: set[str],
        in_stack: set[str],
    ) -> SkillVersion | None:
        if name in in_stack:
            cycle = " -> ".join(list(in_stack) + [name])
            raise CircularDependencyError(f"Circular dependency detected: {cycle}")

        if name in visited:
            if name in self._resolved_cache:
                return self._resolved_cache[name]
            return None

        in_stack.add(name)
        visited.add(name)

        constraint = constraints.get(name, ">=0.1.0")
        skill = self.available_skills.get(name)

        if skill is None:
            result.missing.append(f"{name} {constraint}")
            in_stack.discard(name)
            return None

        version = skill.metadata.version
        if not version.satisfies(constraint):
            result.conflicts.append(
                f"{name}: installed {version} does not satisfy {constraint}"
            )
            in_stack.discard(name)
            return None

        resolved_dep = ResolvedDependency(
            name=name,
            version=version,
            constraint=constraint,
        )
        result.resolved.append(resolved_dep)
        self._resolved_cache[name] = version

        for dep in skill.metadata.dependencies:
            dep_version = self._resolve_recursive(
                dep.name,
                constraints,
                result,
                visited,
                in_stack,
            )
            if dep_version is not None and not dep_version.satisfies(
                dep.version_constraint
            ):
                result.conflicts.append(
                    f"{dep.name}: {dep_version} does not satisfy "
                    f"required {dep.version_constraint} (from {name})"
                )

        in_stack.discard(name)
        return version

    def get_install_order(
        self,
        skills: list[Skill],
    ) -> list[Skill]:
        """Get the order in which skills should be installed (dependencies first)."""
        graph: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = defaultdict(int)
        skill_map: dict[str, Skill] = {}

        for skill in skills:
            name = skill.metadata.name
            skill_map[name] = skill
            if name not in in_degree:
                in_degree[name] = 0

            for dep in skill.metadata.dependencies:
                graph[dep.name].append(name)
                in_degree[name] += 1

        queue = [name for name, degree in in_degree.items() if degree == 0]
        order: list[str] = []

        while queue:
            queue.sort()
            node = queue.pop(0)
            order.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(skills):
            remaining = set(skill_map.keys()) - set(order)
            raise CircularDependencyError(
                f"Circular dependency among: {', '.join(remaining)}"
            )

        return [skill_map[name] for name in order if name in skill_map]

    def find_conflicts(
        self,
        skills: list[Skill],
    ) -> list[str]:
        """Find version conflicts between skills."""
        conflicts: list[str] = []
        name_versions: dict[str, list[tuple[str, SkillVersion]]] = defaultdict(list)

        for skill in skills:
            name_versions[skill.metadata.name].append(
                (skill.full_name, skill.metadata.version)
            )

        for name, versions in name_versions.items():
            if len(versions) > 1:
                version_strs = [f"{fn} ({v})" for fn, v in versions]
                conflicts.append(f"Conflict for {name}: {', '.join(version_strs)}")

        return conflicts

    def check_compatibility(
        self,
        skill_a: Skill,
        skill_b: Skill,
    ) -> tuple[bool, list[str]]:
        """Check if two skills are compatible with each other."""
        issues: list[str] = []

        for dep in skill_a.metadata.dependencies:
            if dep.name == skill_b.metadata.name:
                if not skill_b.metadata.version.satisfies(dep.version_constraint):
                    issues.append(
                        f"{skill_a.metadata.name} requires {dep.name} "
                        f"{dep.version_constraint}, but {skill_b.metadata.name} "
                        f"is {skill_b.metadata.version}"
                    )

        for dep in skill_b.metadata.dependencies:
            if dep.name == skill_a.metadata.name:
                if not skill_a.metadata.version.satisfies(dep.version_constraint):
                    issues.append(
                        f"{skill_b.metadata.name} requires {dep.name} "
                        f"{dep.version_constraint}, but {skill_a.metadata.name} "
                        f"is {skill_a.metadata.version}"
                    )

        if skill_a.metadata.framework != skill_a.metadata.framework.UNIVERSAL:
            if (
                skill_b.metadata.framework != skill_b.metadata.framework.UNIVERSAL
                and skill_a.metadata.framework != skill_b.metadata.framework
            ):
                issues.append(
                    f"Framework mismatch: {skill_a.metadata.framework.value} "
                    f"vs {skill_b.metadata.framework.value}"
                )

        return len(issues) == 0, issues
