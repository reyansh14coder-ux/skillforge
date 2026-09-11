# Security Scan Skill

Comprehensive security vulnerability scanner for codebases and dependencies.

**Author:** skillforge-examples
**Version:** 0.8.0
**Framework:** universal
**Capability:** tool
**Tags:** security, vulnerability, scanning, dependency-audit

## Environment Variables

- `SCAN_TARGETS`: Comma-separated scan targets: code, deps, secrets, config (default: all)
- `FAIL_ON`: Severity level to fail on: none, low, medium, high, critical (default: medium)

## Instructions

Perform a comprehensive security scan:

### 1. Dependency Audit
- Check for known CVEs in dependencies
- Identify outdated packages with security patches
- Verify dependency signatures
- Check for typosquatting attacks

### 2. Secret Detection
- API keys and tokens
- Passwords and credentials
- Private keys and certificates
- Connection strings with embedded passwords

### 3. Code Vulnerabilities
- SQL injection patterns
- Cross-site scripting (XSS)
- Command injection
- Path traversal
- Insecure cryptography usage
- Hardcoded IP addresses

### 4. Configuration Security
- Debug mode in production
- Verbose error messages
- Missing security headers
- Insecure CORS policies
- Default credentials

## Risk Levels

| Level | Description | Action |
|-------|-------------|--------|
| Critical | Immediate exploitation risk | Fix before merge |
| High | Likely exploitable | Fix within 24h |
| Medium | Exploitable with effort | Fix within 1 week |
| Low | Minor security improvement | Track in backlog |
| Info | Best practice recommendation | Optional |

## Output Format

```
## Security Scan Report

**Scan Date:** YYYY-MM-DD HH:MM:SS
**Targets:** code, deps, secrets, config
**Duration:** Xs

### Summary
- Critical: N
- High: N
- Medium: N
- Low: N
- Info: N

### Findings

#### [CRITICAL] SQL Injection in user_service.py:42
```python
# Vulnerable
query = f"SELECT * FROM users WHERE id = {user_id}"

# Fixed
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

#### [HIGH] Hardcoded API Key in config.py:15
...
```
