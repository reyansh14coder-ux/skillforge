# SkillForge Architecture

This document describes the internal architecture of SkillForge in detail.

## System Overview

SkillForge is designed as a modular Python package with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│                     (CLI / Python API)                          │
├─────────────────────────────────────────────────────────────────┤
│                        Core Engine                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Models   │  │ Resolver │  │  Loader  │  │  Validator   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     Storage Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │   Registry    │  │   Sandbox    │  │  Composition Store   │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Models (`core/models.py`)

The data models define the structure of skills, versions, and dependencies.

#### SkillVersion

Semantic versioning with constraint solving:

```python
class SkillVersion:
    major: int
    minor: int
    patch: int
    
    def satisfies(self, constraint: str) -> bool:
        """Check if version satisfies a constraint like '>=1.0.0'"""
```

**Version Constraints:**
- `>=1.0.0` — Greater than or equal to
- `^1.0.0` — Compatible with (same major version)
- `~1.0.0` — Approximately equal to (same major.minor)
- `1.0.0` — Exact match

#### Skill

The main skill model:

```python
class Skill:
    metadata: SkillMetadata    # Name, version, author, etc.
    config: SkillConfig        # Runtime configuration
    content: dict[str, Any]    # Skill content/instructions
    files: dict[str, str]      # Associated files
    entry_point: str | None    # Main entry point
```

#### SkillMetadata

Describes the skill:

```python
class SkillMetadata:
    name: str                  # Unique identifier
    version: SkillVersion      # Semantic version
    description: str           # Brief description
    author: str                # Author name
    framework: SkillFramework  # Target framework
    capability: SkillCapability # What the skill does
    tags: list[str]            # Searchable tags
    dependencies: list[SkillDependency]  # Other skills needed
```

### 2. Resolver (`core/resolver.py`)

The dependency resolver uses topological sorting to determine install order and detect conflicts.

#### Algorithm

1. **Build Dependency Graph**
   ```
   skill-a → dep-1 → dep-2
   skill-b → dep-1
   ```

2. **Detect Cycles**
   ```
   If skill-a → skill-b → skill-a: CircularDependencyError
   ```

3. **Resolve Versions**
   ```
   dep-1 >=1.0.0 (from skill-a)
   dep-1 >=0.5.0 (from skill-b)
   → Use dep-1 v1.2.0 (satisfies both)
   ```

4. **Topological Sort**
   ```
   Install order: dep-2, dep-1, skill-b, skill-a
   ```

#### Resolution Result

```python
@dataclass
class ResolutionResult:
    resolved: list[ResolvedDependency]  # Successfully resolved
    conflicts: list[str]                # Version conflicts
    missing: list[str]                  # Missing dependencies
    warnings: list[str]                 # Non-fatal warnings
```

### 3. Loader (`core/loader.py`)

Loads skills from various formats:

#### Supported Formats

| Format | File | Parser |
|--------|------|--------|
| YAML | `skillforge.yaml` or `skillforge.yml` | PyYAML |
| JSON | `skillforge.json` | json |
| Markdown | `SKILL.md` or `skill.md` | Custom parser |

#### Markdown Parser

The SKILL.md parser extracts metadata from markdown:

```markdown
# Skill Name                    → name
**Author:** John                → author
**Version:** 1.0.0              → version
**Framework:** universal        → framework
**Tags:** a, b, c              → tags

## Dependencies                 → dependencies
- dep-name >=1.0.0

## Instructions                  → content.instructions
Your instructions here...
```

### 4. Registry (`registry/store.py`)

Local skill registry for storing and discovering skills.

#### Storage Structure

```
~/.local/share/skillforge/registry/
├── index.json                 # Skill index
└── skills/
    ├── author_skill-name/
    │   ├── 1.0.0/
    │   │   ├── skill.json     # Skill data
    │   │   ├── SKILL.md       # Skill markdown
    │   │   └── files/         # Associated files
    │   └── 1.1.0/
    │       └── ...
    └── ...
```

#### Index Format

```json
{
  "skills": {
    "author_skill-name": {
      "name": "skill-name",
      "author": "author",
      "versions": ["1.1.0", "1.0.0"],
      "latest": "1.1.0",
      "description": "...",
      "tags": ["tag1", "tag2"],
      "capability": "tool",
      "framework": "universal"
    }
  },
  "updated_at": "2026-09-11T12:00:00Z"
}
```

### 5. Sandbox (`sandbox/executor.py`)

Isolated execution environment for testing skills.

#### Execution Flow

1. **Prepare** — Create temporary directory with skill files
2. **Validate** — Check skill structure and metadata
3. **Test** — Execute test commands in isolation
4. **Diff** — Compare two skill versions
5. **Cleanup** — Remove temporary files

#### Security

- Skills run in isolated directories
- No access to parent directories
- Time-limited execution
- Resource limits

### 6. Composition Engine (`composition/engine.py`)

Orchestrates multiple skills into workflows.

#### Composition Types

**Chain (Sequential):**
```
skill-a → skill-b → skill-c
```

**Parallel:**
```
skill-a ─┐
skill-b ─┼→ (done)
skill-c ─┘
```

**Auto (DAG):**
```
Automatically determines order from dependencies
```

#### Composition Plan

```python
class CompositionPlan:
    name: str                      # Plan name
    description: str               # Description
    steps: list[CompositionStep]   # Execution steps
    skills_used: list[str]         # Skills involved
```

#### Analysis

The analyzer provides:
- Total steps and skills
- Critical path length
- Parallel group identification
- Potential issues detection
- Optimization suggestions

## Data Flow

### Publishing a Skill

```
User → CLI (publish) → Loader → Validator → Registry → Storage
         ↓
    Load SKILL.md/yaml
         ↓
    Validate structure
         ↓
    Store in registry
         ↓
    Update index
```

### Installing a Skill

```
User → CLI (install) → Registry → Resolver → Storage
         ↓
    Look up skill
         ↓
    Resolve dependencies
         ↓
    Determine install order
         ↓
    Store skill files
```

### Composing Skills

```
User → CLI (compose) → Composition → Resolver → Analysis
         ↓
    Load skills
         ↓
    Resolve dependencies
         ↓
    Build execution plan
         ↓
    Analyze plan
         ↓
    Export (yaml/json/mermaid)
```

## Error Handling

### Dependency Errors

```python
class DependencyError(Exception):
    """Base dependency error"""

class CircularDependencyError(DependencyError):
    """Circular dependency detected"""

class VersionConflictError(DependencyError):
    """Version constraint conflict"""

class MissingDependencyError(DependencyError):
    """Required dependency not found"""
```

### Loading Errors

```python
class SkillLoadError(Exception):
    """Skill cannot be loaded"""
```

### Composition Errors

```python
class CompositionError(Exception):
    """Composition failed"""
```

## Performance Considerations

### Caching

- Registry index is cached in memory
- Dependency resolution results are cached
- Skill files are loaded on-demand

### Optimization

- Topological sort is O(V + E)
- Version comparison is O(1)
- Search uses index-based filtering

### Scalability

- Local registry supports thousands of skills
- Remote registry (planned) will use CDN
- Composition plans are generated on-demand

## Extension Points

### Custom Loaders

Add support for new skill formats:

```python
class CustomLoader(SkillLoader):
    def load_from_custom_format(self, path: Path) -> Skill:
        # Parse custom format
        ...
```

### Custom Resolvers

Implement alternative resolution strategies:

```python
class CustomResolver(DependencyResolver):
    def resolve(self, skill: Skill) -> ResolutionResult:
        # Custom resolution logic
        ...
```

### Custom Composers

Add new composition types:

```python
class CustomComposer(SkillComposition):
    def custom_composition(self, skills: list[str]) -> CompositionPlan:
        # Custom composition logic
        ...
```

## Testing Strategy

### Unit Tests

- Model validation
- Version comparison
- Dependency resolution
- Registry operations

### Integration Tests

- CLI commands
- End-to-end workflows
- Cross-component interactions

### Test Coverage

Current: 42 tests covering:
- Core models: 10 tests
- Resolver: 7 tests
- Loader: 6 tests
- Registry: 7 tests
- Sandbox: 4 tests
- Composition: 8 tests
