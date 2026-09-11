# SkillForge

**The Universal AI Agent Skill Registry & Composition Engine**

[![CI](https://github.com/reyansh14coder-ux/skillforge/actions/workflows/ci.yml/badge.svg)](https://github.com/reyansh14coder-ux/skillforge/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-42%20passing-brightgreen.svg)](https://github.com/reyansh14coder-ux/skillforge)

---

## Table of Contents

- [What is SkillForge?](#what-is-skillforge)
- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [CLI Reference](#cli-reference)
- [Skill Format Specification](#skill-format-specification)
- [Examples](#examples)
- [Composition Engine](#composition-engine)
- [Dependency Resolution](#dependency-resolution)
- [Sandbox Testing](#sandbox-testing)
- [Python API](#python-api)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)

---

## What is SkillForge?

The AI agent ecosystem in 2026 has exploded with **skills** — reusable capabilities for Claude Code, Codex, Cursor, Cline, OpenCode, and more. Every developer is building them, sharing them on GitHub, and composing them into workflows.

**But there's no infrastructure.**

There's no npm for AI agent skills. No pip. No cargo. No standard way to:
- Publish a skill and make it discoverable
- Install a skill with its dependencies
- Version skills and handle compatibility
- Chain skills into automated workflows
- Test skills before deploying them

**SkillForge fills this gap.** It's the missing package manager for the AI agent skill ecosystem.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          SkillForge                                 │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │   Registry   │  │   Resolver  │  │   Sandbox   │  │  Compose  │ │
│  │              │  │             │  │             │  │           │ │
│  │  Publish     │  │  Auto-dep   │  │  Validate   │  │  Chain    │ │
│  │  Search      │  │  Versioning │  │  Test       │  │  Parallel │ │
│  │  Discover    │  │  Conflicts  │  │  Diff       │  │  DAG      │ │
│  │  Version     │  │  Topo-sort  │  │  Isolate    │  │  Export   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                     Universal CLI                              │ │
│  │  init · validate · publish · install · search · info          │ │
│  │  delete · test · compose · tree · export · stats · list       │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Problem

### The Skill Explosion

In 2026, AI coding agents have become the primary way developers write code. These agents use **skills** — self-contained capability modules that extend what the agent can do. Skills handle everything from code review to security scanning, documentation generation to deployment automation.

### What's Missing

The current state of AI agent skills is like npm in 2008 — everyone's building packages, but there's no infrastructure:

| Problem | Impact |
|---------|--------|
| **No standard format** | Each framework (Claude Code, Codex, Cursor) has its own skill format |
| **No registry** | Skills live in scattered GitHub repos with no discovery mechanism |
| **No dependency management** | Skills that depend on other skills have no way to declare or resolve dependencies |
| **No versioning** | No semantic versioning, no compatibility checks, no upgrade paths |
| **No testing** | No way to validate skills work before deploying them |
| **No composition** | Chaining skills together is manual and error-prone |

### The Cost

Developers waste hours:
- Searching GitHub for the right skill
- Manually resolving version conflicts
- Debugging skills that depend on other skills
- Writing boilerplate to chain skills together
- Testing skills in production (dangerous!)

---

## The Solution

SkillForge provides the infrastructure layer that the AI agent skill ecosystem needs:

### 1. Universal Registry
```bash
# Publish your skill to the world
skillforge publish .

# Someone else finds and installs it
skillforge search "code review"
skillforge install author/code-review-skill
```

### 2. Automatic Dependency Resolution
```yaml
# Your skill declares dependencies
metadata:
  name: advanced-review
  dependencies:
    - name: base-review
      version_constraint: ">=1.0.0"
    - name: security-scan
      version_constraint: ">=0.5.0"
```

SkillForge automatically:
- Resolves all dependencies
- Detects version conflicts
- Finds circular dependencies
- Determines install order

### 3. Sandbox Testing
```bash
# Test a skill in isolation before deploying
skillforge test ./my-skill

# Validate without running
skillforge validate ./my-skill --strict
```

### 4. Skill Composition
```bash
# Chain skills into a workflow
skillforge compose code-review security-scan auto-format --type chain

# Run skills in parallel
skillforge compose lint test build --type parallel

# Export the composition plan
skillforge compose skill-a skill-b --format yaml > workflow.yaml
```

### 5. Multi-Framework Support
SkillForge works with:
- **Claude Code** — Anthropic's AI coding assistant
- **Codex** — OpenAI's code generation
- **Cursor** — AI-powered code editor
- **Cline** — VS Code AI extension
- **OpenCode** — Open-source coding agent
- **Universal** — Framework-agnostic skills

---

## Architecture

### High-Level Architecture

```
                    ┌─────────────────────────┐
                    │        CLI Layer         │
                    │   (skillforge command)   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     Core Engine          │
                    │  ┌──────────────────┐   │
                    │  │    Models         │   │
                    │  │  Skill, Version,  │   │
                    │  │  Dependency       │   │
                    │  └──────────────────┘   │
                    │  ┌──────────────────┐   │
                    │  │    Resolver       │   │
                    │  │  Topological Sort │   │
                    │  │  Version Check    │   │
                    │  └──────────────────┘   │
                    │  ┌──────────────────┐   │
                    │  │    Loader         │   │
                    │  │  YAML/JSON/MD     │   │
                    │  └──────────────────┘   │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
    ┌─────────▼─────────┐ ┌─────▼─────┐ ┌─────────▼─────────┐
    │     Registry       │ │  Sandbox  │ │   Composition     │
    │                    │ │           │ │                   │
    │  Local storage     │ │  Isolate  │ │  Chain            │
    │  Search/Index      │ │  Test     │ │  Parallel         │
    │  Version mgmt      │ │  Validate │ │  DAG              │
    │  Stats             │ │  Diff     │ │  Export           │
    └────────────────────┘ └───────────┘ └───────────────────┘
```

### Project Structure

```
skillforge/
├── skillforge/                    # Main package
│   ├── __init__.py               # Package metadata
│   ├── core/                     # Core engine
│   │   ├── __init__.py
│   │   ├── models.py             # Data models
│   │   │   ├── Skill             # Main skill model
│   │   │   ├── SkillMetadata     # Skill metadata
│   │   │   ├── SkillVersion      # Semantic version
│   │   │   ├── SkillDependency   # Dependency declaration
│   │   │   ├── SkillConfig       # Runtime config
│   │   │   ├── SkillCapability   # Capability enum
│   │   │   ├── SkillFramework    # Framework enum
│   │   │   ├── InstalledSkill    # Installed skill tracking
│   │   │   ├── CompositionPlan   # Composition plan
│   │   │   └── CompositionStep   # Single composition step
│   │   ├── resolver.py           # Dependency resolver
│   │   │   ├── DependencyResolver
│   │   │   ├── ResolutionResult
│   │   │   ├── ResolvedDependency
│   │   │   └── Exceptions
│   │   └── loader.py             # Multi-format loader
│   │       ├── SkillLoader
│   │       └── SkillLoadError
│   ├── registry/                 # Skill registry
│   │   ├── __init__.py
│   │   └── store.py              # Local registry
│   │       ├── SkillRegistry
│   │       ├── publish()
│   │       ├── get_skill()
│   │       ├── search()
│   │       ├── delete_skill()
│   │       └── get_stats()
│   ├── sandbox/                  # Sandbox execution
│   │   ├── __init__.py
│   │   └── executor.py           # Isolated execution
│   │       ├── SkillSandbox
│   │       ├── SandboxResult
│   │       ├── prepare()
│   │       ├── validate_skill()
│   │       ├── test_skill()
│   │       └── diff()
│   ├── composition/              # Composition engine
│   │   ├── __init__.py
│   │   └── engine.py             # Skill composition
│   │       ├── SkillComposition
│   │       ├── CompositionError
│   │       ├── compose()
│   │       ├── chain()
│   │       ├── parallel()
│   │       ├── analyze()
│   │       └── export_plan()
│   ├── cli/                      # Command-line interface
│   │   ├── __init__.py
│   │   └── main.py               # CLI commands
│   │       ├── init
│   │       ├── validate
│   │       ├── publish
│   │       ├── install
│   │       ├── search
│   │       ├── info
│   │       ├── delete
│   │       ├── test
│   │       ├── compose
│   │       ├── tree
│   │       ├── export
│   │       ├── stats
│   │       └── list
│   └── utils/                    # Utilities
│       ├── __init__.py
│       └── helpers.py
├── tests/                        # Test suite
│   └── test_skillforge.py        # 42 tests
├── examples/                     # Example skills
│   ├── code-review/
│   ├── security-scan/
│   ├── auto-format/
│   └── docs-generator/
├── .github/workflows/            # CI/CD
│   └── ci.yml
├── pyproject.toml                # Project config
├── README.md                     # This file
├── CONTRIBUTING.md               # Contributing guide
├── LICENSE                       # MIT License
└── .gitignore
```

---

## Quick Start

### Installation

```bash
pip install skillforge
```

### Your First Skill

#### Step 1: Initialize

```bash
mkdir my-first-skill
cd my-first-skill
skillforge init --name "greeting" --author "your-name"
```

This creates:
```
my-first-skill/
├── skillforge.yaml    # Skill configuration
└── SKILL.md           # Skill instructions
```

#### Step 2: Edit the Skill

Edit `SKILL.md`:

```markdown
# Greeting Skill

A simple skill that generates friendly greetings.

**Author:** your-name
**Version:** 1.0.0
**Framework:** universal
**Capability:** tool
**Tags:** greeting, hello, utility

## Instructions

When the user asks for a greeting, respond with a friendly message.
Include the current time of day in your greeting (morning, afternoon, evening).
```

#### Step 3: Validate

```bash
skillforge validate .
```

Output:
```
Validation: greeting
+----------+--------+-----------+
| Check    | Status | Details   |
|----------+--------+-----------+
| Name     | OK     | greeting  |
| Version  | OK     | 1.0.0     |
| Author   | OK     | your-name |
+----------+--------+-----------+

Validation passed!
```

#### Step 4: Publish

```bash
skillforge publish .
```

Output:
```
Published!
  Skill: greeting
  Version: 1.0.0
  ID: your-name_greeting@1.0.0
```

#### Step 5: Search & Install

```bash
# Search for skills
skillforge search "greeting"

# Install a skill
skillforge install your-name/greeting

# View skill info
skillforge info greeting
```

---

## Installation

### From PyPI

```bash
pip install skillforge
```

### From Source

```bash
git clone https://github.com/reyansh14coder-ux/skillforge.git
cd skillforge
pip install -e ".[dev]"
```

### Requirements

- Python 3.10 or higher
- Dependencies are automatically installed:
  - click (CLI framework)
  - rich (terminal formatting)
  - pydantic (data validation)
  - pyyaml (YAML parsing)
  - httpx (HTTP client)
  - platformdirs (platform-specific directories)

---

## CLI Reference

### `skillforge init`

Initialize a new skill project.

```bash
skillforge init [PATH] [OPTIONS]

Options:
  --name, -n TEXT        Skill name
  --author, -a TEXT      Author name
  --framework, -f TEXT   Target framework (default: universal)
  --help                 Show this message and exit
```

**Examples:**
```bash
skillforge init --name "my-skill" --author "john"
skillforge init ./my-skill --framework claude-code
```

### `skillforge validate`

Validate a skill project.

```bash
skillforge validate [PATH] [OPTIONS]

Options:
  --strict    Enable strict validation (warnings become errors)
  --help      Show this message and exit
```

**Examples:**
```bash
skillforge validate .
skillforge validate ./my-skill --strict
```

### `skillforge publish`

Publish a skill to the local registry.

```bash
skillforge publish [PATH] [OPTIONS]

Options:
  --version, -v TEXT    Specific version to publish
  --help                Show this message and exit
```

**Examples:**
```bash
skillforge publish .
skillforge publish . --version 2.0.0
```

### `skillforge install`

Install a skill from the registry.

```bash
skillforge install [NAME] [OPTIONS]

Options:
  --version, -v TEXT    Specific version to install
  --help                Show this message and exit
```

**Examples:**
```bash
skillforge install code-review
skillforge install code-review --version 1.2.0
```

### `skillforge search`

Search for skills in the registry.

```bash
skillforge search [QUERY] [OPTIONS]

Options:
  --tags, -t TEXT           Filter by tags (comma-separated)
  --capability, -c TEXT     Filter by capability
  --framework, -f TEXT      Filter by framework
  --limit, -l INTEGER       Max results (default: 20)
  --help                    Show this message and exit
```

**Examples:**
```bash
skillforge search "code review"
skillforge search --tags "security,scanning"
skillforge search --capability tool --framework claude-code
```

### `skillforge info`

Show information about a skill.

```bash
skillforge info [NAME] [OPTIONS]

Options:
  --version, -v TEXT    Specific version
  --help                Show this message and exit
```

**Examples:**
```bash
skillforge info code-review
skillforge info code-review --version 1.2.0
```

### `skillforge delete`

Delete a skill from the registry.

```bash
skillforge delete [NAME] [OPTIONS]

Options:
  --version, -v TEXT    Version to delete
  --all                 Delete all versions
  --help                Show this message and exit
```

**Examples:**
```bash
skillforge delete code-review --version 1.0.0
skillforge delete code-review --all
```

### `skillforge test`

Test a skill in a sandbox.

```bash
skillforge test [PATH] [OPTIONS]

Options:
  --timeout, -t INTEGER    Test timeout in seconds (default: 60)
  --command, -c TEXT       Custom test command
  --help                   Show this message and exit
```

**Examples:**
```bash
skillforge test .
skillforge test ./my-skill --timeout 120
skillforge test ./my-skill --command "python test.py"
```

### `skillforge compose`

Compose multiple skills into a workflow.

```bash
skillforge compose [SKILLS]... [OPTIONS]

Options:
  --name, -n TEXT     Composition name (default: composed-workflow)
  --type TEXT          Composition type: auto, chain, parallel (default: auto)
  --format, -f TEXT    Output format: yaml, json, mermaid (default: yaml)
  --help               Show this message and exit
```

**Examples:**
```bash
skillforge compose skill-a skill-b --type chain
skillforge compose skill-a skill-b skill-c --type parallel
skillforge compose skill-a skill-b --format mermaid
```

### `skillforge tree`

Show dependency tree for a skill.

```bash
skillforge tree [SKILL_NAME]

Options:
  --help    Show this message and exit
```

**Examples:**
```bash
skillforge tree code-review
```

### `skillforge export`

Export a skill as a distributable package.

```bash
skillforge export [PATH] [OPTIONS]

Options:
  --output, -o TEXT    Export directory (default: skillforge-export)
  --help               Show this message and exit
```

**Examples:**
```bash
skillforge export .
skillforge export ./my-skill --output ./dist
```

### `skillforge stats`

Show registry statistics.

```bash
skillforge stats

Options:
  --help    Show this message and exit
```

### `skillforge list`

List all installed skills.

```bash
skillforge list

Options:
  --help    Show this message and exit
```

---

## Skill Format Specification

### SKILL.md Format

Skills can be defined in `SKILL.md` (compatible with Claude Code):

```markdown
# Skill Name

A description of what the skill does.

**Author:** author-name
**Version:** 1.0.0
**Framework:** universal
**Capability:** tool
**Tags:** tag1, tag2, tag3

## Dependencies

- dependency-name >=1.0.0

## Environment Variables

- `VAR_NAME`: Description of the variable

## Instructions

Your skill instructions go here...
```

### skillforge.yaml Format

Skills can also be defined in `skillforge.yaml`:

```yaml
metadata:
  name: skill-name
  version: 1.0.0
  description: "A description of the skill"
  author: author-name
  framework: universal
  capability: tool
  tags:
    - tag1
    - tag2
  dependencies:
    - name: dependency-name
      version_constraint: ">=1.0.0"
  homepage: "https://example.com"
  repository: "https://github.com/example/skill"

config:
  env_vars:
    API_KEY: "Required API key for the service"
    DEBUG: "Enable debug mode (default: false)"
  requires_permissions:
    - filesystem
    - network
  max_execution_time_seconds: 300
  sandbox_required: false

content:
  instructions: |
    Your skill instructions go here...
    You can use multi-line strings.
```

### Skill Fields Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique skill name |
| `version` | string | Yes | Semantic version (MAJOR.MINOR.PATCH) |
| `description` | string | Yes | Brief description (10-500 chars) |
| `author` | string | Yes | Skill author name |
| `framework` | enum | No | Target framework (default: universal) |
| `capability` | enum | No | Skill capability type (default: tool) |
| `tags` | list | No | Searchable tags |
| `dependencies` | list | No | Other skills this depends on |
| `homepage` | string | No | Project homepage URL |
| `repository` | string | No | Source code repository URL |

### Capability Types

| Capability | Description |
|------------|-------------|
| `tool` | Standalone tool that performs a specific task |
| `workflow` | Multi-step workflow that orchestrates other tools |
| `agent` | Autonomous agent that can make decisions |
| `hook` | Event-driven hook that runs on specific triggers |
| `rule` | Validation rule that checks code quality |
| `prompt` | Reusable prompt template |
| `dataset` | Training or reference dataset |

### Framework Values

| Framework | Description |
|-----------|-------------|
| `universal` | Works with any framework |
| `claude-code` | Optimized for Claude Code |
| `codex` | Optimized for OpenAI Codex |
| `cursor` | Optimized for Cursor |
| `cline` | Optimized for Cline |
| `opencode` | Optimized for OpenCode |

---

## Examples

### Example 1: Code Review Skill

```yaml
# skillforge.yaml
metadata:
  name: code-review
  version: 1.2.0
  description: "AI-powered code review with bug detection and security analysis"
  author: skillforge-examples
  framework: universal
  capability: tool
  tags:
    - code-review
    - quality
    - security
  dependencies:
    - name: security-scan
      version_constraint: ">=0.5.0"

config:
  env_vars:
    REVIEW_DEPTH: "Review depth: quick, standard, or deep"
  requires_permissions:
    - filesystem
  max_execution_time_seconds: 600

content:
  instructions: |
    Review code for:
    1. Bugs and logic errors
    2. Security vulnerabilities
    3. Performance issues
    4. Style violations
```

### Example 2: Security Scanner

```yaml
# skillforge.yaml
metadata:
  name: security-scan
  version: 0.8.0
  description: "Comprehensive security vulnerability scanner"
  author: skillforge-examples
  framework: universal
  capability: tool
  tags:
    - security
    - vulnerability
    - scanning

config:
  env_vars:
    SCAN_TARGETS: "Comma-separated scan targets"
    FAIL_ON: "Severity level to fail on"
  requires_permissions:
    - filesystem
    - network

content:
  instructions: |
    Scan for:
    1. Dependency CVEs
    2. Hardcoded secrets
    3. Code vulnerabilities
    4. Configuration issues
```

### Example 3: Workflow Composition

```bash
# Create a complete CI/CD pipeline
skillforge compose \
  code-review \
  security-scan \
  auto-format \
  docs-generator \
  --type chain \
  --name "ci-pipeline" \
  --format yaml > .skillforge/workflow.yaml
```

Output:
```yaml
name: ci-pipeline
description: Chained execution of 4 skills
skills_used:
  - code-review
  - security-scan
  - auto-format
  - docs-generator
steps:
  - skill: code-review
    action: execute
    depends_on: []
  - skill: security-scan
    action: execute
    depends_on:
      - code-review
  - skill: auto-format
    action: execute
    depends_on:
      - security-scan
  - skill: docs-generator
    action: execute
    depends_on:
      - auto-format
```

---

## Composition Engine

### Composition Types

#### Chain (Sequential)
Skills execute one after another, each waiting for the previous to complete.

```bash
skillforge compose skill-a skill-b skill-c --type chain
```

```
skill-a → skill-b → skill-c
```

#### Parallel
All skills execute simultaneously.

```bash
skillforge compose skill-a skill-b skill-c --type parallel
```

```
skill-a ─┐
skill-b ─┼→ (done)
skill-c ─┘
```

#### Auto (DAG)
Automatically determines execution order based on dependencies.

```bash
skillforge compose skill-a skill-b skill-c --type auto
```

### Composition Analysis

The composition engine provides detailed analysis:

```bash
skillforge compose skill-a skill-b --format yaml
```

```yaml
# Composition plan
name: composed-workflow
skills_used:
  - skill-a
  - skill-b
steps:
  - skill: skill-a
    action: execute
    depends_on: []
  - skill: skill-b
    action: execute
    depends_on:
      - skill-a
```

```
# Analysis
Composition Analysis
  Total steps: 2
  Total skills: 2
  Critical path length: 2
  Parallel groups: 2
```

### Export Formats

#### YAML
```bash
skillforge compose skill-a skill-b --format yaml
```

#### JSON
```bash
skillforge compose skill-a skill-b --format json
```

#### Mermaid Diagram
```bash
skillforge compose skill-a skill-b --format mermaid
```

Output:
```mermaid
graph TD
    skill-a_execute [skill-a\nexecute]
    skill-b_execute [skill-b\nexecute]
    skill-a_execute --> skill-b_execute
```

---

## Dependency Resolution

### How It Works

SkillForge uses **topological sorting** with **semantic version constraints**:

1. **Parse Dependencies** — Read all dependency declarations
2. **Build Graph** — Create dependency graph
3. **Detect Cycles** — Check for circular dependencies
4. **Resolve Versions** — Find compatible versions
5. **Determine Order** — Topological sort for install order

### Version Constraints

| Constraint | Meaning | Example |
|------------|---------|---------|
| `>=1.0.0` | Version 1.0.0 or higher | `>=1.0.0` |
| `^1.0.0` | Compatible with 1.0.0 (same major) | `^1.0.0` |
| `~1.0.0` | Compatible with 1.0.0 (same major.minor) | `~1.0.0` |
| `1.0.0` | Exactly version 1.0.0 | `1.0.0` |

### Conflict Detection

```bash
skillforge compose skill-a skill-b
```

If `skill-a` requires `dep >=2.0.0` but `skill-b` requires `dep <2.0.0`:

```
Composition error: Dependency resolution failed:
  - dep: 1.5.0 does not satisfy >=2.0.0 (from skill-a)
```

### Dependency Trees

```bash
skillforge tree code-review
```

```
code-review v1.2.0
├── security-scan v0.8.0
└── base-review v1.0.0
    └── linter v0.5.0
```

---

## Sandbox Testing

### Validation

```bash
skillforge validate .
```

Checks:
- Name is valid
- Version is valid
- Description meets length requirements
- Author is specified
- Required files exist

### Testing

```bash
skillforge test .
```

Runs the skill in an isolated environment:
- Creates temporary directory
- Copies skill files
- Executes test commands
- Reports results
- Cleans up

### Diffing

Compare two versions of a skill:

```python
from skillforge.sandbox import SkillSandbox

sandbox = SkillSandbox()
changes = sandbox.diff(skill_v1, skill_v2)

# Returns:
# {
#     "metadata_changed": True,
#     "content_changed": True,
#     "files_added": ["new_file.py"],
#     "files_removed": ["old_file.py"],
#     "files_changed": ["main.py"]
# }
```

---

## Python API

### Core Models

```python
from skillforge.core import (
    Skill,
    SkillMetadata,
    SkillVersion,
    SkillDependency,
    SkillConfig,
)

# Create a skill
skill = Skill(
    metadata=SkillMetadata(
        name="my-skill",
        version=SkillVersion(major=1, minor=0, patch=0),
        description="My awesome skill",
        author="me",
    ),
    content={"instructions": "Do something cool"},
)

# Version comparison
v1 = SkillVersion.parse("1.0.0")
v2 = SkillVersion.parse("2.0.0")
assert v2 > v1

# Version constraints
assert v2.satisfies(">=1.0.0")
assert v2.satisfies("^1.0.0")
```

### Dependency Resolver

```python
from skillforge.core.resolver import DependencyResolver

resolver = DependencyResolver()
resolver.register_skill(skill_a)
resolver.register_skill(skill_b)

# Resolve dependencies
result = resolver.resolve(skill_with_deps)
if result.success:
    print(f"Resolved {len(result.resolved)} dependencies")

# Get install order
order = resolver.get_install_order([skill_a, skill_b])
```

### Registry

```python
from skillforge.registry import SkillRegistry

registry = SkillRegistry()

# Publish
registry.publish(skill)

# Search
results = registry.search(query="code review")

# Get
skill = registry.get_skill("code-review")

# Stats
stats = registry.get_stats()
```

### Composition

```python
from skillforge.composition import SkillComposition

composition = SkillComposition()
composition.register_skill(skill_a)
composition.register_skill(skill_b)

# Chain
plan = composition.chain(["skill-a", "skill-b"])

# Parallel
plan = composition.parallel(["skill-a", "skill-b"])

# Analyze
analysis = composition.analyze(plan)

# Export
yaml_output = composition.export_plan(plan, output_format="yaml")
```

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/reyansh14coder-ux/skillforge.git
cd skillforge
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
ruff check .
ruff format .
```

---

## Roadmap

### Phase 1: Core (Complete)
- [x] Skill models and validation
- [x] Dependency resolution
- [x] Local registry
- [x] CLI interface
- [x] Sandbox testing
- [x] Composition engine
- [x] Test suite (42 tests)
- [x] CI/CD pipeline

### Phase 2: Remote Registry
- [ ] Remote registry server (skillforge.dev)
- [ ] User authentication
- [ ] Skill ratings and reviews
- [ ] Download statistics

### Phase 3: Advanced Features
- [ ] Automated security scanning
- [ ] IDE extensions (VS Code, JetBrains)
- [ ] Skill templates and scaffolding
- [ ] Team/organization registries
- [ ] Skill analytics and usage tracking

### Phase 4: Ecosystem
- [ ] Skill marketplace
- [ ] Paid skills support
- [ ] Enterprise features
- [ ] API for programmatic access

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Acknowledgments

Built for the AI agent community. Inspired by npm, pip, cargo, and the amazing work being done with Claude Code, Codex, Cursor, and other AI coding agents.
