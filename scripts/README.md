# Scripts Directory

This directory contains utility scripts and build tools for the project.

## Makefile

The `Makefile` provides convenient shortcuts for common Docker Compose operations.

### Usage

From the project root directory:

```bash
# Using make (if installed)
make -f scripts/Makefile up
make -f scripts/Makefile down
make -f scripts/Makefile reset

# Or use docker compose directly
docker compose up --build
docker compose down
docker compose down -v
```

### Available Commands

- `up` - Build and start all containers
- `down` - Stop containers (preserves data)
- `reset` - Stop containers and remove all data (full reset)

