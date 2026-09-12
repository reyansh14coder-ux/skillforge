"""Skill composition engine for chaining skills together."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from skillforge.core.models import (
    CompositionPlan,
    CompositionStep,
    Skill,
)
from skillforge.core.resolver import DependencyResolver, ResolutionResult


class CompositionError(Exception):
    """Raised when composition fails."""

    pass


class SkillComposition:
    """Engine for composing multiple skills into workflows."""

    def __init__(self, resolver: DependencyResolver | None = None):
        self.resolver = resolver or DependencyResolver()
        self._skill_registry: dict[str, Skill] = {}

    def register_skill(self, skill: Skill) -> None:
        """Register a skill for composition."""
        self._skill_registry[skill.metadata.name] = skill
        self.resolver.register_skill(skill)

    def compose(
        self,
        skills: list[str],
        name: str = "composed-workflow",
        description: str = "",
    ) -> CompositionPlan:
        """Create a composition plan from a list of skill names."""
        resolved_skills: list[Skill] = []
        for skill_name in skills:
            skill = self._skill_registry.get(skill_name)
            if skill is None:
                raise CompositionError(f"Skill not found: {skill_name}")
            resolved_skills.append(skill)

        resolution = self._resolve_all(resolved_skills)
        if not resolution.success:
            raise CompositionError(
                f"Dependency resolution failed: {resolution.conflicts + resolution.missing}"
            )

        install_order = self.resolver.get_install_order(resolved_skills)

        steps: list[CompositionStep] = []
        installed: list[str] = []

        for skill in install_order:
            deps = [d for d in installed if d in [dep.name for dep in skill.metadata.dependencies]]

            step = CompositionStep(
                skill_name=skill.metadata.name,
                skill_version=skill.metadata.version,
                action="install",
                params={
                    "description": skill.metadata.description,
                    "capability": skill.metadata.capability.value,
                },
                depends_on=deps,
            )
            steps.append(step)
            installed.append(skill.metadata.name)

        for skill in resolved_skills:
            step = CompositionStep(
                skill_name=skill.metadata.name,
                skill_version=skill.metadata.version,
                action="activate",
                params={"framework": skill.metadata.framework.value},
                depends_on=[skill.metadata.name],
            )
            steps.append(step)

        return CompositionPlan(
            name=name,
            description=description or f"Composition of {len(skills)} skills",
            steps=steps,
            skills_used=[s.metadata.name for s in resolved_skills],
        )

    def chain(
        self,
        skills: list[str],
        name: str = "chained-workflow",
        description: str = "",
    ) -> CompositionPlan:
        """Create a sequential chain of skills where each depends on the previous."""
        steps: list[CompositionStep] = []
        skill_names: list[str] = []
        prev_name: str | None = None

        for skill_name in skills:
            skill = self._skill_registry.get(skill_name)
            if skill is None:
                raise CompositionError(f"Skill not found: {skill_name}")

            deps = [prev_name] if prev_name else []

            step = CompositionStep(
                skill_name=skill.metadata.name,
                skill_version=skill.metadata.version,
                action="execute",
                params={
                    "description": skill.metadata.description,
                    "capability": skill.metadata.capability.value,
                },
                depends_on=deps,
            )
            steps.append(step)
            skill_names.append(skill.metadata.name)
            prev_name = skill.metadata.name

        return CompositionPlan(
            name=name,
            description=description or f"Chained execution of {len(skills)} skills",
            steps=steps,
            skills_used=skill_names,
        )

    def parallel(
        self,
        skills: list[str],
        name: str = "parallel-workflow",
        description: str = "",
    ) -> CompositionPlan:
        """Create a parallel composition where all skills run independently."""
        steps: list[CompositionStep] = []
        skill_names: list[str] = []

        for skill_name in skills:
            skill = self._skill_registry.get(skill_name)
            if skill is None:
                raise CompositionError(f"Skill not found: {skill_name}")

            step = CompositionStep(
                skill_name=skill.metadata.name,
                skill_version=skill.metadata.version,
                action="execute",
                params={
                    "description": skill.metadata.description,
                    "capability": skill.metadata.capability.value,
                    "parallel": True,
                },
                depends_on=[],
            )
            steps.append(step)
            skill_names.append(skill.metadata.name)

        return CompositionPlan(
            name=name,
            description=description or f"Parallel execution of {len(skills)} skills",
            steps=steps,
            skills_used=skill_names,
        )

    def analyze(self, plan: CompositionPlan) -> dict[str, Any]:
        """Analyze a composition plan for issues and optimizations."""
        analysis: dict[str, Any] = {
            "total_steps": len(plan.steps),
            "total_skills": len(plan.skills_used),
            "critical_path": [],
            "parallel_groups": [],
            "potential_issues": [],
            "optimizations": [],
        }

        graph: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = defaultdict(int)

        for step in plan.steps:
            in_degree[step.skill_name] = len(step.depends_on)
            for dep in step.depends_on:
                graph[dep].append(step.skill_name)

        queue = [name for name, degree in in_degree.items() if degree == 0]
        levels: list[list[str]] = []

        while queue:
            level = list(queue)
            levels.append(level)
            next_queue: list[str] = []
            for node in level:
                for neighbor in graph[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_queue.append(neighbor)
            queue = next_queue

        analysis["parallel_groups"] = levels
        analysis["critical_path_length"] = len(levels)

        for step in plan.steps:
            if step.timeout < 60:
                analysis["potential_issues"].append(
                    f"Low timeout ({step.timeout}s) for {step.skill_name}"
                )

        for i, step_a in enumerate(plan.steps):
            for step_b in plan.steps[i + 1 :]:
                if step_a.skill_name in step_b.depends_on:
                    continue
                if step_b.skill_name in step_a.depends_on:
                    continue

                skill_a = self._skill_registry.get(step_a.skill_name)
                skill_b = self._skill_registry.get(step_b.skill_name)

                if skill_a and skill_b:
                    compatible, issues = self.resolver.check_compatibility(
                        skill_a, skill_b
                    )
                    if not compatible:
                        analysis["potential_issues"].extend(issues)

        return analysis

    def export_plan(self, plan: CompositionPlan, output_format: str = "yaml") -> str:
        """Export a composition plan to a string."""
        if output_format == "yaml":
            import yaml

            plan_dict = {
                "name": plan.name,
                "description": plan.description,
                "skills_used": plan.skills_used,
                "steps": [
                    {
                        "skill": step.skill_name,
                        "version": str(step.skill_version),
                        "action": step.action,
                        "depends_on": step.depends_on,
                        "params": step.params,
                    }
                    for step in plan.steps
                ],
            }
            return yaml.dump(plan_dict, default_flow_style=False)

        elif output_format == "json":
            import json

            plan_dict = {
                "name": plan.name,
                "description": plan.description,
                "skills_used": plan.skills_used,
                "steps": [
                    {
                        "skill": step.skill_name,
                        "version": str(step.skill_version),
                        "action": step.action,
                        "depends_on": step.depends_on,
                        "params": step.params,
                    }
                    for step in plan.steps
                ],
            }
            return json.dumps(plan_dict, indent=2)

        elif output_format == "mermaid":
            lines = ["graph TD"]
            for step in plan.steps:
                label = f"{step.skill_name}\\n{step.action}"
                lines.append(f"    {step.skill_name}_{step.action} [{label}]")
                for dep in step.depends_on:
                    dep_action = "install"
                    for s in plan.steps:
                        if s.skill_name == dep:
                            dep_action = s.action
                            break
                    lines.append(
                        f"    {dep}_{dep_action} --> {step.skill_name}_{step.action}"
                    )
            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _resolve_all(self, skills: list[Skill]) -> ResolutionResult:
        """Resolve dependencies for all skills."""
        combined_result = ResolutionResult()
        seen: set[str] = set()

        for skill in skills:
            if skill.metadata.name not in seen:
                result = self.resolver.resolve(skill)
                combined_result.resolved.extend(result.resolved)
                combined_result.conflicts.extend(result.conflicts)
                combined_result.missing.extend(result.missing)
                combined_result.warnings.extend(result.warnings)
                seen.add(skill.metadata.name)

        return combined_result
