# Contributing to mddiff

Contributions are welcome!

## Development Setup

```bash
git clone https://github.com/izag8216/mddiff.git
cd mddiff
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
python3 -m pytest tests/ -v
```

## Code Style

- Python 3.9+ compatibility
- Type hints on all public functions
- Docstrings on all public modules/classes/functions
- Tests required for new features

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`python3 -m pytest`)
5. Commit with clear messages
6. Push and create a Pull Request

## Reporting Issues

Please use GitHub Issues with:
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
