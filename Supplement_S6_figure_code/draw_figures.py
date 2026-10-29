#!/usr/bin/env python3
"""Deterministic vector drawings for the manuscript (no empirical computation).

Figure 1: question-specific comparisons of the audit procedure.
Figure 2: typed repair and independent verification for a constructed example.
Figure B.1: historical pairing audit (frozen aggregates only).

Style: sans-serif 7.5-8 pt at final size (drawn 5.4 in wide, scaled to
the 31 pc sn-jnl text width), flat boxes, one accent colour,
no slash-separated labels, no internal version codes.
Usage: python3 draw_figures.py OUTPUT_DIR
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

STYLE = {"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "font.size": 8,
         "pdf.fonttype": 42, "svg.hashsalt": "is-figures", "savefig.bbox": "tight",
         "savefig.pad_inches": 0.03}
INK, LINE, FILL = "#222222", "#555555", "#F3F3F3"
ACCENT, ACCENT_FILL = "#0072B2", "#E3EEF7"
WARN_FILL = "#FBE9DF"
W = 5.4


def canvas(height):
    fig = plt.figure(figsize=(W, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, height)
    ax.axis("off")
    return fig, ax


def box(ax, cx, cy, w, h, text, fill=FILL, edge=LINE, size=7.6, weight="normal"):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0,rounding_size=0.04",
                                linewidth=0.7, edgecolor=edge, facecolor=fill))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=size, color=INK,
            linespacing=1.3, fontweight=weight)


def arrow(ax, x0, y0, x1, y1, style="-|>"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle=style, lw=0.75, color=LINE,
                                shrinkA=0, shrinkB=0, mutation_scale=8))


def text(ax, x, y, s, size=7.6, color=INK, weight="normal", style="normal", ha="center"):
    ax.text(x, y, s, ha=ha, va="center", fontsize=size, color=color,
            fontweight=weight, fontstyle=style, linespacing=1.3)


def figure1(out):
    rows = [
        ("Event concordance", None,
         "Snapshot differences\nunder C and V", "Native event records,\nkept apart from the diff",
         "Concordant or discrepant. Undetermined without an event witness."),
        ("Correspondence sufficiency", None,
         "Labels and targets supported\nby all optimal CSV matches", "Labels and targets revealed\nby native identities",
         "Undetermined if supported labels or targets conflict."),
        ("Adapter compatibility", "Snapshots and cell coordinates held fixed",
         "Raw or direct\nvalue adapter", "Normalized native\nmaterialization path",
         "Agreement or discrepancy. Truth of the clean table stays unknown."),
        ("Name-to-variant correspondence", "Producer results kept as the native control",
         "Consumer file read under\na dataset name", "Every producer variant\nof the same name",
         "Matched variant, other variant, or undetermined provenance."),
        ("Reference conformance", None,
         "Complete D and typed R,\nindependently resolved to E′", "Observed G and certificate,\nreplayed to G′",
         "Invalid preconditions: refuse or reject success. Business truth stays unknown."),
    ]
    H = 6.15
    fig, ax = canvas(H)
    row_h = 1.18
    top = H - 0.18
    for i, (title, scope, left, right, outcome) in enumerate(rows):
        y0 = top - i * row_h
        text(ax, 0.08, y0 - 0.12, title, size=8, color=ACCENT, weight="bold", ha="left")
        if scope:
            text(ax, W - 0.08, y0 - 0.12, scope, size=7, color=LINE, style="italic", ha="right")
        cy = y0 - 0.55
        box(ax, 1.3, cy, 2.3, 0.52, left)
        box(ax, 4.1, cy, 2.3, 0.52, right)
        arrow(ax, 2.47, cy, 2.93, cy, style="<|-|>")
        text(ax, 2.7, cy + 0.15, "compare", size=6.8, color=LINE)
        text(ax, 2.7, cy - 0.43, outcome, size=7.2, color=INK, style="italic")
        if i < len(rows) - 1:
            ax.plot([0.08, W - 0.08], [y0 - row_h + 0.06] * 2, color="#D0D0D0", lw=0.5)
    fig.savefig(out / "Figure_1.pdf", metadata={"CreationDate": None})
    fig.savefig(out / "Figure_1.png", dpi=200)
    plt.close(fig)


def figure2(out):
    H = 5.15
    fig, ax = canvas(H)
    xa, xb, bw = 1.42, 3.98, 2.42
    box(ax, W / 2, H - 0.3, 5.1, 0.46,
        "Supplied snapshots D, R and G\nD declares [B1, B2]; the observed G is [B1, B1]",
        fill=ACCENT_FILL, edge=ACCENT)
    text(ax, xa - bw / 2, H - 0.8, "(a) Repair", size=8, weight="bold", ha="left")
    text(ax, xb - bw / 2, H - 0.8, "(b) Independent verifier", size=8, weight="bold", ha="left")
    arrow(ax, xa + 0.85, H - 0.53, xa + 0.85, H - 0.98)
    arrow(ax, xb + 0.85, H - 0.53, xb + 0.85, H - 0.98)
    y1, y2, y3 = H - 1.48, H - 2.62, H - 3.72
    box(ax, xa, y1, bw, 0.96, "Check types, identity, uniqueness\nand the completeness flag\npass: resolve E = [B1, B2]\nfail: refuse and keep G")
    box(ax, xb, y1, bw, 0.96, "Check types, identity, uniqueness\nand the completeness flag\npass: resolve E′ again\nfail: reject the success claim")
    arrow(ax, xa, y1 - 0.48, xa, y2 + 0.38)
    arrow(ax, xb, y1 - 0.48, xb, y2 + 0.38)
    box(ax, xa, y2, bw, 0.76, "Occurrence delta from G to E\nremove one B1, add B2,\npreserve one B1")
    box(ax, xb, y2, bw, 0.76, "Independent E′ = [B1, B2]\nno expected adjacency\naccepted from the caller")
    arrow(ax, xa, y2 - 0.38, xa, y3 + 0.48)
    arrow(ax, xb, y2 - 0.38, xb, y3 + 0.48)
    box(ax, xa, y3, bw, 0.96, "Output [B1, B2] with certificate\ndigests h(D, R) and h(sorted G)\nremoved, added and preserved\noccurrences",
        fill=ACCENT_FILL, edge=ACCENT)
    box(ax, xb, y3, bw, 0.96, "Check schema, rule and reason,\nboth digests, and delta and\noutput against E′\naccept only if every check passes",
        fill=ACCENT_FILL, edge=ACCENT)
    arrow(ax, xa + bw / 2, y3, xb - bw / 2, y3)
    text(ax, W / 2, 0.52, "B1 = (depends_on, metric:revenue, offset 1 month)", size=7.2, color=LINE)
    text(ax, W / 2, 0.28, "B2 = (depends_on, metric:revenue, offset 2 months)", size=7.2, color=LINE)
    fig.savefig(out / "Figure_2.pdf", metadata={"CreationDate": None})
    fig.savefig(out / "Figure_2.png", dpi=200)
    plt.close(fig)


def figureB1(out):
    H = 4.6
    fig, ax = canvas(H)
    text(ax, 0.08, H - 0.16, "(a) Archived construction: two separately generated runs", size=8, weight="bold", ha="left")
    xs = [0.66, 1.98, 3.3, 4.62]
    bw, bh = 1.12, 0.5
    for y, steps in [(H - 0.62, ["Initial seed s", "Build clean\nskeleton", "Draw legal\nslicer edges", "G_clean"]),
                     (H - 1.3, ["Initial seed s", "Build and inject,\nconsuming draws", "Draw legal\nslicer edges", "G_defective"])]:
        for k, (x, s) in enumerate(zip(xs, steps)):
            fill = WARN_FILL if "inject" in s else (ACCENT_FILL if k == 3 else FILL)
            label = s.replace("G_clean", "$G_{\\mathrm{clean}}$").replace("G_defective", "$G_{\\mathrm{defective}}$")
            box(ax, x, y, bw, bh, label, fill=fill, edge=LINE, size=7.3)
            if k < 3:
                arrow(ax, x + bw / 2, y, xs[k + 1] - bw / 2, y)
    text(ax, W / 2, H - 1.78, "Injection can shift the random state used for the later legal edges.", size=7.2, style="italic")
    text(ax, W / 2, H - 2.0, "170 of 383 tasks contain unrelated legal differences, totaling 175 edges.", size=7.2)
    text(ax, W / 2, H - 2.2, "146 tasks are not edge-injection targets. The two categories overlap.", size=7.2)
    ax.plot([0.08, W - 0.08], [H - 2.42] * 2, color="#D0D0D0", lw=0.5)
    text(ax, 0.08, H - 2.62, "(b) Corrected control: generate the legal variation once", size=8, weight="bold", ha="left")
    yc = H - 3.36
    box(ax, 0.95, yc, 1.6, 0.56, "Complete graph G,\nincluding legal edges", fill=FILL, size=7.3)
    box(ax, 2.55, yc, 1.1, 0.56, "Copy the\nsame G", fill=FILL, size=7.3)
    box(ax, 4.35, yc + 0.36, 1.6, 0.46, "Gold: G,\nno new draws", fill=ACCENT_FILL, edge=ACCENT, size=7.3)
    box(ax, 4.35, yc - 0.36, 1.6, 0.46, "Input: G mutated\nafter copying", fill=WARN_FILL, size=7.3)
    arrow(ax, 1.75, yc, 2.0, yc)
    arrow(ax, 3.1, yc + 0.05, 3.55, yc + 0.36)
    arrow(ax, 3.1, yc - 0.05, 3.55, yc - 0.36)
    text(ax, W / 2, 0.22, "81 graph pairs and 231 scoped metric-edge tasks", size=7.2)
    fig.savefig(out / "Figure_B1.pdf", metadata={"CreationDate": None})
    fig.savefig(out / "Figure_B1.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(STYLE)
    figure1(out)
    figure2(out)
    figureB1(out)
    print("written to", out)
