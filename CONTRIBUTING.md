# Contributing to Blender Drone Sim

First off, thank you for considering contributing to Blender Drone Sim! It's people like you that make it such a great tool.

## Development Setup

To set up your local development environment:

1. Clone the repo
2. Install the package with developer dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Coding Standards

We use `ruff` for fast linting and formatting, and `mypy` for static type checking. 

Before committing your changes, please ensure your code is clean by running the following commands from the root directory. 
*(Note: Our main code directories are `custom_drone_env`, `blender_addon`, and `tests` instead of `src/`)*

```bash
# Run linting checks
ruff check custom_drone_env/ blender_addon/ tests/

# Format code
ruff format custom_drone_env/ blender_addon/ tests/

# Run type checker
mypy custom_drone_env/ blender_addon/ tests/
```

## Running Tests

We use `pytest` for running our test suite. To run the tests:

```bash
pytest tests/
```

## Submitting Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes (`pytest`).
5. Ensure your code passes linting, formatting, and type checks.
6. Issue that pull request!
