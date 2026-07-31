# Contributing to NOW Index

Thank you for your interest in contributing to the NOW Quant Framework! We welcome contributions from everyone.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### 1. Reporting Issues

- Check if the issue already exists in the [issue tracker](https://github.com/Liam-Son/NOW-index/issues)
- Provide a clear and descriptive title
- Include steps to reproduce, expected behavior, and actual behavior
- Include version information and environment details

### 2. Feature Requests

- Describe the feature and its use case
- Explain how it fits into the NOW Index architecture
- Provide examples if possible

### 3. Pull Requests

1. **Fork** the repository
2. **Create a branch** with a descriptive name:
   - `feature/your-feature-name`
   - `fix/your-fix-name`
   - `docs/your-docs-update`
3. **Make your changes** following our coding standards
4. **Write tests** for your changes
5. **Run the test suite** to ensure everything passes
6. **Submit a pull request** with a clear description

### Development Guidelines

#### Coding Standards

- Follow PEP 8 for Python code
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

#### Adding a New Asset Class

1. Add the new class to `AssetClass` enum in `engine/scoring.py`
2. Add it to `ASSET_CLASS_GROUPS` if applicable
3. Register example assets in `AssetRegistry.seed_default_assets()`
4. The scoring engine works automatically — no changes needed

#### Adding a New Factor

1. Create a factor calculator method in `NOWScorer`
2. Add the factor to `FACTOR_WEIGHTS`
3. Register it in `_register_default_factors()`
4. Or use the plugin system: `FactorRegistry` in `engine/factors.py`

#### Testing

- Write tests for all new functionality
- Run existing tests before submitting: `pytest tests/ -v`
- Aim for >80% code coverage

### Project Setup

```bash
git clone https://github.com/Liam-Son/NOW-index.git
cd NOW-index
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx flake8
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_scoring.py -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=engine --cov=api --cov=database
```

## Questions?

Feel free to open an issue or reach out to the maintainers.

Thank you for contributing! 🚀
