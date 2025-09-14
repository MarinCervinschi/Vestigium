# Vestigium 🫆🌳

[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen.svg)](https://pre-commit.com/)
[![CI Tests](https://github.com/MarinCervinschi/Vestigium/actions/workflows/ci.yml/badge.svg)](https://github.com/MarinCervinschi/Vestigium/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/MarinCervinschi/Vestigium/branch/main/graph/badge.svg)](https://codecov.io/gh/MarinCervinschi/Vestigium)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

<img src="assets/vestigium_logo.png" alt="Vestigium Logo" width="400"/>

A simple Version Control System (VCS) built in Python for educational purposes.

## Features

- **Clean architecture**: Modular design with separated CLI, core logic, and commands
- **Docker support**: Isolated testing environment with Docker Compose
- **CI/CD**: Automated testing with GitHub Actions

## Installation

### Local Development

1. Clone the repository:

```bash
git clone https://github.com/MarinCervinschi/Vestigium.git
cd Vestigium
```

2. Install in development mode with dependencies:

```bash
pip install -e ".[dev]"
```

3. Make the executable script runnable:

```bash
chmod +x ./ves
```

### Docker Development

For a clean, isolated environment:

```bash
# Run tests
docker compose run --rm vestigium-test

# Start development environment
docker compose run --rm vestigium-dev
```

## Usage

### Available Commands

For detailed usage and examples of all commands, see [COMMANDS.md](docs/COMMANDS.md).

**Basic Commands:**
- `init` - Initialize a new repository
- `add` - Add files to staging area
- `commit` - Record changes to repository
- `status` - Show working tree status
- `checkout` - Extract commit to directory

**Object Management:**
- `hash-object` - Calculate and store file hash
- `cat-file` - Display object content

**Navigation & History:**
- `log` - Show commit history
- `ls-files` - List files in index
- `ls-tree` - List tree contents

**References & Tags:**
- `tag` - Create and list tags
- `show-ref` - Show all references
- `rev-parse` - Resolve identifiers

**Utilities:**
- `rm` - Remove files from index
- `check-ignore` - Verify ignore rules

## Development

### Code Quality Tools

This project uses several tools to maintain code quality:

```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Type checking with MyPy
mypy src/

# Run all quality checks
black src/ tests/ && isort src/ tests/ && mypy src/
```

### Testing

#### Docker Testing (Recommended)

```bash
# Run tests in clean Docker environment
docker compose run --rm vestigium-test

# Development environment with all tools available
docker compose run --rm vestigium-dev
```

#### Local Testing

```bash
# Run tests locally
pytest tests/ -v

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
