# SkillForge

**The Universal AI Agent Skill Registry & Composition Engine**

[![CI](https://github.com/skillforge/skillforge/actions/workflows/ci.yml/badge.svg)](https://github.com/skillforge/skillforge/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## What is SkillForge?

The AI agent ecosystem has exploded with skills — for Claude Code, Codex, Cursor, Cline, and more. But there's **no universal infrastructure** for managing them.

**SkillForge** is the missing layer. It's the **npm/pip/cargo for AI agent skills**.

```
┌─────────────────────────────────────────────────────────┐
│                    SkillForge                           │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Registry │  │ Resolver │  │ Sandbox  │  │ Compose│ │
│  │          │  │          │  │          │  │        │ │
│  │ Publish  │  │ Deps     │  │ Test     │  │ Chain  │ │
│  │ Search   │  │ Version  │  │ Validate │  │ Merge  │ │
│  │ Discover │  │ Conflicts│  │ Diff     │  │ Plan   │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Universal CLI                        │  │
│  │  init · publish · install · search · compose     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Features

- **Universal Registry** — Publish, discover, and manage skills across any framework
- **Dependency Resolution** — Automatic version resolution with conflict detection
- **Sandbox Testing** — Test skills in isolated environments before deployment
- **Skill Composition** — Chain, merge, and orchestrate multiple skills into workflows
- **Multi-Framework** — Works with Claude Code, Codex, Cursor, Cline, OpenCode, and more
- **Version Management** — Semantic versioning with constraint solving
- **Dependency Trees** — Visualize skill dependency graphs
- **Export & Distribute** — Package skills for sharing

## Quick Start

### Installation

```bash
pip install skillforge
```

### Create a Skill

```bash
mkdir my-skill && cd my-skill
skillforge init --name "awesome-skill" --author "your-name"
```

This creates:
- `skillforge.yaml` — Skill configuration
- `SKILL.md` — Skill instructions (Claude Code compatible)

### Publish to Registry

```bash
skillforge publish .
```

### Search & Install

```bash
skillforge search "code review"
skillforge install author/awesome-skill
```

### Compose Skills

```bash
skillforge compose skill-a skill-b skill-c --type chain
```

## Commands

| Command | Description |
|---------|-------------|
| `skillforge init` | Initialize a new skill project |
| `skillforge validate` | Validate a skill |
| `skillforge publish` | Publish to local registry |
| `skillforge install` | Install from registry |
| `skillforge search` | Search for skills |
| `skillforge info` | Show skill details |
| `skillforge delete` | Remove from registry |
| `skillforge test` | Test in sandbox |
| `skillforge compose` | Compose multiple skills |
| `skillforge tree` | Show dependency tree |
| `skillforge export` | Export as distributable |
| `skillforge stats` | Registry statistics |

## Skill Format

Skills are defined in `SKILL.md` (compatible with Claude Code) or `skillforge.yaml`:

```yaml
metadata:
  name: my-skill
  version: 1.0.0
  description: "Does something awesome"
  author: your-name
  framework: universal
  capability: tool
  tags: [automation, utility]
  dependencies:
    - name: base-skill
      version_constraint: ">=0.5.0"

config:
  env_vars:
    API_KEY: "Required API key"
  requires_permissions: ["filesystem"]
  max_execution_time_seconds: 300

content:
  instructions: |
    Your skill instructions here...
```

## Architecture

```
skillforge/
├── core/
│   ├── models.py      # Data models (Skill, Version, etc.)
│   ├── resolver.py    # Dependency resolution engine
│   └── loader.py      # Multi-format skill loader
├── registry/
│   └── store.py       # Local skill registry
├── sandbox/
│   └── executor.py    # Isolated execution environment
├── composition/
│   └── engine.py      # Skill composition engine
├── cli/
│   └── main.py        # CLI interface
└── utils/
    └── helpers.py     # Utility functions
```

## Why SkillForge?

The AI agent skill ecosystem in 2026 looks like npm in 2010 — everyone's building packages, but there's no infrastructure. SkillForge provides that infrastructure:

1. **Discovery** — Find the right skill for your task
2. **Trust** — Validate skills before running them
3. **Composition** — Chain skills into powerful workflows
4. **Versioning** — Manage compatibility across updates
5. **Universal** — Works with any agent framework

## Roadmap

- [ ] Remote registry (skillforge.dev)
- [ ] Skill ratings and reviews
- [ ] Automated security scanning
- [ ] IDE extensions (VS Code, JetBrains)
- [ ] Skill templates and scaffolding
- [ ] Team/organization registries
- [ ] Skill analytics and usage tracking

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE)
