#!/usr/bin/env python3
"""Analyze sleep-memory data and generate short Markdown + PDF reports."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

DATA_PATH = Path("data/raw/sleep_memory_2x2.csv")
OUTPUT_PDF = Path("output/sleep_memory_report.pdf")
OUTPUT_MD = Path("reports/sleep_memory_report.md")


def mean(values):
    return sum(values) / len(values)


def sample_sd(values):
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def se(values):
    return sample_sd(values) / math.sqrt(len(values))


def format_float(x):
    return f"{x:.2f}"


def build_ascii_bar(label, value, min_v=20, max_v=31, width=26):
    clamped = max(min_v, min(max_v, value))
    n_blocks = int(round((clamped - min_v) / (max_v - min_v) * width))
    bar = "█" * n_blocks + "·" * (width - n_blocks)
    return f"{label:<16} |{bar}| {value:>5.2f}"


def load_rows(path: Path):
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "id": int(row["id"]),
                    "sleep": row["sleep"],
                    "cue": row["cue"],
                    "recall_score": float(row["recall_score"]),
                }
            )
    return rows


def analyze(rows):
    by_cell = defaultdict(list)
    for r in rows:
        by_cell[(r["sleep"], r["cue"])].append(r["recall_score"])

    cell_stats = {}
    for key, values in sorted(by_cell.items()):
        cell_stats[key] = {
            "n": len(values),
            "mean": mean(values),
            "sd": sample_sd(values),
            "se": se(values),
        }

    sleeps = sorted({r["sleep"] for r in rows})
    cues = sorted({r["cue"] for r in rows})

    sleep_means = {s: mean([r["recall_score"] for r in rows if r["sleep"] == s]) for s in sleeps}
    cue_means = {c: mean([r["recall_score"] for r in rows if r["cue"] == c]) for c in cues}
    grand_mean = mean([r["recall_score"] for r in rows])

    a = len(sleeps)
    b = len(cues)
    n = cell_stats[(sleeps[0], cues[0])]["n"]

    ss_total = sum((r["recall_score"] - grand_mean) ** 2 for r in rows)
    ss_sleep = b * n * sum((sleep_means[s] - grand_mean) ** 2 for s in sleeps)
    ss_cue = a * n * sum((cue_means[c] - grand_mean) ** 2 for c in cues)

    ss_interaction = 0.0
    for s in sleeps:
        for c in cues:
            ss_interaction += (
                cell_stats[(s, c)]["mean"] - sleep_means[s] - cue_means[c] + grand_mean
            ) ** 2
    ss_interaction *= n

    ss_error = ss_total - ss_sleep - ss_cue - ss_interaction
    df_error = len(rows) - (a * b)
    ms_error = ss_error / df_error

    f_sleep = ss_sleep / ms_error
    f_cue = ss_cue / ms_error
    f_interaction = ss_interaction / ms_error

    eta_sleep = ss_sleep / (ss_sleep + ss_error)
    eta_cue = ss_cue / (ss_cue + ss_error)
    eta_interaction = ss_interaction / (ss_interaction + ss_error)

    # simple mean differences for plain-language interpretation
    delta_sleep = sleep_means["Sleep"] - sleep_means["Wake"]
    delta_cue = cue_means["TMR"] - cue_means["Control"]

    return {
        "n_total": len(rows),
        "cell_stats": cell_stats,
        "sleep_means": sleep_means,
        "cue_means": cue_means,
        "grand_mean": grand_mean,
        "f_sleep": f_sleep,
        "f_cue": f_cue,
        "f_interaction": f_interaction,
        "eta_sleep": eta_sleep,
        "eta_cue": eta_cue,
        "eta_interaction": eta_interaction,
        "delta_sleep": delta_sleep,
        "delta_cue": delta_cue,
    }


def report_lines_for_pdf(stats):
    cs = stats["cell_stats"]
    sm = stats["sleep_means"]
    cm = stats["cue_means"]

    return [
        "Sleep and Memory Recall: Data Report",
        "",
        f"Sample: {stats['n_total']} participants, 2x2 design (Sleep/Wake x TMR/Control)",
        "Outcome: recall_score (higher = better recall)",
        "",
        "Main findings:",
        f"- Sleep mean = {format_float(sm['Sleep'])}; Wake mean = {format_float(sm['Wake'])}",
        f"- TMR mean = {format_float(cm['TMR'])}; Control mean = {format_float(cm['Control'])}",
        f"- Sleep advantage = {format_float(stats['delta_sleep'])} points",
        f"- TMR advantage = {format_float(stats['delta_cue'])} points",
        "",
        "Group means (M) and SD:",
        f"- Sleep + TMR: M={format_float(cs[('Sleep','TMR')]['mean'])}, SD={format_float(cs[('Sleep','TMR')]['sd'])}",
        f"- Sleep + Control: M={format_float(cs[('Sleep','Control')]['mean'])}, SD={format_float(cs[('Sleep','Control')]['sd'])}",
        f"- Wake + TMR: M={format_float(cs[('Wake','TMR')]['mean'])}, SD={format_float(cs[('Wake','TMR')]['sd'])}",
        f"- Wake + Control: M={format_float(cs[('Wake','Control')]['mean'])}, SD={format_float(cs[('Wake','Control')]['sd'])}",
        "",
        "Graph (ASCII bars; scale 20 to 31 points):",
        build_ascii_bar("Sleep + TMR", cs[("Sleep", "TMR")]["mean"]),
        build_ascii_bar("Sleep + Control", cs[("Sleep", "Control")]["mean"]),
        build_ascii_bar("Wake + TMR", cs[("Wake", "TMR")]["mean"]),
        build_ascii_bar("Wake + Control", cs[("Wake", "Control")]["mean"]),
        "",
        "Statistics (2x2 ANOVA decomposition):",
        f"- Sleep effect: F(1,76)={format_float(stats['f_sleep'])}, partial eta^2={format_float(stats['eta_sleep'])}",
        f"- Cue effect: F(1,76)={format_float(stats['f_cue'])}, partial eta^2={format_float(stats['eta_cue'])}",
        f"- Sleep x Cue interaction: F(1,76)={format_float(stats['f_interaction'])}, partial eta^2={format_float(stats['eta_interaction'])}",
        "",
        "Interpretation:",
        "- Sleep and TMR are both linked with higher recall scores.",
        "- Interaction is very small, so TMR appears helpful in both Sleep and Wake.",
        "",
        "References (APA 7th)",
        "Oudiette, D., & Paller, K. A. (2013). Upgrading the sleeping brain with targeted memory reactivation. Trends in Cognitive Sciences, 17(3), 142-149.",
        "Rasch, B., Buchel, C., Gais, S., & Born, J. (2007). Odor cues during slow-wave sleep prompt declarative memory consolidation. Science, 315(5817), 1426-1429.",
    ]


def markdown_report(stats):
    cs = stats["cell_stats"]
    sm = stats["sleep_means"]
    cm = stats["cue_means"]

    lines = [
        "# Sleep and Memory Recall Report",
        "",
        "## 1) Data overview",
        "- Source: `data/raw/sleep_memory_2x2.csv`",
        f"- Participants: **{stats['n_total']}**",
        "- Design: **2×2 factorial** (Sleep vs. Wake; TMR vs. Control)",
        "- Outcome: **recall_score** (higher = better memory)",
        "",
        "## 2) Key results (plain language)",
        f"- Sleep mean = **{format_float(sm['Sleep'])}**, Wake mean = **{format_float(sm['Wake'])}**.",
        f"- TMR mean = **{format_float(cm['TMR'])}**, Control mean = **{format_float(cm['Control'])}**.",
        f"- Sleep advantage = **{format_float(stats['delta_sleep'])} points**.",
        f"- TMR advantage = **{format_float(stats['delta_cue'])} points**.",
        "- Best-performing group: **Sleep + TMR**.",
        "",
        "## 3) Group summary table",
        "| Condition | n | Mean (M) | SD |",
        "|---|---:|---:|---:|",
        f"| Sleep + TMR | {cs[('Sleep','TMR')]['n']} | {format_float(cs[('Sleep','TMR')]['mean'])} | {format_float(cs[('Sleep','TMR')]['sd'])} |",
        f"| Sleep + Control | {cs[('Sleep','Control')]['n']} | {format_float(cs[('Sleep','Control')]['mean'])} | {format_float(cs[('Sleep','Control')]['sd'])} |",
        f"| Wake + TMR | {cs[('Wake','TMR')]['n']} | {format_float(cs[('Wake','TMR')]['mean'])} | {format_float(cs[('Wake','TMR')]['sd'])} |",
        f"| Wake + Control | {cs[('Wake','Control')]['n']} | {format_float(cs[('Wake','Control')]['mean'])} | {format_float(cs[('Wake','Control')]['sd'])} |",
        "",
        "## 4) Graph (mean recall by condition)",
        "Scale: left = 20 points, right = 31 points",
        "",
        "```text",
        build_ascii_bar("Sleep + TMR", cs[("Sleep", "TMR")]["mean"]),
        build_ascii_bar("Sleep + Control", cs[("Sleep", "Control")]["mean"]),
        build_ascii_bar("Wake + TMR", cs[("Wake", "TMR")]["mean"]),
        build_ascii_bar("Wake + Control", cs[("Wake", "Control")]["mean"]),
        "```",
        "",
        "### Graph explanation",
        "- Longer bars mean better average memory recall.",
        "- Sleep groups score higher than Wake groups.",
        "- In both Sleep and Wake groups, TMR scores higher than Control.",
        "",
        "## 5) Statistics (explained simply)",
        "- **F value**: how much real signal exists compared with random noise.",
        "- **Partial eta-squared (ηp²)**: effect size (how large the effect is).",
        "  - Rough guide: .01 = small, .06 = medium, .14 = large.",
        "",
        f"- Sleep effect: **F(1,76) = {format_float(stats['f_sleep'])}, ηp² = {format_float(stats['eta_sleep'])}**",
        f"- Cue effect: **F(1,76) = {format_float(stats['f_cue'])}, ηp² = {format_float(stats['eta_cue'])}**",
        f"- Sleep × Cue interaction: **F(1,76) = {format_float(stats['f_interaction'])}, ηp² = {format_float(stats['eta_interaction'])}**",
        "",
        "## 6) Conclusion",
        "This dataset shows that sleep and TMR are both associated with better memory recall. The interaction effect is near zero, suggesting TMR helps similarly in Sleep and Wake conditions.",
        "",
        "## References (APA 7th)",
        "Oudiette, D., & Paller, K. A. (2013). Upgrading the sleeping brain with targeted memory reactivation. *Trends in Cognitive Sciences, 17*(3), 142–149. https://doi.org/10.1016/j.tics.2013.01.006",
        "",
        "Rasch, B., Büchel, C., Gais, S., & Born, J. (2007). Odor cues during slow-wave sleep prompt declarative memory consolidation. *Science, 315*(5817), 1426–1429. https://doi.org/10.1126/science.1138581",
    ]
    return "\n".join(lines) + "\n"


def escape_pdf_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_simple_pdf(lines, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)

    content_lines = ["BT", "/F1 10 Tf", "50 790 Td", "12 TL"]
    first = True
    for line in lines:
        prefix = "" if first else "T* "
        content_lines.append(f"{prefix}({escape_pdf_text(line)}) Tj")
        first = False
    content_lines.append("ET")

    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Courier >> endobj\n",
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode("ascii") + stream + b"\nendstream endobj\n",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii")
    )
    out_path.write_bytes(pdf)


def main():
    rows = load_rows(DATA_PATH)
    stats = analyze(rows)

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(markdown_report(stats), encoding="utf-8")

    pdf_lines = report_lines_for_pdf(stats)
    write_simple_pdf(pdf_lines, OUTPUT_PDF)

    print(f"Wrote {OUTPUT_MD}")
    print(f"Wrote {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
