"""Shared matplotlib style for the t2d-patient-subtyping project.

Centralizes color palette, rcParams, and custom colormaps so all
notebooks produce visually consistent plots without repeating
configuration. Hex values aligned to the shared design system
(design.md); roles map 1:1 to the project's original color palette.
"""

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns

# Project color palette (roles match the original palette;
# hex values aligned to design.md tokens)
COLOR_ACCENT = "#E64A19"   # highlights, reference lines, primary series
COLOR_BLUE = "#A3C9F1"     # secondary series, contrast
COLOR_DARK = "#1A1A1A"     # text, axes, structural elements
COLOR_BG = "#F7F9FA"       # plot/figure background
COLOR_GRAY = "#A0A0A0"     # muted/tertiary elements, gridlines


def set_project_style():
    """Apply a shared matplotlib/seaborn global style"""
    sns.set_style('ticks')
    plt.rcParams.update({
        "figure.figsize": (8, 5),
        "figure.facecolor": COLOR_BG,
        "axes.facecolor": COLOR_BG,
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.titleweight": "bold",
        "axes.labelweight": "bold",
        "axes.edgecolor": COLOR_DARK,
        "axes.labelcolor": COLOR_DARK,
        "text.color": COLOR_DARK,
        "xtick.color": COLOR_DARK,
        "ytick.color": COLOR_DARK,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


# --- Custom colormaps for heatmaps -----------------------------------------

# Sequential / monochromatic: black -> accent
# Use for single-direction intensity (e.g., missingness, counts, density)
_cmap_mono = mcolors.LinearSegmentedColormap.from_list(
    "project_mono", [COLOR_DARK, COLOR_ACCENT]
)
plt.colormaps.register(cmap=_cmap_mono, force=True)

# Diverging: blue -> white -> accent
# White center reads as "neutral / no signal" (standard for diverging
# maps like correlation matrices, where the midpoint = 0). A dark
# center would visually compete with the endpoints instead of receding.
_cmap_diverging = mcolors.LinearSegmentedColormap.from_list(
    "project_diverging", [COLOR_BLUE, "#FFFFFF", COLOR_ACCENT]
)
plt.colormaps.register(cmap=_cmap_diverging, force=True)