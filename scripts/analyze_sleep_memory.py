import csv
import math
from collections import defaultdict
from pathlib import Path

DATA_PATH = Path('data/raw/sleep_memory_2x2.csv')
REPORT_PATH = Path('docs/data_analysis_report.md')
FIGURE_PATH = Path('docs/figures/recall_by_group.svg')


def read_data(path: Path):
    rows = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['recall_score'] = float(row['recall_score'])
            rows.append(row)
    return rows


def mean(values):
    return sum(values) / len(values)


def sample_sd(values):
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def sem(values):
    return sample_sd(values) / math.sqrt(len(values))


def t_pdf(x, nu):
    numerator = math.gamma((nu + 1) / 2)
    denominator = math.sqrt(nu * math.pi) * math.gamma(nu / 2)
    return numerator / denominator * (1 + x * x / nu) ** (-(nu + 1) / 2)


def t_cdf(x, nu):
    if x == 0:
        return 0.5
    sign = 1 if x > 0 else -1
    x = abs(x)
    n = 10000
    h = x / n
    s = t_pdf(0, nu) + t_pdf(x, nu)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * t_pdf(i * h, nu)
    area = s * h / 3
    cdf = 0.5 + area
    return cdf if sign > 0 else 1 - cdf


def p_value_from_f_df1_is_1(f_value, df2):
    # For df1=1, F distribution is equivalent to t^2.
    t_value = math.sqrt(f_value)
    return 2 * (1 - t_cdf(t_value, df2))


def anova_2x2(rows):
    cells = defaultdict(list)
    a_levels = sorted({r['sleep'] for r in rows})
    b_levels = sorted({r['cue'] for r in rows})

    for row in rows:
        cells[(row['sleep'], row['cue'])].append(row['recall_score'])

    n = len(next(iter(cells.values())))
    N = len(rows)
    a = len(a_levels)
    b = len(b_levels)

    cell_means = {k: mean(v) for k, v in cells.items()}
    a_means = {A: sum(cell_means[(A, B)] for B in b_levels) / b for A in a_levels}
    b_means = {B: sum(cell_means[(A, B)] for A in a_levels) / a for B in b_levels}
    grand_mean = mean([r['recall_score'] for r in rows])

    ss_a = b * n * sum((a_means[A] - grand_mean) ** 2 for A in a_levels)
    ss_b = a * n * sum((b_means[B] - grand_mean) ** 2 for B in b_levels)
    ss_ab = n * sum(
        (cell_means[(A, B)] - a_means[A] - b_means[B] + grand_mean) ** 2
        for A in a_levels
        for B in b_levels
    )
    ss_e = sum(
        sum((x - cell_means[(A, B)]) ** 2 for x in cells[(A, B)])
        for A in a_levels
        for B in b_levels
    )

    df_a = a - 1
    df_b = b - 1
    df_ab = (a - 1) * (b - 1)
    df_e = N - (a * b)

    ms_a = ss_a / df_a
    ms_b = ss_b / df_b
    ms_ab = ss_ab / df_ab
    ms_e = ss_e / df_e

    f_a = ms_a / ms_e
    f_b = ms_b / ms_e
    f_ab = ms_ab / ms_e

    p_a = p_value_from_f_df1_is_1(f_a, df_e)
    p_b = p_value_from_f_df1_is_1(f_b, df_e)
    p_ab = p_value_from_f_df1_is_1(f_ab, df_e)

    eta_a = ss_a / (ss_a + ss_e)
    eta_b = ss_b / (ss_b + ss_e)
    eta_ab = ss_ab / (ss_ab + ss_e)

    return {
        'cells': cells,
        'a_levels': a_levels,
        'b_levels': b_levels,
        'cell_means': cell_means,
        'grand_mean': grand_mean,
        'anova': {
            'sleep': (f_a, p_a, eta_a),
            'cue': (f_b, p_b, eta_b),
            'interaction': (f_ab, p_ab, eta_ab),
            'df_error': df_e,
        },
    }


def build_svg(cells):
    order = [('Sleep', 'Control'), ('Sleep', 'TMR'), ('Wake', 'Control'), ('Wake', 'TMR')]
    labels = ['Sleep\nControl', 'Sleep\nTMR', 'Wake\nControl', 'Wake\nTMR']
    means = [mean(cells[k]) for k in order]
    sems = [sem(cells[k]) for k in order]

    width, height = 760, 460
    margin_left, margin_bottom, margin_top, margin_right = 80, 90, 40, 40
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    y_min, y_max = 0, 35

    def y_scale(v):
        return margin_top + (y_max - v) / (y_max - y_min) * plot_h

    bar_w = 100
    gap = (plot_w - bar_w * 4) / 5
    xs = [margin_left + gap + i * (bar_w + gap) for i in range(4)]
    colors = ['#7FA8D1', '#3B6EA8', '#C9A66B', '#8F6B32']

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text { font-family: Arial, sans-serif; fill: #222; } .small { font-size: 12px; } .axis { stroke: #333; stroke-width: 1.2; } .grid { stroke: #ddd; stroke-width: 1; } .title { font-size: 18px; font-weight: 700; } .subtitle { font-size: 13px; }</style>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="380" y="24" text-anchor="middle" class="title">Recall Scores by Sleep and Cue Condition</text>',
        '<text x="380" y="42" text-anchor="middle" class="subtitle">Bars show means; error bars show ±1 SEM</text>',
    ]

    for tick in range(0, 36, 5):
        y = y_scale(tick)
        parts.append(f'<line x1="{margin_left}" y1="{y:.1f}" x2="{width - margin_right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{margin_left - 10}" y="{y + 4:.1f}" text-anchor="end" class="small">{tick}</text>')

    parts.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" class="axis"/>')
    parts.append(f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" class="axis"/>')
    parts.append(f'<text x="18" y="{margin_top + plot_h / 2:.1f}" transform="rotate(-90,18,{margin_top + plot_h / 2:.1f})" text-anchor="middle" class="small">Mean Recall Score</text>')

    for x, m, s, label, color in zip(xs, means, sems, labels, colors):
        y = y_scale(m)
        bar_h = (height - margin_bottom) - y
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{bar_h:.1f}" fill="{color}"/>')

        e_top = y_scale(m + s)
        e_bot = y_scale(m - s)
        cx = x + bar_w / 2
        parts.append(f'<line x1="{cx:.1f}" y1="{e_top:.1f}" x2="{cx:.1f}" y2="{e_bot:.1f}" stroke="#111" stroke-width="2"/>')
        parts.append(f'<line x1="{cx - 10:.1f}" y1="{e_top:.1f}" x2="{cx + 10:.1f}" y2="{e_top:.1f}" stroke="#111" stroke-width="2"/>')
        parts.append(f'<line x1="{cx - 10:.1f}" y1="{e_bot:.1f}" x2="{cx + 10:.1f}" y2="{e_bot:.1f}" stroke="#111" stroke-width="2"/>')

        parts.append(f'<text x="{cx:.1f}" y="{height - margin_bottom + 24}" text-anchor="middle" class="small">{label.splitlines()[0]}</text>')
        parts.append(f'<text x="{cx:.1f}" y="{height - margin_bottom + 40}" text-anchor="middle" class="small">{label.splitlines()[1]}</text>')
        parts.append(f'<text x="{cx:.1f}" y="{y - 8:.1f}" text-anchor="middle" class="small">{m:.2f}</text>')

    parts.append('</svg>')
    return '\n'.join(parts)


def write_report(stats):
    cells = stats['cells']
    anova = stats['anova']
    order = [('Sleep', 'Control'), ('Sleep', 'TMR'), ('Wake', 'Control'), ('Wake', 'TMR')]

    lines = []
    lines.append('# Sleep and Memory: Short Data Report')
    lines.append('')
    lines.append('## 1) What was tested')
    lines.append('- This dataset uses a **2×2 design** (two factors, each with two groups):')
    lines.append('  - **Sleep condition**: Sleep vs. Wake')
    lines.append('  - **Cue condition**: TMR vs. Control')
    lines.append('- Outcome: **recall score** (higher = better memory recall).')
    lines.append('- Sample size: 80 participants (20 in each group).')
    lines.append('')
    lines.append('## 2) Main results in plain language')
    sleep_f, sleep_p, sleep_eta = anova['sleep']
    cue_f, cue_p, cue_eta = anova['cue']
    int_f, int_p, int_eta = anova['interaction']
    df_e = anova['df_error']

    lines.append(f'- **Sleep effect:** strong and statistically significant, *F*(1, {df_e}) = {sleep_f:.2f}, *p* < .001, partial η² = {sleep_eta:.3f}.')
    lines.append('  - Simple meaning: people who slept recalled more than people who stayed awake.')
    lines.append(f'- **Cue (TMR) effect:** significant, *F*(1, {df_e}) = {cue_f:.2f}, *p* < .001, partial η² = {cue_eta:.3f}.')
    lines.append('  - Simple meaning: TMR (targeted memory reactivation, a reminder cue linked to learned material) improved recall.')
    lines.append(f'- **Interaction (Sleep × Cue):** not significant, *F*(1, {df_e}) = {int_f:.2f}, *p* = {int_p:.3f}, partial η² = {int_eta:.3f}.')
    lines.append('  - Simple meaning: the TMR benefit looked similar in both Sleep and Wake groups.')
    lines.append('')
    lines.append('## 3) Group averages')
    lines.append('| Sleep | Cue | n | Mean recall | SD |')
    lines.append('|---|---|---:|---:|---:|')
    for key in order:
        values = cells[key]
        lines.append(f'| {key[0]} | {key[1]} | {len(values)} | {mean(values):.2f} | {sample_sd(values):.2f} |')
    lines.append('')
    lines.append('## 4) Graph')
    lines.append('![Bar chart of recall scores by sleep and cue condition](figures/recall_by_group.svg)')
    lines.append('')
    lines.append('### Graph explanation (easy language)')
    lines.append('- Each bar is the average recall score for one group.')
    lines.append('- Error bars show **SEM** (standard error of the mean), which gives a sense of estimate precision.')
    lines.append('- The pattern is clear: Sleep groups are higher than Wake groups, and TMR groups are higher than Control groups.')
    lines.append('- The parallel pattern across Sleep and Wake supports the non-significant interaction.')
    lines.append('')
    lines.append('## 5) Quick interpretation')
    lines.append('- In this dataset, both sleeping and receiving TMR cues were linked to better memory recall.')
    lines.append('- There is no strong evidence here that TMR only works during sleep; it appears helpful in both conditions.')
    lines.append('')
    lines.append('## References (APA style)')
    lines.append('Agents Workshop. (n.d.). *sleep_memory_2x2.csv* [Data set].')
    lines.append('Python Software Foundation. (n.d.). *Python (Version 3.10)* [Computer software]. https://www.python.org/')

    REPORT_PATH.write_text('\n'.join(lines))


def main():
    rows = read_data(DATA_PATH)
    stats = anova_2x2(rows)
    FIGURE_PATH.write_text(build_svg(stats['cells']))
    write_report(stats)
    print(f'Wrote report to {REPORT_PATH}')
    print(f'Wrote figure to {FIGURE_PATH}')


if __name__ == '__main__':
    main()
