"""Built-in skill templates for quick project scaffolding."""

from __future__ import annotations

TEMPLATES = {
    "code-review": {
        "name": "code-review",
        "description": "Automated code review with security and style checks",
        "instructions": """# Code Review Skill

## Steps
1. Read the diff or changed files
2. Check for security issues (injection, XSS, auth bypass)
3. Check for bugs (null checks, edge cases, race conditions)
4. Check style (naming, formatting, comments)
5. Provide actionable feedback with file:line references

## Output Format
For each issue found:
- File and line number
- Severity (critical/warning/info)
- Description
- Suggested fix
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "security-audit": {
        "name": "security-audit",
        "description": "Security audit for code and dependencies",
        "instructions": """# Security Audit Skill

## Steps
1. Scan code for vulnerabilities (OWASP Top 10)
2. Check dependencies for known CVEs
3. Review authentication and authorization
4. Check for secrets/credentials in code
5. Generate security report

## Critical Checks
- SQL injection
- XSS vulnerabilities
- Insecure deserialization
- Hardcoded secrets
- Weak cryptography
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "test-generator": {
        "name": "test-generator",
        "description": "Generate comprehensive test suites",
        "instructions": """# Test Generator Skill

## Steps
1. Analyze the function/class to test
2. Identify edge cases and boundary conditions
3. Generate unit tests with assertions
4. Generate integration tests if applicable
5. Check test coverage

## Test Types
- Happy path
- Edge cases (empty, null, max values)
- Error cases
- Boundary conditions
- Performance (if applicable)
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "refactor-assistant": {
        "name": "refactor-assistant",
        "description": "Code refactoring with safety checks",
        "instructions": """# Refactor Assistant Skill

## Steps
1. Analyze current code structure
2. Identify code smells and anti-patterns
3. Propose refactoring plan
4. Execute refactoring
5. Verify no behavior change
6. Run tests

## Code Smells to Detect
- Long methods
- Duplicated code
- Deep nesting
- God objects
- Feature envy
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "api-designer": {
        "name": "api-designer",
        "description": "RESTful API design and documentation",
        "instructions": """# API Designer Skill

## Steps
1. Analyze requirements
2. Design endpoint structure
3. Define request/response schemas
4. Add validation rules
5. Generate OpenAPI spec

## Design Principles
- RESTful naming conventions
- Consistent error responses
- Pagination support
- Rate limiting
- Versioning strategy
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "database-optimizer": {
        "name": "database-optimizer",
        "description": "Database query optimization and indexing",
        "instructions": """# Database Optimizer Skill

## Steps
1. Analyze slow queries
2. Review query execution plans
3. Suggest index improvements
4. Optimize N+1 queries
5. Recommend schema changes

## Common Optimizations
- Add missing indexes
- Remove unused indexes
- Optimize JOIN operations
- Reduce data transfer
- Cache frequently accessed data
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "doc-writer": {
        "name": "doc-writer",
        "description": "Generate comprehensive documentation",
        "instructions": """# Documentation Writer Skill

## Steps
1. Analyze code structure and APIs
2. Generate README content
3. Create API documentation
4. Add inline comments
5. Generate changelog

## Documentation Types
- README.md
- API reference
- Installation guide
- Usage examples
- Troubleshooting guide
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "migration-assistant": {
        "name": "migration-assistant",
        "description": "Code migration and upgrade assistance",
        "instructions": """# Migration Assistant Skill

## Steps
1. Analyze current codebase
2. Identify migration targets
3. Create migration plan
4. Execute migration step by step
5. Verify functionality

## Supported Migrations
- Python 2 to 3
- JavaScript ES5 to ES6+
- React class to hooks
- Database migrations
- Framework upgrades
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
}


def get_template(name: str) -> dict | None:
    return TEMPLATES.get(name)


def list_templates() -> list[str]:
    return sorted(TEMPLATES.keys())


def get_template_details(name: str) -> dict | None:
    t = TEMPLATES.get(name)
    if t:
        return {
            "name": t["name"],
            "description": t["description"],
            "version": t["version"],
            "author": t["author"],
            "capability": t["capability"],
        }
    return None
