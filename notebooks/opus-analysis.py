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
def _(mo):
    mo.md(r"""
    ## Imports

    We import the core libraries needed for data loading, visualization, and set analysis.
    """)
    return


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    from pathlib import Path
    from upsetplot import UpSet

    return Path, mo, pd, plt, sns


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Load the Dataset

    We read the IRED Novartis mutation screening CSV into a pandas DataFrame. This dataset contains mutation labels, activity means, and other assay metrics for an imine reductase (IRED) enzyme engineering campaign.
    """)
    return


@app.cell(hide_code=True)
def _(Path, pd):
    data_path = Path('data/ired-novartis/cs1c02786_si_002.csv')
    df_raw = pd.read_csv(data_path, index_col=0)
    df_raw.head(10)
    return (df_raw,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Identify Single Point Mutations

    The mutation column contains both single and multi-point mutations. Multi-point mutations are separated by semicolons (e.g. "A111T; S220T"). We filter to only single-point mutations, then parse out the wildtype residue, numeric position, and mutant residue from labels like "A111C" (Ala at position 111 mutated to Cys).
    """)
    return


@app.cell(hide_code=True)
def _(df_raw):
    # Filter to single-point mutations (no semicolons in the mutation string)
    # Also drop any rows with missing mutation values
    df_single = df_raw[~df_raw['mutation'].str.contains(';', na=True)].copy()
    df_single = df_single.dropna(subset=['mutation'])

    # Parse mutation components: wildtype letter, position, mutant letter
    df_single['wildtype'] = df_single['mutation'].str[0]
    df_single['position'] = df_single['mutation'].str.extract(r'(\d+)')[0].astype(int)
    df_single['mutant'] = df_single['mutation'].str[-1]

    print(f'Total rows: {len(df_raw):,}')
    print(f'Single-point mutations: {len(df_single):,}')
    print(f'Multi-point mutations: {len(df_raw) - len(df_single):,}')
    print(f'Unique positions: {df_single["position"].nunique()}')
    print(f'Unique mutant residues: {df_single["mutant"].nunique()}')
    df_single.head(10)
    return (df_single,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Heatmap of Single-Point Mutation Activity

    We pivot the single-point mutation data into a matrix with position on the x-axis and mutant amino acid on the y-axis, using the mean activity as the heatmap value. This gives us a comprehensive view of how each substitution at each position affects enzyme activity. Positions are sorted numerically and amino acids are sorted alphabetically.
    """)
    return


@app.cell(hide_code=True)
def _(df_single, plt, sns):
    # Pivot to create the heatmap matrix: position (x) vs mutant letter (y), value = mean
    heatmap_data = df_single.pivot_table(
        index='mutant',
        columns='position',
        values='mean',
        aggfunc='mean'
    )

    # Sort axes
    heatmap_data = heatmap_data.sort_index()  # alphabetical mutant letters
    heatmap_data = heatmap_data[sorted(heatmap_data.columns)]  # numeric positions

    fig_heatmap, ax_heatmap = plt.subplots(figsize=(40, 8))
    sns.heatmap(
        heatmap_data,
        cmap='YlOrRd',
        ax=ax_heatmap,
        xticklabels=True,
        yticklabels=True,
        cbar_kws={'label': 'Mean Activity'},
        linewidths=0,
    )
    ax_heatmap.set_xlabel('Position')
    ax_heatmap.set_ylabel('Mutant Amino Acid')
    ax_heatmap.set_title('Single-Point Mutation Activity Heatmap')
    ax_heatmap.tick_params(axis='x', rotation=90, labelsize=5)
    ax_heatmap.tick_params(axis='y', rotation=0, labelsize=8)
    plt.tight_layout()
    fig_heatmap
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Rank Positions by Activity

    We rank positions two ways to identify the most promising mutation sites. First, we rank by the average value of the mean column across all mutant residues at each position — this highlights positions that are broadly tolerant to or improved by substitution. Second, we rank by the top (maximum) value of the mean column at each position — this highlights positions where at least one substitution produced a strong effect. We take the top 20 from each ranking for comparison.
    """)
    return


@app.cell(hide_code=True)
def _(df_single):
    # Rank positions by average mean activity
    pos_avg_mean = df_single.groupby('position')['mean'].mean().sort_values(ascending=False)
    top20_avg = set(pos_avg_mean.head(20).index.tolist())

    # Rank positions by top (max) mean activity
    pos_max_mean = df_single.groupby('position')['mean'].max().sort_values(ascending=False)
    top20_max = set(pos_max_mean.head(20).index.tolist())

    print('Top 20 positions by AVERAGE mean:')
    print(pos_avg_mean.head(20).to_string())
    print()
    print('Top 20 positions by MAX mean:')
    print(pos_max_mean.head(20).to_string())
    print()
    print(f'Overlap: {len(top20_avg & top20_max)} positions appear in both top-20 lists')
    print(f'Positions in both: {sorted(top20_avg & top20_max)}')
    print(f'Only in avg top-20: {sorted(top20_avg - top20_max)}')
    print(f'Only in max top-20: {sorted(top20_max - top20_avg)}')
    return top20_avg, top20_max


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## UpSet Plot: Overlap of Top 20 Positions

    The UpSet plot visualizes the set relationships between the two ranking methods. Each position in the union of both top-20 lists is assigned membership in one or both sets. The intersection bars show how many positions are shared between rankings versus unique to each, helping us distinguish positions that are consistently high-performing (in both lists) from those that are high only by one metric.
    """)
    return


@app.cell(hide_code=True)
def _(plt, top20_avg, top20_max):
    from matplotlib.gridspec import GridSpec

    # Define the three subsets
    only_avg = sorted(top20_avg - top20_max)
    only_max = sorted(top20_max - top20_avg)
    both_sets = sorted(top20_avg & top20_max)

    subset_labels = ['Top 20 by Average\nonly', 'Both', 'Top 20 by Max\nonly']
    subset_sizes = [len(only_avg), len(both_sets), len(only_max)]
    subset_membership = [
        (True, False),   # avg only
        (True, True),    # both
        (False, True),   # max only
    ]
    set_names = ['Top 20 by Average', 'Top 20 by Max']
    set_totals = [len(top20_avg), len(top20_max)]

    fig_upset = plt.figure(figsize=(8, 6))
    gs = GridSpec(2, 1, height_ratios=[3, 1], hspace=0.05, figure=fig_upset)

    # Top: bar chart of intersection sizes
    ax_bar = fig_upset.add_subplot(gs[0])
    x_positions = range(len(subset_sizes))
    bars = ax_bar.bar(x_positions, subset_sizes, color=['#4878CF', '#6ACC65', '#D65F5F'], width=0.6)
    for bar_item, count in zip(bars, subset_sizes):
        ax_bar.text(bar_item.get_x() + bar_item.get_width()/2, bar_item.get_height() + 0.2,
                   str(count), ha='center', va='bottom', fontweight='bold', fontsize=12)
    ax_bar.set_ylabel('Intersection Size', fontsize=11)
    ax_bar.set_xticks([])
    ax_bar.set_xlim(-0.5, len(subset_sizes) - 0.5)
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)

    # Bottom: dot matrix showing set membership
    ax_matrix = fig_upset.add_subplot(gs[1])
    for col_idx, membership in enumerate(subset_membership):
        for row_idx, is_member in enumerate(membership):
            color = '#333333' if is_member else '#cccccc'
            ax_matrix.scatter(col_idx, row_idx, s=200, c=color, zorder=3)
        # Draw line connecting active dots
        active = [r for r, m in enumerate(membership) if m]
        if len(active) > 1:
            ax_matrix.plot([col_idx, col_idx], [min(active), max(active)],
                           c='#333333', linewidth=2, zorder=2)

    ax_matrix.set_yticks(range(len(set_names)))
    ax_matrix.set_yticklabels(set_names, fontsize=10)
    ax_matrix.set_xticks([])
    ax_matrix.set_xlim(-0.5, len(subset_sizes) - 0.5)
    ax_matrix.set_ylim(-0.5, len(set_names) - 0.5)
    ax_matrix.spines['top'].set_visible(False)
    ax_matrix.spines['right'].set_visible(False)
    ax_matrix.spines['bottom'].set_visible(False)

    fig_upset.suptitle('UpSet Plot: Top 20 Positions by Average vs Max Mean Activity',
                       fontsize=13, fontweight='bold')
    plt.tight_layout()
    fig_upset
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Recommendation: Priority Positions for Mutagenesis

    Based on the analysis above, we can classify positions into three tiers for prioritization in a focused mutagenesis campaign.

    ### Tier 1: High-confidence targets (in both top-20 lists)

    These 11 positions rank highly by both average and maximum mean activity, making them the strongest candidates for mutagenesis. A position that scores well on average across many substitutions suggests the site is generally tolerant to or improved by mutation, while a high maximum indicates at least one substitution produces a strong beneficial effect. The convergence of both signals gives the highest confidence that mutagenesis here will pay off.

    The standout positions in this tier are **position 220 (S)**, whose S220T mutation achieved the single highest mean activity (0.678) among all positions in both lists, **position 243 (L)**, which had the highest average across substitutions (0.294), and **position 154 (H)**, where H154V reached 0.583. Positions 156, 159, 212, and 218 also show strong performance on both metrics. These eleven positions should form the core of any combinatorial library design.

    ### Tier 2: Specialist targets (in max top-20 only)

    Nine positions appear only in the top-20-by-max ranking. These sites have one or a few exceptional mutations but lower average performance, meaning most substitutions at these positions are neutral or deleterious. **Position 296 (A)** stands out here: A296I achieved the highest single-mutant mean activity in the entire dataset (0.712), yet the position average is modest (0.140), suggesting that only specific substitutions work. Similarly, **position 175 (V175K, 0.539)** and **position 259 (A259T, 0.488)** show strong individual hits but low averages. These positions are worth including if you can target the specific beneficial substitutions, but are riskier in a saturation mutagenesis context because most variants will be inactive.

    ### Tier 3: Broadly tolerant positions (in avg top-20 only)

    Nine positions appear only in the top-20-by-average ranking. These positions tolerate diverse substitutions well (averages around 0.16-0.20) but lack a standout individual mutation (max values 0.27-0.35). They are useful for building combinatorial diversity — since many substitutions are viable, they contribute to library quality without requiring precise design. Positions 117, 155, and 118 are the strongest in this tier.

    ### Practical recommendation

    For a focused combinatorial library, prioritize the 11 Tier 1 positions as the backbone. If additional diversity is desired, add position 296 (targeting the A296I substitution specifically) and positions 175 and 259 with their identified beneficial mutations. For saturation mutagenesis at fewer sites, the top five positions to prioritize would be **220, 243, 156, 212, and 159**, which combine the strongest average and peak activity signals.
    """)
    return


if __name__ == "__main__":
    app.run()
