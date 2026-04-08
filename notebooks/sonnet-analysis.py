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
    # Sonnet Analysis: IRED Novartis Single Point Mutation Analysis

    This notebook analyses the single-point mutation fitness data from the IRED Novartis dataset (cs1c02786_si_002.csv). We identify which residue positions and substitutions are associated with high activity, visualise the landscape as a heatmap, compare two position-ranking strategies, and conclude with actionable mutation recommendations.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Imports

    We import the core libraries needed for data loading, parsing, visualisation, and the UpSet plot. `pathlib.Path` is used throughout for all file paths.
    """)
    return


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import numpy as np
    import upsetplot
    from pathlib import Path

    return Path, mo, np, pd, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Load the Dataset

    We read the IRED Novartis CSV into a pandas DataFrame. The dataset contains 11,305 rows representing both single-point mutations (e.g. `A111C`) and multi-mutation variants (e.g. `P22A; D125N; L173M; T207S; H230L`). The `mean` column captures the activity (fitness) score for each variant.
    """)
    return


@app.cell(hide_code=True)
def _(Path, pd):
    data_path = Path("data/ired-novartis/cs1c02786_si_002.csv")
    df_raw = pd.read_csv(data_path)
    df_raw
    return (df_raw,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Filter Single Point Mutations

    We keep only rows where the mutation string matches the pattern `[WT amino acid][position][mutant amino acid]` — a single letter, one or more digits, and a single letter. From these we parse the wild-type residue, the position number, and the mutant amino acid into separate columns. This leaves us with 4,720 single-point mutation records across 303 distinct positions and 20 amino acid substitutions.
    """)
    return


@app.cell(hide_code=True)
def _(df_raw):
    single_point_pattern = r"^([A-Z])(\d+)([A-Z])$"
    df_single = df_raw[df_raw["mutation"].str.match(single_point_pattern)].copy()
    df_single["wt_aa"] = df_single["mutation"].str.extract(r"^([A-Z])\d+[A-Z]$")
    df_single["position"] = df_single["mutation"].str.extract(r"^[A-Z](\d+)[A-Z]$").astype(int)
    df_single["mutant_aa"] = df_single["mutation"].str.extract(r"^[A-Z]\d+([A-Z])$")
    df_single = df_single.reset_index(drop=True)
    df_single[["mutation", "wt_aa", "position", "mutant_aa", "mean"]].head(10)
    return (df_single,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Mutation Landscape Heatmap

    We pivot the single-point data into a 2-D matrix with sequence position on the x-axis and the mutant amino acid on the y-axis. Each cell is filled with the `mean` activity score for that substitution, or left as NaN when the combination was not measured. The heatmap provides an immediate visual survey of the entire mutation landscape: warm colours indicate high activity, cool colours indicate low activity.
    """)
    return


@app.cell(hide_code=True)
def _(df_single, plt):
    heatmap_pivot = df_single.pivot_table(
        index="mutant_aa", columns="position", values="mean", aggfunc="mean"
    )

    amino_acid_order = list("ACDEFGHIKLMNPQRSTVWY")
    heatmap_pivot = heatmap_pivot.reindex(amino_acid_order)

    fig_heatmap, ax_heatmap = plt.subplots(figsize=(30, 6))
    im = ax_heatmap.imshow(
        heatmap_pivot.values,
        aspect="auto",
        cmap="viridis",
        interpolation="nearest",
        vmin=0,
    )
    plt.colorbar(im, ax=ax_heatmap, label="Mean activity score")
    ax_heatmap.set_yticks(range(len(heatmap_pivot.index)))
    ax_heatmap.set_yticklabels(heatmap_pivot.index, fontsize=8)
    ax_heatmap.set_xticks(range(len(heatmap_pivot.columns)))
    ax_heatmap.set_xticklabels(heatmap_pivot.columns.tolist(), rotation=90, fontsize=5)
    ax_heatmap.set_xlabel("Sequence position")
    ax_heatmap.set_ylabel("Mutant amino acid")
    ax_heatmap.set_title("Single-point mutation landscape — mean activity score")
    fig_heatmap.tight_layout()
    fig_heatmap
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Ranking Positions by Activity

    Two complementary strategies are used to prioritise positions for follow-up mutagenesis.

    The first strategy ranks positions by their **average** `mean` score across all measured substitutions at that position. This rewards positions that are broadly tolerant of mutation — many different amino acids all yield elevated activity.

    The second strategy ranks positions by their **maximum** (top) `mean` score observed at that position. This highlights positions where at least one highly beneficial substitution exists, even if other substitutions at the same site are neutral or deleterious.

    The top 20 positions from each ranking are stored for comparison in the UpSet plot that follows.
    """)
    return


@app.cell(hide_code=True)
def _(df_single):
    pos_avg_mean = (
        df_single.groupby("position")["mean"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"mean": "avg_mean"})
    )
    top20_by_avg = pos_avg_mean.head(20)
    top20_by_avg
    return (top20_by_avg,)


@app.cell(hide_code=True)
def _(df_single):
    pos_top_mean = (
        df_single.groupby("position")["mean"]
        .max()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"mean": "top_mean"})
    )
    top20_by_top = pos_top_mean.head(20)
    top20_by_top
    return (top20_by_top,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## UpSet Plot: Overlap Between the Two Top-20 Rankings

    An UpSet plot shows how the top-20 position sets from the two ranking strategies overlap. Each bar on the left shows the total size of each set (20 positions each). The connected dots in the matrix below indicate which combination of sets each intersection bar represents. Positions that appear in both rankings are the most robustly prioritised — they score high both on average fitness across all substitutions and on peak fitness for the single best substitution.
    """)
    return


@app.cell(hide_code=True)
def _(np, pd, plt, top20_by_avg, top20_by_top):
    import upsetplot.plotting as _up_plt
    import upsetplot.util as _up_util


    def _patched_plot_matrix(self, ax):
        """Patched version fixing nan edgecolor bug in upsetplot 0.9.0 with matplotlib>=3.10."""
        ax = self._reorient(ax)
        data = self.intersections
        n_cats = data.index.nlevels
        inclusion = data.index.to_frame().values
        styles_list = [
            [
                self.subset_styles[i]
                if inclusion[i, j]
                else {"facecolor": self._other_dots_color, "linewidth": 0}
                for j in range(n_cats)
            ]
            for i in range(len(data))
        ]
        styles_list = sum(styles_list, [])
        style_columns = {
            "facecolor": "facecolors",
            "edgecolor": "edgecolors",
            "linewidth": "linewidths",
            "linestyle": "linestyles",
            "hatch": "hatch",
        }
        styles_df = (
            pd.DataFrame(styles_list)
            .reindex(columns=style_columns.keys())
            .astype({"facecolor": "O", "edgecolor": "O", "linewidth": float, "linestyle": "O", "hatch": "O"})
        )
        styles_df["linewidth"] = styles_df["linewidth"].fillna(1)
        styles_df["facecolor"] = styles_df["facecolor"].fillna(self._facecolor)
        styles_df["edgecolor"] = styles_df["edgecolor"].fillna(styles_df["facecolor"])
        nan_mask = styles_df["edgecolor"].isna()
        if nan_mask.any():
            styles_df.loc[nan_mask, "edgecolor"] = styles_df.loc[nan_mask, "facecolor"]
        styles_df["linestyle"] = styles_df["linestyle"].fillna("solid")
        del styles_df["hatch"]
        x_coords = np.repeat(np.arange(len(data)), n_cats)
        y_coords = np.tile(np.arange(n_cats), len(data))
        s = (self._element_size * 0.35) ** 2 if self._element_size is not None else 200
        ax.scatter(
            *self._swapaxes(x_coords, y_coords),
            s=s,
            zorder=10,
            **styles_df.rename(columns=style_columns),
        )
        if self._with_lines:
            idx = np.flatnonzero(inclusion)
            line_data = (
                pd.Series(y_coords[idx], index=x_coords[idx])
                .groupby(level=0)
                .aggregate(["min", "max"])
            )
            colors_series = pd.Series(
                [style.get("edgecolor", style.get("facecolor", self._facecolor)) for style in self.subset_styles],
                name="color",
            )
            line_data = line_data.join(colors_series)
            ax.vlines(
                line_data.index.values, line_data["min"], line_data["max"], lw=2, colors=line_data["color"], zorder=5
            )
        tick_axis = ax.yaxis
        tick_axis.set_ticks(np.arange(n_cats))
        tick_axis.set_ticklabels(data.index.names, rotation=0 if self._horizontal else -90)
        ax.xaxis.set_visible(False)
        ax.tick_params(axis="both", which="both", length=0)
        if not self._horizontal:
            ax.yaxis.set_ticks_position("top")
        ax.set_frame_on(False)
        ax.set_xlim(-0.5, float(x_coords[-1]) + 0.5, auto=False)
        ax.grid(False)


    def _patched_label_sizes(self, ax, rects, where):
        """Patched version fixing 1-D numpy array text position bug with matplotlib>=3.10."""
        if not self._show_counts and not self._show_percentages:
            return
        count_fmt = "{:.0f}" if self._show_counts is True else self._show_counts
        if count_fmt and "{" not in count_fmt:
            count_fmt = _up_util.to_new_pos_format(count_fmt)
        pct_fmt = "{:.1%}" if self._show_percentages is True else self._show_percentages
        if count_fmt and pct_fmt:
            fmt = f"{count_fmt}\n({pct_fmt})" if where == "top" else f"{count_fmt} ({pct_fmt})"
            def make_args(val):
                return val, val / self.total
        elif count_fmt:
            fmt = count_fmt
            def make_args(val):
                return (val,)
        else:
            fmt = pct_fmt
            def make_args(val):
                return (val / self.total,)

        if where in ("right", "left"):
            margin = float(0.01 * abs(np.diff(ax.get_xlim())[0]))
            ha = "left" if where == "right" else "right"
            for rect in rects:
                width = float(rect.get_width() + rect.get_x())
                ax.text(
                    width + margin,
                    float(rect.get_y() + rect.get_height() * 0.5),
                    fmt.format(*make_args(width)),
                    ha=ha,
                    va="center",
                )
        elif where == "top":
            margin = float(0.01 * abs(np.diff(ax.get_ylim())[0]))
            for rect in rects:
                height = float(rect.get_height() + rect.get_y())
                ax.text(
                    float(rect.get_x() + rect.get_width() * 0.5),
                    height + margin,
                    fmt.format(*make_args(height)),
                    ha="center",
                    va="bottom",
                )
        else:
            raise NotImplementedError("unhandled where: %r" % where)


    _up_plt.UpSet.plot_matrix = _patched_plot_matrix
    _up_plt.UpSet._label_sizes = _patched_label_sizes

    from upsetplot import UpSet, from_contents

    avg_positions_set = set(top20_by_avg["position"].tolist())
    top_positions_set = set(top20_by_top["position"].tolist())

    upset_contents = {
        "Top-20 by average": avg_positions_set,
        "Top-20 by peak": top_positions_set,
    }
    upset_data = from_contents(upset_contents)

    fig_upset = plt.figure(figsize=(10, 6))
    UpSet(upset_data, subset_size="count", show_counts=True).plot(fig=fig_upset)
    fig_upset
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Mutation Recommendations

    The UpSet plot reveals that 11 positions appear in **both** top-20 lists — flagged by both the "broadly beneficial" (average) and "peak-hit" (maximum) criteria. These are the highest-confidence targets for mutagenesis because they are simultaneously tolerant of many substitutions and capable of yielding at least one highly active variant.

    The five strongest candidates from the consensus set, ranked by their peak activity score, are:

    **Position 220 (S220, peak mean 0.678, avg mean 0.175).** The S220T substitution alone reaches mean activity 0.678 — the second-highest single-mutation score in the entire dataset. The large difference between peak and average scores tells us the site is sharply selective: T is strongly preferred, whereas other substitutions are near-neutral. S220T should be the first mutation introduced into any improved variant.

    **Position 243 (L243, peak 0.501, avg 0.294).** This position has the highest *average* activity of all positions, meaning that many different amino acids are tolerated here and most of them improve activity. The top substitutions are L243D (0.501), L243T (0.496), and L243F (0.475). Any of these is a strong choice; if building a combinatorial library, this site is ideal because multiple substitutions are productive.

    **Position 247 (R247, peak 0.469, avg 0.196).** R247K (0.469), R247N (0.436), and R247S (0.396) all score well. The conservative K substitution preserves positive charge and has the highest score, suggesting an electrostatic role for this residue that can be fine-tuned.

    **Position 218 (A218, peak 0.519, avg 0.191).** A218L (0.519), A218M (0.434), and A218I (0.414) suggest the site accommodates larger hydrophobic side chains much better than the wild-type alanine. This is a classic buried-cavity substitution pattern.

    **Position 212 (I212, peak 0.467, avg 0.252).** I212K (0.467) and I212N (0.456) introduce polar/charged residues at what is presumably a surface-exposed position, suggesting a beneficial surface electrostatics contribution.

    **Practical design strategy.** Begin with the single-residue substitution S220T, which already delivers a large activity gain on its own. Layer in L243D or L243T next, as position 243 is broadly permissive and additive gains are plausible. Add A218L and I212K in subsequent rounds. Avoid combining too many changes at once — the dataset is single-point data and epistatic interactions could be negative. Positions that appear only in the peak-activity ranking (296, 175, 57, 26, 33, 177, 189, 259, 71) are worth a targeted follow-up screen but should not be prioritised over the consensus set in the initial campaign.
    """)
    return


if __name__ == "__main__":
    app.run()
