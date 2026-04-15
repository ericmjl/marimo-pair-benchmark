# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.22.5",
#     "matplotlib==3.10.8",
#     "pandas<3",
#     "seaborn==0.13.2",
#     "upsetplot==0.9.0",
# ]
# ///

import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _(mo):
    mo.md(r"""
    ## Imports

    We import the core libraries for reading the mutation data, reshaping it for analysis, and generating the heatmap and UpSet plots.
    """)
    return


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns
    from upsetplot import UpSet, from_memberships

    return Path, UpSet, from_memberships, mo, pd, plt, sns


@app.cell
def _(mo):
    mo.md(r"""
    ## Load the mutation dataset and isolate single substitutions

    We read the Novartis IRED mutation table from disk, parse mutation strings of the form `A111C`, and keep only rows that represent a single amino-acid substitution with a numeric `mean` value.
    """)
    return


@app.cell
def _(Path, pd):
    csv_path = Path("data/ired-novartis/cs1c02786_si_002.csv")
    raw_mutation_df = pd.read_csv(csv_path)
    mutation_pattern = r"^(?P<wildtype>[A-Z])(?P<position>\d+)(?P<mutant>[A-Z])$"
    mutation_parts_df = (
        raw_mutation_df["mutation"].astype(str).str.extract(mutation_pattern)
    )
    parsed_mutation_df = pd.concat([raw_mutation_df, mutation_parts_df], axis=1)
    single_point_mutation_df = parsed_mutation_df.dropna(
        subset=["wildtype", "position", "mutant"]
    ).copy()
    single_point_mutation_df["position"] = single_point_mutation_df[
        "position"
    ].astype(int)
    single_point_mutation_df["mean"] = pd.to_numeric(
        single_point_mutation_df["mean"], errors="coerce"
    )
    single_point_mutation_df = single_point_mutation_df.dropna(subset=["mean"])
    single_point_mutation_df[
        ["mutation", "position", "wildtype", "mutant", "mean"]
    ].head()
    return (single_point_mutation_df,)


@app.cell
def _(mo):
    mo.md(r"""
    ## Heatmap of mutation effects by position and mutant residue

    The next cell pivots the single-point mutation table so each tile maps one position and mutant amino acid, with color representing the `mean` value.
    """)
    return


@app.cell
def _(plt, single_point_mutation_df, sns):
    heatmap_matrix_df = (
        single_point_mutation_df.pivot_table(
            index="mutant",
            columns="position",
            values="mean",
            aggfunc="mean",
        )
        .sort_index(axis=0)
        .sort_index(axis=1)
    )
    heatmap_fig, heatmap_ax = plt.subplots(figsize=(18, 7))
    sns.heatmap(
        heatmap_matrix_df,
        cmap="viridis",
        ax=heatmap_ax,
        cbar_kws={"label": "Mean activity"},
    )
    heatmap_ax.set_xlabel("Position")
    heatmap_ax.set_ylabel("Mutant amino acid")
    heatmap_ax.set_title("Single-point mutation heatmap (mean value)")
    heatmap_fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Rank positions using average and maximum mutation outcomes

    We compute two rankings over positions: one by average `mean` across all substitutions at a site, and one by the top `mean` achieved at that site.
    """)
    return


@app.cell
def _(mo, single_point_mutation_df):
    position_average_ranked = (
        single_point_mutation_df.groupby("position")["mean"]
        .mean()
        .sort_values(ascending=False)
    )
    position_top_ranked = (
        single_point_mutation_df.groupby("position")["mean"]
        .max()
        .sort_values(ascending=False)
    )
    top20_average_positions = set(position_average_ranked.head(20).index.tolist())
    top20_top_positions = set(position_top_ranked.head(20).index.tolist())
    top20_average_table = (
        position_average_ranked.head(20).rename("average_mean").to_frame()
    )
    top20_top_table = position_top_ranked.head(20).rename("top_mean").to_frame()
    mo.vstack(
        [
            mo.md("### Top 20 positions by average `mean`"),
            top20_average_table,
            mo.md("### Top 20 positions by top `mean`"),
            top20_top_table,
        ]
    )
    return top20_average_positions, top20_top_positions


@app.cell
def _(mo):
    mo.md(r"""
    ## UpSet plot of top-20 overlap

    This plot compares the top-20 position sets from the two ranking strategies and shows their overlap and differences.
    """)
    return


@app.cell
def _(
    UpSet,
    from_memberships,
    plt,
    top20_average_positions,
    top20_top_positions,
):
    combined_top_positions = sorted(top20_average_positions | top20_top_positions)
    position_memberships = [
        tuple(
            ranking_name
            for ranking_name, ranking_set in (
                ("Top 20 by average mean", top20_average_positions),
                ("Top 20 by top mean", top20_top_positions),
            )
            if position_value in ranking_set
        )
        for position_value in combined_top_positions
    ]
    upset_input = from_memberships(
        position_memberships, data=[1] * len(position_memberships)
    )
    upset_plot = UpSet(
        upset_input,
        subset_size="count",
        show_counts=False,
        sort_by="cardinality",
    )
    upset_plot.plot()
    upset_figure = plt.gcf()
    upset_figure.suptitle("Overlap of top-20 positions", y=1.02)
    upset_figure
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Position recommendations for follow-up mutagenesis

    We combine both rankings to prioritize robust positions (consistently strong across substitutions) and exploratory positions (high upside from at least one substitution).
    """)
    return


@app.cell
def _(mo, top20_average_positions, top20_top_positions):
    shared_priority_positions = sorted(
        top20_average_positions & top20_top_positions
    )
    average_only_positions = sorted(top20_average_positions - top20_top_positions)
    top_only_positions = sorted(top20_top_positions - top20_average_positions)
    priority_slice = shared_priority_positions[:10]
    recommendation_markdown = mo.md(
        f"""
    ### Recommended mutation positions

    The strongest first-pass targets are positions appearing in **both** top-20 lists, because they are good under both aggregate and best-case criteria.

    **Primary positions to mutate next (shared top performers):** `{priority_slice}`

    For exploratory sweeps, include positions that are only strong by best-case score (potentially high-upside but less consistent):

    **High-upside exploratory positions:** `{top_only_positions[:10]}`

    Positions that are only strong by average score can be used when you want reliable broad improvements:

    **Consistency-oriented positions:** `{average_only_positions[:10]}`
    """
    )
    recommendation_markdown
    return


if __name__ == "__main__":
    app.run()
