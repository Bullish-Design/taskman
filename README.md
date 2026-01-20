# TaskMan

**TaskMan** is an orchestration and safety layer for [Taskwarrior](https://taskwarrior.org/) with first-class LLM integration. It provides:

- **Safe, deterministic execution** of LLM-proposed task changes
- **User-friendly UX** with analyze and revise workflows
- **Strong typing** via [Taskdantic](https://github.com/Bullish-Design/taskdantic) for UDA management
- **LLM-assisted planning** with strict validation and constrained outputs

## Features

### 🔒 Safety First

- **Strict allowlist** of permitted fields and operations
- **Grammar-based parser** for revise scripts (no shell evaluation)
- **UUID normalization** to avoid ambiguity
- **Editor review** before executing any changes
- **Validation** at every step

### 🤖 LLM Integration

- **Analyze** tasks for insights and missing context
- **Revise** tasks with LLM-generated improvements
- **Batch analyze** for consistency across multiple tasks
- Powered by the `llms` library with structured output

### 📋 UDA Management

- **Single source of truth** for User Defined Attributes
- Define UDAs in Python using Taskdantic models
- Automatic `taskrc` configuration generation
- Type-safe UDA validation

## Installation

### Prerequisites

- Python 3.11+
- [Taskwarrior](https://taskwarrior.org/) installed
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Install from source

```bash
git clone https://github.com/Bullish-Design/taskman
cd taskman
uv pip install -e .
```

## Quick Start

### 1. Sync UDAs

Generate UDA configuration for Taskwarrior:

```bash
# Use example UDAs
taskman sync-udas --example

# Or provide your own model paths
taskman sync-udas --model myproject.models
```

This creates `~/.taskrc-udas`. Add to your `~/.taskrc`:

```
include ~/.taskrc-udas
```

### 2. Analyze a Task

Get LLM insights about a task:

```bash
taskman analyze 123
```

Output includes:
- Summary and insights
- Suggestions for improvement
- Missing context identification
- Next actions

### 3. Revise a Task

Let the LLM propose improvements:

```bash
taskman revise 123
```

Workflow:
1. Exports task
2. Generates revise script via LLM
3. Opens script in `$EDITOR` for review
4. Validates commands
5. Shows preview of changes
6. Executes after confirmation

### 4. Batch Analyze

Analyze multiple tasks for consistency:

```bash
taskman batch-analyze-cmd "status:pending project:work"
```

## Configuration

TaskMan can be configured via environment variables:

```bash
# Taskwarrior binary
export TASKMAN_TASK_BIN="task"

# LLM settings
export TASKMAN_LLM_MODEL="gpt-4"
export TASKMAN_LLM_TEMPERATURE="0.1"

# Safety mode
export TASKMAN_DEFAULT_MODE="safe"  # or "power"

# Editor
export EDITOR="vim"
```

## Safety Policy

### SAFE Mode (Default)

Allowed fields:
- `tags`, `project`, `priority`
- `due`, `until`
- `depends`
- All registered UDAs
- `annotate` (append-only)

Forbidden:
- `description` modifications
- `start`/`stop`
- `recur`
- Delete/purge operations

### POWER Mode

Allows additional operations but still validates everything.

Enable with `--mode power` or `TASKMAN_DEFAULT_MODE=power`.

## Revise Script Grammar

Revise scripts use a strict, safe subset of Taskwarrior commands:

### Modify Command

```bash
task <selector> modify <field_ops...>
```

Field operations:
- Set field: `field:value`
- Add tag: `+tagname`
- Remove tag: `-tagname`

Example:
```bash
task 123 modify project:work priority:H +urgent -someday
```

### Annotate Command

```bash
task <selector> annotate <text...>
```

Example:
```bash
task 123 annotate "Discussed with team on 2024-01-15"
```

### Rules

- One command per line
- Use UUID or numeric ID as selector
- Only modify allowed fields
- No shell features (pipes, redirection, etc.)
- Comments start with `#`

## UDA Examples

Example UDAs included in TaskMan:

| UDA | Type | Description |
|-----|------|-------------|
| `context` | string | Where/when the task should be done |
| `why` | string | Reason or motivation |
| `stakeholder` | string | Who cares about this task |
| `waiting_on` | string | What/who is blocking this |
| `next_action` | string | Very next physical action |
| `impact` | string | Expected impact (low/medium/high/critical) |
| `effort` | string | Effort required (trivial/small/medium/large/huge) |

## Development

### Setup

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/taskman

# Linting
ruff check src/taskman
```

### Project Structure

```
taskman/
├── src/taskman/
│   ├── __init__.py       # Public API
│   ├── cli.py            # CLI commands
│   ├── config.py         # Configuration
│   ├── policy.py         # Safety policies
│   ├── parser.py         # Revise script parser
│   ├── validator.py      # Validation logic
│   ├── executor.py       # Command execution
│   ├── export.py         # Task export/selection
│   ├── uda.py            # UDA operations
│   └── llm.py            # LLM integration
├── tests/                # Test suite
├── pyproject.toml        # Project metadata
└── README.md             # This file
```

## Architecture

TaskMan follows a clear separation of concerns:

1. **Taskdantic** (dependency):
   - Pydantic models for tasks
   - UDA discovery and registry
   - Taskwarrior data parsing

2. **TaskMan** (this project):
   - CLI and user workflows
   - Safety policies and validation
   - LLM orchestration
   - Revise script parsing and execution

## CLI Reference

### `taskman sync-udas`

Sync UDA definitions to taskrc configuration.

```bash
taskman sync-udas [OPTIONS]

Options:
  -m, --model TEXT      Python module paths for UDA discovery
  -o, --output PATH     Output path (default: ~/.taskrc-udas)
  --example             Use example UDAs
```

### `taskman analyze`

Analyze a task using LLM.

```bash
taskman analyze SELECTOR [OPTIONS]

Arguments:
  SELECTOR              Task selector (id, uuid, or filter)

Options:
  -m, --mode TEXT       Policy mode: safe or power [default: safe]
  --show-prompt         Show LLM prompt
```

### `taskman revise`

Revise a task with LLM suggestions.

```bash
taskman revise SELECTOR [OPTIONS]

Arguments:
  SELECTOR              Task selector (id, uuid)

Options:
  -m, --mode TEXT       Policy mode: safe or power [default: safe]
  --show-prompt         Show LLM prompt
  --dry-run             Don't execute, just preview
  --skip-editor         Skip editor review (dangerous!)
```

### `taskman batch-analyze-cmd`

Batch analyze multiple tasks.

```bash
taskman batch-analyze-cmd [FILTER] [OPTIONS]

Arguments:
  FILTER                Taskwarrior filter [default: status:pending]

Options:
  -m, --mode TEXT       Policy mode
  --show-prompt         Show LLM prompt
```

## Contributing

Contributions welcome! Please:

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Ensure tests pass: `pytest`
5. Check types: `mypy src/taskman`
6. Lint: `ruff check src/taskman`

## License

[Add your license here]

## Acknowledgments

- [Taskwarrior](https://taskwarrior.org/) - The underlying task management system
- [Taskdantic](https://github.com/Bullish-Design/taskdantic) - Pydantic models for Taskwarrior
- [llms](https://github.com/simonw/llm) - LLM CLI tool and library

## Roadmap

- [ ] Full Taskdantic UDA integration
- [ ] Complete LLM integration with `llms` library
- [ ] External context store (optional)
- [ ] Batch revise operations
- [ ] Improved prompt size management
- [ ] Plugin system for custom workflows
