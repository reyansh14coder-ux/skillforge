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
    "performance-profiler": {
        "name": "performance-profiler",
        "description": "Profile and optimize code performance",
        "instructions": """# Performance Profiler Skill

## Steps
1. Identify performance bottlenecks
2. Profile CPU and memory usage
3. Analyze algorithm complexity
4. Optimize hot paths
5. Benchmark before/after

## Key Metrics
- Execution time
- Memory allocation
- I/O operations
- CPU utilization
- Cache hit rate

## Optimization Techniques
- Memoization
- Lazy loading
- Batch processing
- Parallel execution
- Connection pooling
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "api-mocker": {
        "name": "api-mocker",
        "description": "Generate mock API servers for testing",
        "instructions": """# API Mocker Skill

## Steps
1. Analyze API specification
2. Generate mock endpoints
3. Create realistic test data
4. Add delay simulation
5. Support error scenarios

## Features
- RESTful endpoint mocking
- OpenAPI/Swagger support
- Request/response recording
- Stateful mocking
- CORS support
- Rate limiting simulation
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "docker-builder": {
        "name": "docker-builder",
        "description": "Generate optimized Docker configurations",
        "instructions": """# Docker Builder Skill

## Steps
1. Analyze project structure
2. Detect language/framework
3. Generate multi-stage Dockerfile
4. Create docker-compose.yml
5. Optimize image size

## Best Practices
- Multi-stage builds
- Layer caching
- Non-root user
- Health checks
- Secret management
- Minimal base images
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "ci-pipeline": {
        "name": "ci-pipeline",
        "description": "Generate CI/CD pipeline configurations",
        "instructions": """# CI Pipeline Skill

## Steps
1. Detect project type
2. Generate GitHub Actions workflow
3. Add test automation
4. Configure deployment
5. Set up notifications

## Supported Platforms
- GitHub Actions
- GitLab CI
- CircleCI
- Travis CI
- Jenkins
- Azure DevOps

## Pipeline Stages
- Build
- Test
- Lint
- Security scan
- Deploy
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "graphql-schema": {
        "name": "graphql-schema",
        "description": "Generate GraphQL schemas from requirements",
        "instructions": """# GraphQL Schema Skill

## Steps
1. Analyze data requirements
2. Design type system
3. Generate resolvers
4. Add subscriptions
5. Create documentation

## Schema Components
- Types and interfaces
- Queries and mutations
- Subscriptions
- Enums and scalars
- Input types
- Directives
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "microservice-scaffold": {
        "name": "microservice-scaffold",
        "description": "Scaffold microservice architecture",
        "instructions": """# Microservice Scaffold Skill

## Steps
1. Design service boundaries
2. Generate service templates
3. Set up API gateway
4. Configure service discovery
5. Add monitoring

## Components
- Service skeleton
- API gateway config
- Database per service
- Event bus integration
- Circuit breaker
- Distributed tracing
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "data-pipeline": {
        "name": "data-pipeline",
        "description": "Build ETL and data processing pipelines",
        "instructions": """# Data Pipeline Skill

## Steps
1. Define data sources
2. Design transformation logic
3. Implement extraction
4. Add validation
5. Configure loading

## Pipeline Types
- Batch processing
- Real-time streaming
- ETL/ELT
- Data lake ingestion
- Data warehouse sync

## Quality Checks
- Schema validation
- Data completeness
- Duplicate detection
- Anomaly detection
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "state-machine": {
        "name": "state-machine",
        "description": "Generate finite state machines from specs",
        "instructions": """# State Machine Skill

## Steps
1. Identify states and transitions
2. Define guards and actions
3. Generate state machine code
4. Add visualization
5. Create tests

## Features
- State diagrams
- Transition tables
- Guard conditions
- Entry/exit actions
- History states
- Parallel states
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "regex-builder": {
        "name": "regex-builder",
        "description": "Build and test regular expressions",
        "instructions": """# Regex Builder Skill

## Steps
1. Analyze input patterns
2. Build regex expression
3. Add test cases
4. Optimize performance
5. Generate documentation

## Pattern Types
- Email validation
- Phone numbers
- URLs
- Dates
- Credit cards
- Custom patterns

## Output
- Regex pattern
- Test cases
- Performance metrics
- Edge cases
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "cli-builder": {
        "name": "cli-builder",
        "description": "Generate CLI tools with proper structure",
        "instructions": """# CLI Builder Skill

## Steps
1. Define command structure
2. Generate argument parsing
3. Add help text
4. Implement completion
5. Create documentation

## Features
- Subcommands
- Option groups
- Interactive mode
- Shell completion
- Color output
- Progress bars

## Output Formats
- Python (click/argparse)
- Node.js (commander/yargs)
- Go (cobra)
- Rust (clap)
""",
        "version": "0.1.0",
        "author": "skillforge",
        "capability": "tool",
        "framework": "universal",
    },
    "webhook-manager": {
        "name": "webhook-manager",
        "description": "Manage and process webhook integrations",
        "instructions": """# Webhook Manager Skill

## Steps
1. Define webhook endpoints
2. Add signature verification
3. Implement retry logic
4. Create payload validation
5. Set up monitoring

## Features
- Signature verification (HMAC)
- Retry with exponential backoff
- Payload validation
- Rate limiting
- Logging and auditing
- Dead letter queue

## Integrations
- GitHub
- Stripe
- Slack
- Discord
- Custom webhooks
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


def get_template_categories() -> dict[str, list[str]]:
    """Group templates by category."""
    categories = {
        "Code Quality": ["code-review", "refactor-assistant", "test-generator"],
        "Security": ["security-audit"],
        "DevOps": ["docker-builder", "ci-pipeline", "microservice-scaffold"],
        "API": ["api-designer", "api-mocker", "graphql-schema", "webhook-manager"],
        "Data": ["database-optimizer", "data-pipeline"],
        "Documentation": ["doc-writer"],
        "Migration": ["migration-assistant"],
        "Performance": ["performance-profiler"],
        "Architecture": ["state-machine", "cli-builder"],
        "Utilities": ["regex-builder"],
    }
    return categories
