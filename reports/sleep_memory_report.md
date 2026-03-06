# Sleep and Memory Recall Report

## 1) Data overview
- Source: `data/raw/sleep_memory_2x2.csv`
- Participants: **80**
- Design: **2×2 factorial** (Sleep vs. Wake; TMR vs. Control)
- Outcome: **recall_score** (higher = better memory)

## 2) Key results (plain language)
- Sleep mean = **28.17**, Wake mean = **23.06**.
- TMR mean = **27.19**, Control mean = **24.04**.
- Sleep advantage = **5.11 points**.
- TMR advantage = **3.16 points**.
- Best-performing group: **Sleep + TMR**.

## 3) Group summary table
| Condition | n | Mean (M) | SD |
|---|---:|---:|---:|
| Sleep + TMR | 20 | 29.85 | 3.92 |
| Sleep + Control | 20 | 26.49 | 3.58 |
| Wake + TMR | 20 | 24.54 | 3.22 |
| Wake + Control | 20 | 21.58 | 3.36 |

## 4) Graph (mean recall by condition)
Scale: left = 20 points, right = 31 points

```text
Sleep + TMR      |███████████████████████···| 29.85
Sleep + Control  |███████████████···········| 26.49
Wake + TMR       |███████████···············| 24.54
Wake + Control   |████······················| 21.58
```

### Graph explanation
- Longer bars mean better average memory recall.
- Sleep groups score higher than Wake groups.
- In both Sleep and Wake groups, TMR scores higher than Control.

## 5) Statistics (explained simply)
- **F value**: how much real signal exists compared with random noise.
- **Partial eta-squared (ηp²)**: effect size (how large the effect is).
  - Rough guide: .01 = small, .06 = medium, .14 = large.

- Sleep effect: **F(1,76) = 42.01, ηp² = 0.36**
- Cue effect: **F(1,76) = 16.01, ηp² = 0.17**
- Sleep × Cue interaction: **F(1,76) = 0.07, ηp² = 0.00**

## 6) Conclusion
This dataset shows that sleep and TMR are both associated with better memory recall. The interaction effect is near zero, suggesting TMR helps similarly in Sleep and Wake conditions.

## References (APA 7th)
Oudiette, D., & Paller, K. A. (2013). Upgrading the sleeping brain with targeted memory reactivation. *Trends in Cognitive Sciences, 17*(3), 142–149. https://doi.org/10.1016/j.tics.2013.01.006

Rasch, B., Büchel, C., Gais, S., & Born, J. (2007). Odor cues during slow-wave sleep prompt declarative memory consolidation. *Science, 315*(5817), 1426–1429. https://doi.org/10.1126/science.1138581
