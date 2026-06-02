---
name: meta-bleed-check
description: Detect money-losing ad sets/ads (high spend, no conversions / CPA above target) so they can be paused. Use for daily/weekly spend hygiene.
---
# Meta Ads — Bleed Check
1. Pull active ad sets/ads with insights (spend, results, CPA, ROAS) over the chosen window (default last 7 days).
2. Flag any with spend >= a meaningful threshold AND (0 conversions OR CPA > target OR ROAS < breakeven).
3. Rank by wasted spend descending.
4. Recommend pause/keep per item with the reason; on approval, pause the flagged ones via `meta_ads`.
