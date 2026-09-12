"""Skill quality scoring and analytics system."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QualityScore:
    """Quality score breakdown for a skill."""

    overall: float = 0.0
    documentation: float = 0.0
    metadata: float = 0.0
    testing: float = 0.0
    structure: float = 0.0
    completeness: float = 0.0
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class SkillScorer:
    """Evaluates skill quality across multiple dimensions."""

    def score(self, skill_data: dict) -> QualityScore:
        """Calculate comprehensive quality score for a skill."""
        score = QualityScore()

        self._score_metadata(skill_data, score)
        self._score_documentation(skill_data, score)
        self._score_structure(skill_data, score)
        self._score_completeness(skill_data, score)

        weights = {"metadata": 0.25, "documentation": 0.30, "structure": 0.20, "completeness": 0.25}
        score.overall = (
            score.metadata * weights["metadata"]
            + score.documentation * weights["documentation"]
            + score.structure * weights["structure"]
            + score.completeness * weights["completeness"]
        )

        return score

    def _score_metadata(self, data: dict, score: QualityScore) -> None:
        points = 0
        max_points = 100

        name = data.get("name", "")
        if name:
            points += 15
        else:
            score.issues.append("Missing skill name")

        desc = data.get("description", "")
        if desc:
            points += 10
            if len(desc) >= 20:
                points += 5
            else:
                score.suggestions.append("Description is too short (aim for 20+ characters)")
        else:
            score.issues.append("Missing description")

        version = data.get("version", "")
        if version:
            points += 10
            parts = version.split(".")
            if len(parts) == 3:
                points += 5
            else:
                score.suggestions.append("Use semantic versioning (MAJOR.MINOR.PATCH)")

        author = data.get("author", "")
        if author:
            points += 10
        else:
            score.issues.append("Missing author")

        framework = data.get("framework", "")
        if framework:
            points += 5

        capability = data.get("capability", "")
        if capability:
            points += 5

        tags = data.get("tags", [])
        if tags:
            points += 10
            if len(tags) >= 3:
                points += 5
        else:
            score.suggestions.append("Add tags for better discoverability")

        deps = data.get("dependencies", [])
        if deps:
            points += 5

        homepage = data.get("homepage", "")
        if homepage:
            points += 5

        repo = data.get("repository", "")
        if repo:
            points += 5

        score.metadata = min(points / max_points * 100, 100)

    def _score_documentation(self, data: dict, score: QualityScore) -> None:
        points = 0
        max_points = 100

        content = data.get("content", {})
        instructions = content.get("instructions", "")

        if instructions:
            points += 30

            lines = instructions.strip().split("\n")
            if len(lines) >= 5:
                points += 10
            elif len(lines) >= 3:
                points += 5

            if any(line.startswith("#") for line in lines):
                points += 10

            if any(kw in instructions.lower() for kw in ["step", "example", "usage"]):
                points += 10

            if len(instructions) >= 100:
                points += 10
            elif len(instructions) >= 50:
                points += 5
        else:
            score.issues.append("No instructions provided")

        content = data.get("content", {})
        examples = content.get("examples", []) if isinstance(content, dict) else []
        if examples:
            points += 10
        else:
            score.suggestions.append("Add examples for better documentation")

        readme = data.get("readme", "")
        if readme:
            points += 10

        score.documentation = min(points / max_points * 100, 100)

    def _score_structure(self, data: dict, score: QualityScore) -> None:
        points = 0
        max_points = 100

        if data.get("name"):
            points += 20

        if data.get("version"):
            points += 20

        if data.get("description"):
            points += 20

        if data.get("author"):
            points += 20

        if data.get("content"):
            points += 20

        score.structure = min(points / max_points * 100, 100)

    def _score_completeness(self, data: dict, score: QualityScore) -> None:
        points = 0
        max_points = 100

        fields = [
            "name", "version", "description", "author",
            "framework", "capability", "tags", "content"
        ]
        present = sum(1 for f in fields if data.get(f))
        points += (present / len(fields)) * 50

        if data.get("dependencies"):
            points += 10

        if data.get("homepage"):
            points += 10

        if data.get("repository"):
            points += 10

        if data.get("license"):
            points += 10

        if data.get("changelog"):
            points += 10

        score.completeness = min(points / max_points * 100, 100)

    def get_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"

    def get_badge(self, score: float) -> str:
        """Get badge text for score."""
        if score >= 90:
            return "[GOLD]"
        elif score >= 80:
            return "[SILVER]"
        elif score >= 70:
            return "[BRONZE]"
        elif score >= 60:
            return "[PASS]"
        else:
            return "[NEW]"
