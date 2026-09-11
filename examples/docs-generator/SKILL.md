# Documentation Generator Skill

Automatic documentation generation from code comments, docstrings, and type hints.

**Author:** skillforge-examples
**Version:** 0.9.0
**Framework:** universal
**Capability:** tool
**Tags:** documentation, docstrings, api-docs, markdown

## Dependencies

- code-review >=1.0.0

## Environment Variables

- `DOC_FORMAT`: Output format: markdown, rst, html (default: markdown)
- `INCLUDE_PRIVATE`: Include private functions in docs (default: false)

## Instructions

Generate comprehensive documentation from code:

### 1. Code Analysis
- Parse docstrings (Google, NumPy, Sphinx styles)
- Extract type hints
- Identify public API surface
- Map function relationships

### 2. Documentation Types

#### API Reference
- Function signatures with types
- Parameter descriptions
- Return value documentation
- Usage examples

#### Architecture Docs
- Module relationships
- Data flow diagrams (Mermaid)
- Dependency graphs

#### README Generation
- Project overview
- Installation instructions
- Quick start guide
- API reference links

### 3. Documentation Standards
- Follow Google style docstrings
- Include code examples
- Link to related functions
- Mark experimental features

## Output Format

```
## Documentation Generated

**Module:** my_project
**Public Functions:** 25
**Classes:** 8
**Coverage:** 87%

### Files Created
- docs/api/README.md
- docs/architecture.md
- docs/examples.md

### Coverage Report
| Module | Functions | Documented | Coverage |
|--------|-----------|------------|----------|
| core | 12 | 11 | 92% |
| utils | 8 | 6 | 75% |
| api | 5 | 5 | 100% |
```
