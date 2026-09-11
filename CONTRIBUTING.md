# Contributing to SkillForge

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/skillforge/skillforge.git
cd skillforge
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Code Style

We use `ruff` for linting and formatting:

```bash
ruff check .
ruff format .
```

## Type Checking

```bash
mypy skillforge/
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Reporting Issues

- Use the GitHub issue tracker
- Include Python version and OS
- Provide minimal reproduction steps

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
