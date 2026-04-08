# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.0.0",
#     "marimo>=0.22.5",
#     "matplotlib==3.10.8",
#     "numpy==2.4.4",
#     "pandas==3.0.2",
#     "upsetplot==0.9.0",
# ]
# ///

import marimo

__generated_with = "0.22.5"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Imports\n\nWe import the core libraries needed for data loading, transformation, and visualization.
    """)
    return


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import re
    from pathlib import Path

    return Path, alt, mo, pd, re


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Load the dataset\n\nWe read the IRED Novartis CSV into a pandas DataFrame for analysis.
    """)
    return


@app.cell(hide_code=True)
def _(Path, pd):
    data_path = Path('data/ired-novartis/cs1c02786_si_002.csv')
    df_raw = pd.read_csv(data_path)
    df_raw.shape
    return (df_raw,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Filter single point mutations\n\nThe mutation column contains both single point mutations (e.g., A111C) and multi-point mutations separated by semicolons. We filter for single point mutations only, then parse each mutation into its wildtype residue, position, and mutant residue.
    """)
    return


@app.cell(hide_code=True)
def _(df_raw, pd, re):
    mutation_pattern = re.compile(r'^([A-Z])(\d+)([A-Z])$')

    def parse_mutation(mutation_str):
        if not isinstance(mutation_str, str):
            return None, None, None
        match = mutation_pattern.match(mutation_str)
        if match:
            return match.group(1), int(match.group(2)), match.group(3)
        return None, None, None

    df_single = df_raw[~df_raw['mutation'].str.contains(';', na=False)].copy()
    df_single[['wildtype', 'position', 'mutant']] = df_single['mutation'].apply(
        lambda m: pd.Series(parse_mutation(m))
    )
    df_single = df_single.dropna(subset=['position'])
    df_single['position'] = df_single['position'].astype(int)
    df_single.shape
    return (df_single,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Heatmap of single point mutations\n\nWe construct a heatmap with position on the x-axis, mutant residue on the y-axis, and the mean activity value as the color. This gives us an at-a-glance view of which positions and substitutions yield the highest activity.
    """)
    return


@app.cell(hide_code=True)
def _(alt, df_single):
    heatmap_data = df_single[['position', 'mutant', 'mean']].copy()
    heatmap_chart = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X('position:O', title='Position'),
        y=alt.Y('mutant:O', title='Mutant Residue', sort=alt.SortField('mutant')),
        color=alt.Color('mean:Q', title='Mean Activity', scale=alt.Scale(scheme='viridis')),
        tooltip=['position:O', 'mutant:O', 'mean:Q']
    ).properties(
        width=1200,
        height=400,
        title='Single Point Mutation Activity Heatmap'
    )
    heatmap_chart
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Rank order by average mean\n\nWe group by position and compute the average mean activity across all mutant residues at each position. Positions are sorted from highest to lowest average, revealing which positions are most consistently active regardless of the specific substitution.
    """)
    return


@app.cell(hide_code=True)
def _(df_single):
    pos_avg_mean = df_single.groupby('position')['mean'].mean().sort_values(ascending=False).reset_index()
    pos_avg_mean.columns = ['position', 'avg_mean']
    pos_avg_mean
    return (pos_avg_mean,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Rank order by top mean\n\nWe group by position and take the maximum mean activity observed at each position. This highlights positions where at least one substitution achieves very high activity, even if other substitutions at that position are poor.
    """)
    return


@app.cell(hide_code=True)
def _(df_single):
    pos_top_mean = df_single.groupby('position')['mean'].max().sort_values(ascending=False).reset_index()
    pos_top_mean.columns = ['position', 'top_mean']
    pos_top_mean
    return (pos_top_mean,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## UpSet plot of top 20 positions\n\nWe compare the top 20 positions ranked by average mean versus the top 20 positions ranked by top mean. The UpSet plot visualizes the overlap between these two sets, showing which positions appear in both rankings (the intersection) versus those unique to each ranking criterion. Positions in the intersection are especially promising because they are both consistently active and capable of reaching high peak activity.
    """)
    return


@app.cell(hide_code=True)
def _(pd, pos_avg_mean, pos_top_mean):
    import matplotlib
    import matplotlib.pyplot as plt

    top20_avg_positions = set(pos_avg_mean.head(20)['position'])
    top20_top_positions = set(pos_top_mean.head(20)['position'])

    both = top20_avg_positions & top20_top_positions
    avg_only = top20_avg_positions - top20_top_positions
    top_only = top20_top_positions - top20_avg_positions

    set_data = pd.DataFrame({
        'Category': ['Both (Avg & Top)', 'Avg Mean Only', 'Top Mean Only'],
        'Count': [len(both), len(avg_only), len(top_only)],
        'Positions': [
            ', '.join(str(p) for p in sorted(both)),
            ', '.join(str(p) for p in sorted(avg_only)),
            ', '.join(str(p) for p in sorted(top_only))
        ]
    })
    set_data
    return avg_only, both, plt, top_only


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## UpSet-style visualization\n\nWe build a manual UpSet-style plot to visualize the overlap between the top 20 positions ranked by average mean and the top 20 positions ranked by top mean.
    """)
    return


@app.cell(hide_code=True)
def _(avg_only, both, plt, top_only):
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), gridspec_kw={'height_ratios': [1, 3]})

    categories = ['Both (Avg & Top)', 'Avg Mean Only', 'Top Mean Only']
    counts = [len(both), len(avg_only), len(top_only)]
    colors = ['#2ca02c', '#1f77b4', '#ff7f0e']

    ax_bar = axes[0]
    ax_bar.barh(categories, counts, color=colors)
    ax_bar.set_xlabel('Number of Positions')
    ax_bar.set_title('UpSet Plot: Top 20 Positions by Avg Mean vs Top Mean')
    for i, (c, v) in enumerate(zip(categories, counts)):
        ax_bar.text(v + 0.2, i, str(v), va='center', fontsize=12, fontweight='bold')

    ax_matrix = axes[1]
    ax_matrix.set_xlim(-0.5, len(categories) - 0.5)
    ax_matrix.set_ylim(-0.5, 1.5)
    sets = ['Top 20\nby Avg Mean', 'Top 20\nby Top Mean']
    ax_matrix.set_yticks([0, 1])
    ax_matrix.set_yticklabels(sets)
    ax_matrix.set_xticks(range(len(categories)))
    ax_matrix.set_xticklabels([])

    membership = [
        [True, True],
        [True, False],
        [False, True]
    ]
    for col_idx, members in enumerate(membership):
        for row_idx, is_member in enumerate(members):
            if is_member:
                ax_matrix.plot(col_idx, row_idx, 'o', markersize=15, color='black')
            else:
                ax_matrix.plot(col_idx, row_idx, 'o', markersize=15, color='lightgray', markeredgecolor='gray')
        if all(members):
            ax_matrix.plot([col_idx, col_idx], [0, 1], '-', color='black', linewidth=2)

    ax_matrix.spines['top'].set_visible(False)
    ax_matrix.spines['right'].set_visible(False)
    ax_matrix.spines['bottom'].set_visible(False)
    plt.tight_layout()
    fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Recommendation\n\nBased on the UpSet plot analysis, 11 positions appear in both the top 20 by average mean and the top 20 by top mean: **6, 154, 156, 159, 160, 212, 218, 220, 242, 243, and 247**. These are the strongest candidates for mutagenesis because they are both consistently active across substitutions and capable of reaching high peak activity.\n\n**Priority 1 — Highest confidence targets (in both rankings, top 5 by avg):** Position 243 ranks 1st by average mean (0.294) and 5th by top mean (0.501), making it the single best position to mutate. Position 156 ranks 2nd by average (0.276) and 14th by top (0.425), indicating broad robustness. Position 212 ranks 3rd by average (0.252) and 10th by top (0.467). Position 159 ranks 4th by average (0.250) and 13th by top (0.427). Position 242 ranks 5th by average (0.212) and 17th by top (0.419).\n\n**Priority 2 — High-ceiling targets (in both rankings, strong top mean):** Position 218 has the 5th highest top mean (0.519) while ranking 9th by average (0.191), suggesting a specific substitution achieves exceptional activity. Position 220 has the 2nd highest top mean overall (0.678) and ranks 15th by average (0.175), indicating a narrow but powerful substitution exists. Position 154 ranks 10th by average (0.189) and 3rd by top mean (0.583), another high-ceiling position.\n\n**Priority 3 — Worth exploring (top mean only):** Position 296 has the single highest top mean (0.712) but did not make the top 20 by average, meaning only a narrow set of substitutions work well there. If you can tolerate lower mutational robustness in exchange for maximum possible activity, position 296 is the top pick.\n\n**Summary:** For a first-round mutagenesis campaign, we recommend prioritizing positions **243, 156, 212, 159, and 242** for their combination of high average and high peak activity. Add **218, 220, and 154** as secondary targets if you want to capture high-ceiling substitutions. Reserve **296** for specialized exploration when maximum activity is worth the risk of poor performance with most substitutions.
    """)
    return


if __name__ == "__main__":
    app.run()
