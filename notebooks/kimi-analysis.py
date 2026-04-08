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
    import marimo as mo
    import seaborn as sns
    import matplotlib.pyplot as plt
    from pathlib import Path
    import numpy as np
    import re

    # For UpSet plot
    try:
        import upsetplot
        from upsetplot import UpSet
    except ImportError:
        upsetplot = None

    # Set plotting style
    sns.set_style('whitegrid')
    plt.rcParams['figure.figsize'] = (14, 8)
    return Path, mo, pd, plt, sns


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Imports

    We import the necessary libraries for data manipulation and visualization, including pandas for data handling, seaborn and matplotlib for plotting, and upsetplot for the set intersection visualization.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Data Loading

    We load the mutation data from the CSV file. Each row contains a mutation in the format `[OriginalAA][Position][MutantAA]` (e.g., A111C), along with activity measurements including the 'mean' column that we will use for our analysis.
    """)
    return


@app.cell(hide_code=True)
def _(Path, pd):
    data_path = Path("data/ired-novartis/cs1c02786_si_002.csv")
    df_raw = pd.read_csv(data_path)
    print(f"Total rows loaded: {len(df_raw)}")
    df_raw.head()
    return (df_raw,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Parse Single Point Mutations

    We filter the data to include only single point mutations (no multi-mutations with semicolons) and parse each mutation string to extract:
    - Original amino acid (first letter)
    - Position number (digits in the middle)
    - Mutant amino acid (last letter)

    This gives us the data structure needed for our heatmap visualization.
    """)
    return


@app.cell(hide_code=True)
def _(df_raw, pd):
    def parse_single_mutation(mutation_str):
        """Parse single point mutation like 'A111C' into (original, position, mutant)"""
        if pd.isna(mutation_str):
            return None, None, None
        mutation_str = str(mutation_str).strip()
        # Skip multi-mutations (contain semicolons)
        if ';' in mutation_str:
            return None, None, None
        # Must be format like A111C (letter, digits, letter)
        if len(mutation_str) < 3:
            return None, None, None
        original = mutation_str[0]
        mutant = mutation_str[-1]
        # Extract digits from middle
        middle = mutation_str[1:-1]
        if not middle.isdigit():
            return None, None, None
        position = int(middle)
        return original, position, mutant

    # Filter to single point mutations only
    single_mutation_mask = ~df_raw['mutation'].str.contains(';', na=False)
    df_parsed = df_raw[single_mutation_mask].copy()

    # Parse mutations
    parse_results = df_parsed['mutation'].apply(parse_single_mutation)
    df_parsed['original_aa'] = [p[0] for p in parse_results]
    df_parsed['position'] = [p[1] for p in parse_results]
    df_parsed['mutant_aa'] = [p[2] for p in parse_results]

    # Remove failed parses
    df_parsed = df_parsed.dropna(subset=['position', 'mutant_aa', 'mean'])

    print(f"Total rows in raw data: {len(df_raw)}")
    print(f"Single point mutations: {len(df_parsed)}")
    print(f"Multi-mutations filtered: {len(df_raw) - len(df_parsed)}")
    print(f"\nUnique positions: {df_parsed['position'].nunique()}")
    print(f"Position range: {df_parsed['position'].min()} - {df_parsed['position'].max()}")
    print(f"\nUnique mutant amino acids: {sorted(df_parsed['mutant_aa'].unique())}")
    print("\nSample data:")
    df_parsed[['mutation', 'position', 'mutant_aa', 'mean']].head(15)
    return (df_parsed,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Mutation Activity Heatmap

    We create a heatmap showing the mean activity values for each position (x-axis) and mutant amino acid (y-axis). Darker colors indicate higher activity values. This visualization helps identify which positions and mutations have the highest activity.
    """)
    return


@app.cell(hide_code=True)
def _(df_parsed, plt, sns):
    # Create pivot table for heatmap
    # For positions with multiple mutations, we'll show the mean value for each mutant-position pair
    heatmap_data = df_parsed.pivot_table(
        values='mean', 
        index='mutant_aa', 
        columns='position', 
        aggfunc='mean'
    )

    # Sort positions numerically
    heatmap_data = heatmap_data.reindex(sorted(heatmap_data.columns), axis=1)

    # Sort mutant amino acids alphabetically
    heatmap_data = heatmap_data.sort_index()

    # Create the heatmap
    fig, ax = plt.subplots(figsize=(24, 10))
    sns.heatmap(
        heatmap_data, 
        cmap='viridis', 
        cbar_kws={'label': 'Mean Activity'},
        xticklabels=50,  # Show fewer x-tick labels for readability
        ax=ax
    )
    ax.set_xlabel('Position')
    ax.set_ylabel('Mutant Amino Acid')
    ax.set_title('Mutation Activity Heatmap (Position × Mutant)')
    plt.tight_layout()
    fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Rank Order by Average Activity

    We rank positions by their average 'mean' activity value across all mutations at that position. This helps identify positions that generally show higher activity regardless of the specific mutation. These are positions where multiple mutations can yield good results.
    """)
    return


@app.cell(hide_code=True)
def _(df_parsed):
    # Calculate average mean activity per position
    position_avg = df_parsed.groupby('position')['mean'].mean().sort_values(ascending=False)

    print("Top 20 positions by average activity:")
    print("=" * 50)
    for i, (pos, val) in enumerate(position_avg.head(20).items(), 1):
        print(f"{i:2d}. Position {int(pos)}: {val:.6f}")
    
    position_avg
    return (position_avg,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Rank Order by Maximum Activity

    We rank positions by their maximum 'mean' activity value achieved by any single mutation at that position. This identifies positions where at least one specific mutation yields very high activity, even if other mutations at that position perform poorly.
    """)
    return


@app.cell(hide_code=True)
def _(df_parsed):
    # Calculate maximum mean activity per position
    position_top_values = df_parsed.groupby('position')['mean'].max().sort_values(ascending=False)

    print("Top 20 positions by maximum activity:")
    print("=" * 60)
    for idx, (pos_val, max_val) in enumerate(position_top_values.head(20).items(), 1):
        # Find which mutation achieved this max
        best_mut = df_parsed[(df_parsed['position'] == pos_val) & (df_parsed['mean'] == max_val)]['mutation'].iloc[0]
        print(f"{idx:2d}. Position {int(pos_val)}: {max_val:.6f} ({best_mut})")
    
    position_top_values
    return (position_top_values,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## UpSet Plot: Comparing Top 20 Rankings

    We visualize the overlap between the top 20 positions from each ranking method using an UpSet plot. This shows which positions appear in both rankings (the intersection) versus positions unique to each ranking method.
    """)
    return


@app.cell(hide_code=True)
def _(df_parsed, pd, plt, position_avg, position_top_values):
    from upsetplot import UpSet as UpSetPlot, from_memberships

    # Get top 20 from each ranking
    top20_avg_set = set(position_avg.head(20).index)
    top20_max_set = set(position_top_values.head(20).index)

    # Create membership data for UpSet plot
    all_positions_upset = sorted(top20_avg_set | top20_max_set)
    memberships_upset = []
    for pos_upset in all_positions_upset:
        member_of_upset = []
        if pos_upset in top20_avg_set:
            member_of_upset.append('Top 20 by Avg')
        if pos_upset in top20_max_set:
            member_of_upset.append('Top 20 by Max')
        memberships_upset.append(member_of_upset)

    # Count occurrences
    counts_upset = {}
    for m_upset in memberships_upset:
        key_upset = tuple(sorted(m_upset))
        counts_upset[key_upset] = counts_upset.get(key_upset, 0) + 1

    # Create the UpSet data
    index_upset = pd.MultiIndex.from_tuples([
        ('Top 20 by Avg' in k_upset, 'Top 20 by Max' in k_upset) 
        for k_upset in counts_upset.keys()
    ], names=['Top 20 by Avg', 'Top 20 by Max'])

    upset_data_series = pd.Series(list(counts_upset.values()), index=index_upset)

    # Sort by degree (number of categories)
    upset_data_series = upset_data_series.sort_index()

    # Create UpSet plot
    fig_upset = plt.figure(figsize=(10, 6))
    upset_plot = UpSetPlot(upset_data_series, subset_size='count', show_counts=True)
    upset_plot.plot(fig=fig_upset)
    plt.suptitle('Overlap Between Top 20 Positions by Average vs Maximum Activity', y=1.02)
    fig_upset

    # Print the intersection details
    print("Positions in BOTH Top 20 (Average AND Maximum):")
    print("=" * 55)
    both_sets = sorted(top20_avg_set & top20_max_set)
    for pos_both in both_sets:
        avg_val_both = position_avg[pos_both]
        max_val_both = position_top_values[pos_both]
        best_mut_both = df_parsed[(df_parsed['position'] == pos_both) & (df_parsed['mean'] == max_val_both)]['mutation'].iloc[0]
        print(f"  Position {int(pos_both)}: avg={avg_val_both:.4f}, max={max_val_both:.4f} ({best_mut_both})")

    print(f"\n\nPositions ONLY in Top 20 by Average: {sorted(top20_avg_set - top20_max_set)}")
    print(f"\nPositions ONLY in Top 20 by Maximum: {sorted(top20_max_set - top20_avg_set)}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Recommendations: Which Positions to Mutate

    Based on our analysis of single point mutations in the IRED Novartis dataset, we provide the following recommendations for protein engineering:

    ### Tier 1: Highest Priority Positions (Top Performers in Both Rankings)

    These **11 positions** appear in both the top 20 by average activity AND top 20 by maximum activity. They represent the most promising targets because:
    - Multiple mutations at these positions show good activity (high average)
    - At least one mutation achieves exceptional activity (high maximum)

    **Recommended positions:** 6, 154, 156, 159, 212, 218, 220, 242, 243, 247, 160

    **Best specific mutations to try first:**
    - Position 243: L243D (max=0.501) - highest maximum activity among shared positions
    - Position 220: S220T (max=0.678) - exceptional single mutation performance
    - Position 154: H154V (max=0.583) - strong single mutation
    - Position 212: I212K (max=0.467) - good performance
    - Position 218: A218L (max=0.519) - high activity mutant

    ### Tier 2: High Consistency Positions (Top 20 by Average Only)

    These **9 positions** have high average activity but didn't make the top 20 by single mutation maximum. They are valuable because:
    - Multiple mutations work well here (robustness)
    - Good for library-based screening approaches

    **Positions:** 114, 117, 118, 155, 188, 215, 216, 303, 304

    ### Tier 3: High Peak Performance Positions (Top 20 by Maximum Only)

    These **9 positions** have at least one exceptional mutation but lower average. They offer:
    - Potential for breakthrough activity if you find the right mutation
    - Higher risk but potentially higher reward

    **Notable positions:**
    - Position 296: A296I (max=0.712) - highest single mutation activity in entire dataset!
    - Position 175: V175K (max=0.539) - strong performer
    - Position 57: S57T (max=0.493) - good activity
    - Position 33: A33K (max=0.445) - solid choice

    ### Strategic Recommendations

    1. **Start with Tier 1 positions** (especially 243, 220, 154) for the best balance of reliability and performance
    2. **Include position 296** if you want to chase the highest possible activity, even though it has fewer validated mutations
    3. **Consider positions 156, 159, 160** as a cluster - they are adjacent and may interact
    4. **Use Tier 2 positions** for saturation mutagenesis libraries since multiple mutations work well there
    """)
    return


@app.cell(hide_code=True)
def _(df_parsed, position_avg, position_top_values):
    print("=" * 80)
    print("SUMMARY: RECOMMENDED POSITIONS TO MUTATE")
    print("=" * 80)

    # Tier 1: In both top 20s
    tier1_positions = sorted(set(position_avg.head(20).index) & set(position_top_values.head(20).index))
    print(f"\n🎯 TIER 1 - Both High Average AND High Maximum ({len(tier1_positions)} positions):")
    print("-" * 60)
    for pos in tier1_positions:
        avg_val = position_avg[pos]
        max_val = position_top_values[pos]
        best_mut = df_parsed[(df_parsed['position'] == pos) & (df_parsed['mean'] == max_val)]['mutation'].iloc[0]
        print(f"  Position {int(pos):3d}: avg={avg_val:.4f}, max={max_val:.4f} | Best: {best_mut}")

    # Tier 2: High average only
    tier2_positions = sorted(set(position_avg.head(20).index) - set(position_top_values.head(20).index))
    print(f"\n📊 TIER 2 - High Average Only ({len(tier2_positions)} positions):")
    print("-" * 60)
    for pos in tier2_positions:
        avg_val = position_avg[pos]
        print(f"  Position {int(pos):3d}: avg={avg_val:.4f}")

    # Tier 3: High maximum only
    tier3_positions = sorted(set(position_top_values.head(20).index) - set(position_avg.head(20).index))
    print(f"\n🚀 TIER 3 - High Maximum Only ({len(tier3_positions)} positions):")
    print("-" * 60)
    for pos in tier3_positions:
        max_val = position_top_values[pos]
        best_mut = df_parsed[(df_parsed['position'] == pos) & (df_parsed['mean'] == max_val)]['mutation'].iloc[0]
        print(f"  Position {int(pos):3d}: max={max_val:.4f} | Best: {best_mut}")

    print("\n" + "=" * 80)
    return


if __name__ == "__main__":
    app.run()
