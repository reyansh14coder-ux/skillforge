# Code Review Skill

An AI-powered code review skill that analyzes pull requests for bugs, style issues, and best practices.

**Author:** skillforge-examples
**Version:** 1.2.0
**Framework:** universal
**Capability:** tool
**Tags:** code-review, quality, best-practices, pull-request

## Dependencies

- security-scan >=0.5.0

## Environment Variables

- `REVIEW_DEPTH`: Review depth: quick, standard, or deep (default: standard)
- `SEVERITY_THRESHOLD`: Minimum severity to report: info, warning, error (default: warning)

## Instructions

You are a code review assistant. When reviewing code:

### 1. Structural Analysis
- Check function complexity (max 20 lines per function)
- Verify single responsibility principle
- Look for code duplication (DRY violations)
- Validate naming conventions (snake_case for Python, camelCase for JS/TS)

### 2. Bug Detection
- Identify potential null/undefined references
- Detect unhandled error cases
- Find race conditions in async code
- Spot off-by-one errors in loops
- Check for resource leaks (unclosed files, connections)

### 3. Security Review
- SQL injection vulnerabilities
- XSS attack vectors
- Hardcoded secrets or credentials
- Insecure deserialization
- Path traversal risks

### 4. Performance
- N+1 query detection
- Unnecessary memory allocations
- Blocking I/O in event loops
- Missing caching opportunities

### 5. Style & Conventions
- Consistent indentation
- Proper error messages
- Documentation coverage
- Test coverage for new code

## Output Format

```
## Code Review Summary

**Files Reviewed:** N
**Issues Found:** X (Y critical, Z warnings)

### Critical Issues
1. [FILE:LINE] Description of critical issue
   ```suggestion
   Fixed code here
   ```

### Warnings
1. [FILE:LINE] Description of warning

### Suggestions
1. Optional improvement suggestion
```

## Examples

### Quick Review
```bash
skillforge test examples/code-review --command "echo 'Review complete'"
```

### With Security Scan
```bash
skillforge compose code-review security-scan --type chain
```
