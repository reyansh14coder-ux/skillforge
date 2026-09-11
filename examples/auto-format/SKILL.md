# Auto Format Skill

Automatic code formatting and style enforcement across multiple languages.

**Author:** skillforge-examples
**Version:** 1.0.0
**Framework:** universal
**Capability:** tool
**Tags:** formatting, style, linting, automation

## Environment Variables

- `FORMAT_LANGUAGES`: Comma-separated list of languages to format (default: all detected)
- `DRY_RUN`: If true, show changes without applying (default: false)

## Instructions

Automatically format code to match project conventions:

### 1. Language Detection
- Analyze file extensions and config files
- Detect primary language(s) in project
- Load appropriate formatter configuration

### 2. Format Rules by Language

#### Python
- Line length: 88 characters (Black default)
- Import sorting: isort compatible
- String quotes: double quotes
- Trailing commas: yes

#### JavaScript/TypeScript
- Prettier configuration
- ESLint integration
- Consistent semicolons
- Arrow function preference

#### Go
- gofmt standard
- goimports for imports
- golangci-lint compliance

### 3. Pre-commit Hooks
- Generate `.pre-commit-config.yaml`
- Configure hook for auto-formatting
- Add commit message validation

## Output Format

```
## Format Report

**Files Processed:** N
**Files Modified:** M
**Languages:** python, javascript

### Changes Applied

| File | Language | Changes |
|------|----------|---------|
| src/main.py | Python | reformatted, imports sorted |
| src/utils.js | JavaScript | prettified |
| README.md | Markdown | no changes |

### Summary
- Reformatted: X files
- Already formatted: Y files
- Errors: Z files
```
