# Makefile Quick Reference Guide

This project includes a comprehensive Makefile with 40+ commands for development, testing, and deployment. All commands use `uv` for dependency management.

## Quick Start

```bash
make install-dev    # Install all dependencies
make fresh-db       # Setup fresh database (reset, migrate, seed)
make up             # Start development server
make info           # Show quick reference
```

## Command Categories

### 📦 Setup & Dependencies
| Command | Description |
|---------|-------------|
| `make install-dev` | Install all dependencies (dev + main) |
| `make install-prod` | Install only production dependencies |
| `make sync` | Sync/refresh all dependencies |

### 🚀 Server & Development
| Command | Description |
|---------|-------------|
| `make up` | Start dev server (auto-opens browser) |
| `make down` | Stop dev server |
| `make shell` | Open Django interactive shell |
| `make shell-db` | Open database shell |

### 🗄️ Database Operations
| Command | Description |
|---------|-------------|
| `make migrate` | Apply all pending migrations |
| `make makemigrations` | Create migrations for model changes |
| `make migrations` | Show migration status |
| `make show-migrations` | Display all migrations (detailed) |
| `make reset-db` | ⚠️ Reset database (DELETE ALL DATA) |
| `make fresh-db` | Reset, migrate, and seed database |
| `make backup-db` | Backup SQLite database |

### 👤 User Management
| Command | Description |
|---------|-------------|
| `make admin-user` | Create superuser (interactive) |
| `make create-superuser` | Create superuser non-interactively |
| `make seed` | Seed demo data |

### ✅ Testing
| Command | Description |
|---------|-------------|
| `make test` | Run all tests (verbose) |
| `make test-quick` | Run tests (quiet output) |
| `make test-watch` | Run tests in watch mode |
| `make coverage` | Run tests with coverage report |
| `make coverage-report` | Show coverage statistics |

### 🔍 Code Quality
| Command | Description |
|---------|-------------|
| `make lint` | Run all linters (ruff, mypy, bandit) |
| `make type-check` | Run type checker (mypy) |
| `make format-check` | Check formatting without fixing |
| `make format` | Auto-format code with ruff |
| `make security` | Run security scanner (bandit) |
| `make fix` | Format code and lint |
| `make check` | Django deployment checklist |

### 📦 Static Files & Collection
| Command | Description |
|---------|-------------|
| `make collect-static` | Collect static files for production |
| `make collectstatic` | Alias for `collect-static` |

### 🗑️ Cleaning Up
| Command | Description |
|---------|-------------|
| `make clean-pycache` | Remove Python cache files |
| `make clean-cache` | Remove all cache directories |
| `make clean-migrations` | List migration files (review only) |
| `make clean-all` | Clean all caches and artifacts |

### 🐳 Docker
| Command | Description |
|---------|-------------|
| `make docker-up` | Build and start Docker stack |
| `make docker-down` | Stop Docker stack |
| `make docker-logs` | Tail Docker logs (web container) |
| `make docker-rebuild` | Rebuild Docker images |

### ℹ️ Information & Utilities
| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make info` | Show project information |
| `make status` | Show project status |
| `make versions` | Show dependency versions |
| `make import-demo` | Import demo data (XLSX) |

## Common Workflows

### Initial Setup
```bash
make install-dev    # Install dependencies
make fresh-db       # Setup database
make seed           # Seed demo data
make up             # Start server
```

### Development Cycle
```bash
make test           # Run tests
make lint           # Check code quality
make format         # Auto-format code
make up             # Start server
```

### Before Committing
```bash
make test           # Ensure tests pass
make fix            # Format and lint code
make check          # Run deployment checks
```

### Cleanup
```bash
make clean-all      # Clean cache files
make format         # Format code
make lint           # Verify linting
```

## Available Endpoints

When running `make up`:
- **Main App**: http://localhost:8000/
- **Django Admin**: http://localhost:8000/admin/
- **REST API**: http://localhost:8000/api/v1/
- **Browsable API**: http://localhost:8000/api/v1/

## Project Statistics

- **Tests**: 70 total, 100% passing
- **Python Files**: 49 files
- **Lines of Code**: 2,996 LOC
- **Linters**: Ruff, MyPy, Bandit
- **Type Coverage**: 100% (mypy clean)

## Tips

1. **Use `make help` frequently** - Lists all available commands with descriptions
2. **`make info`** - Quick reference for endpoints and common tasks
3. **`make test-quick`** - Fastest way to verify code changes
4. **`make fix`** - One command to format and lint
5. **Combine commands**: `make reset-db migrate seed up` - multiple commands in sequence

## Notes

- All commands use `uv` for Python dependency management
- Database is SQLite by default (`db.sqlite3`)
- Most commands have safety checks (e.g., `reset-db` requires confirmation)
- Use `make down` to stop the dev server gracefully
- Docker commands require Docker to be installed

## Getting Help

```bash
make help           # Show all available commands
make info           # Show quick reference
make status         # Show project information
```

For more information, see the main `Makefile` file.
