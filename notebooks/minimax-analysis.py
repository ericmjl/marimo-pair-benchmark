# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.22.5",
#     "matplotlib==3.10.8",
#     "numpy==2.4.4",
#     "pandas==3.0.2",
#     "seaborn==0.13.2",
#     "upsetplot==0.9.0",
# ]
# ///

import marimo

__generated_with = "0.22.5"
app = marimo.App()


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    from pathlib import Path
    import re

    data_path = Path("data/ired-novartis/cs1c02786_si_002.csv")
    df_raw = pd.read_csv(data_path)

    mutation_pattern = re.compile(r'^([A-Z])(\d+)([A-Z])$')

    def parse_mutation(mutation_str):
        if pd.isna(mutation_str):
            return None, None, None
        match = mutation_pattern.match(str(mutation_str))
        if match:
            return match.group(1), int(match.group(2)), match.group(3)
        return None, None, None

    df_raw[["original_aa", "position", "mutant_aa"]] = df_raw["mutation"].apply(
        lambda x: pd.Series(parse_mutation(x))
    )

    df_spm = df_raw.dropna(subset=["original_aa", "position", "mutant_aa"]).copy()
    df_spm["position"] = df_spm["position"].astype(int)

    print(f"Total mutations: {len(df_raw)}")
    print(f"Single point mutations parsed: {len(df_spm)}")
    print(f"Unique positions: {df_spm['position'].nunique()}")
    print(f"Unique mutant AAs: {sorted(df_spm['mutant_aa'].unique())}")
    return df_spm, plt, sns


@app.cell(hide_code=True)
def _(df_spm, plt, sns):
    df_heatmap = df_spm.pivot_table(
        index="mutant_aa", 
        columns="position", 
        values="mean", 
        aggfunc="mean"
    )

    plt.figure(figsize=(24, 10))
    sns.heatmap(
        df_heatmap, 
        cmap="viridis", 
        cbar_kws={"label": "Mean Value"},
        xticklabels=50
    )
    plt.xlabel("Position")
    plt.ylabel("Mutant Amino Acid")
    plt.title("Heatmap of Mean Values by Position and Mutant Amino Acid")
    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(df_spm):
    pos_avg = df_spm.groupby("position")["mean"].mean().sort_values(ascending=False)
    pos_top = df_spm.groupby("position")["mean"].max().sort_values(ascending=False)

    print("Top 20 positions by average mean value:")
    print(pos_avg.head(20))
    print()
    print("Top 20 positions by top mean value:")
    print(pos_top.head(20))
    return pos_avg, pos_top


@app.cell(hide_code=True)
def _(pos_avg, pos_top):
    from upsetplot import UpSet, from_memberships

    top20_avg = set(pos_avg.head(20).index)
    top20_top = set(pos_top.head(20).index)

    print(f"Top 20 by avg: {sorted(top20_avg)}")
    print(f"Top 20 by top: {sorted(top20_top)}")
    print(f"Overlap: {sorted(top20_avg & top20_top)}")
    print(f"Only in avg: {sorted(top20_avg - top20_top)}")
    print(f"Only in top: {sorted(top20_top - top20_avg)}")
    return top20_avg, top20_top


@app.cell(hide_code=True)
def _(plt, pos_avg, pos_top):
    from upsetplot import UpSet, from_memberships

    top20_avg_list = list(pos_avg.head(20).index)
    top20_top_list = list(pos_top.head(20).index)

    memberships = [
        ["Top20_by_Avg", "Top20_by_Max"],
    ]

    data = []
    for pos in top20_avg_list:
        cats = ["Top20_by_Avg"]
        if pos in top20_top_list:
            cats.append("Top20_by_Max")
        data.append(cats)

    upset_data = from_memberships(data)
    fig = plt.figure(figsize=(12, 8))
    upset = UpSet(upset_data, subset_size="count", show_counts=True, sort_by="cardinality")
    upset.plot(fig=fig)
    plt.suptitle("UpSet Plot: Overlap of Top 20 Positions (Avg vs Max)")
    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(df_spm, pos_avg, top20_avg, top20_top):
    overlap_positions = sorted(top20_avg & top20_top)
    print("=" * 70)
    print("RECOMMENDATION: Positions to Mutate")
    print("=" * 70)
    print()
    print("These 11 positions appear in BOTH top 20 by average AND top 20 by max,")
    print("making them the most robust targets for mutation:")
    print()
    print(f"  {overlap_positions}")
    print()
    print("Top 5 with highest average mean values:")
    for i, (pos, val) in enumerate(pos_avg.head(5).items()):
        top_mutant = df_spm[df_spm["position"] == pos].loc[df_spm[df_spm["position"] == pos]["mean"].idxmax(), "mutant_aa"]
        print(f"  {i+1}. Position {pos}: avg={val:.4f}, best_mutant={top_mutant}")
    print()
    print("=" * 70)
    return


if __name__ == "__main__":
    app.run()
