# marimo-pair-benchmark

Benchmark of LLM-assisted data science workflows using [marimo](https://marimo.io/) as the notebook environment.

The benchmark task is a re-analysis of the Novartis imine reductase (IRED) enzyme engineering dataset from:

> Ma et al., *ACS Catal.* 2021, 11(20), 12433–12445. DOI: 10.1021/acscatal.1c02786

Each notebook in this repo represents one model/agent run performing the same analysis from scratch, making it straightforward to compare output quality, code style, and analytical depth across models.

## Repository layout

- **`data/ired-novartis/`** — Source data files from the Ma et al. paper (see the folder README for citations and column descriptions).
- **`notebooks/`** — One marimo notebook per model run.

## Running a notebook

```bash
uv run marimo edit notebooks/<notebook>.py
```
