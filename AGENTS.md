# AGENTS.md

Coding agent instructions for the marimo-pair-benchmark repository.

## Cell Structure Convention

Every notebook follows a strict two-part cell pattern: a markdown cell explaining intent, followed by a code cell that implements it.

### Markdown cells precede code cells

Before writing any code cell, always create a markdown cell that explains what the next code cell does and why. This produces a readable narrative throughout the notebook. Use `mo.md(...)` for markdown cells:

```python
async with cm.get_context() as ctx:
    ctx.create_cell("mo.md(r'## Load the dataset\\n\\nWe read the IRED Novartis CSV into a pandas DataFrame for analysis.')")
```

Then create the corresponding code cell. Never write a code cell without a preceding markdown cell.

### Imports live in their own cell

Imports must be isolated in a dedicated cell, separate from any computation or logic. The pattern is:

1. A markdown cell explaining what libraries we are importing and why.
2. A code cell containing only import statements.

```python
async with cm.get_context() as ctx:
    ctx.create_cell("mo.md(r'## Imports\\n\\nWe import the core libraries needed for data loading and visualization.')")
    ctx.create_cell("import pandas as pd\nimport marimo as mo")
```

Do not mix imports with data loading, transformations, plotting, or any other logic. Each code cell should do one thing. If new imports are needed later in the notebook, create a new markdown-plus-import cell pair at that point.

## Always Run Cells After Creation

Every cell must be executed immediately after it is created so that errors surface right away. Use `ctx.run_cell(cid)` after every `ctx.create_cell(...)` call. Never batch cell creation without running — catch problems early while the context is still fresh.

## Variable Rules

- Never redefine a variable across cells. This includes loop variables. Each variable name must be defined by exactly one cell. If you need a similar concept, use a distinct name (e.g., `df_raw` and `df_cleaned` instead of reusing `df`).

## Prose Style

- Write narrative prose in markdown cells, not bullet-point lists.
- Every code cell gets a markdown cell before it — no exceptions.

## Data Location

Source data lives in `data/ired-novartis/`. Use `pathlib.Path` for all file paths, never `os.path`.
