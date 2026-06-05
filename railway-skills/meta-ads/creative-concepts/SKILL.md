---
name: creative-concepts
description: The matching discipline — one concept = ONE angle expressed identically across visual + copy + website CTA, never produced independently. Holds the brand-specific starter concept matrices for PeningBot and PeningLab. Use by Copywriter + Image/Video Producers so every ad is a matched, brand-specific unit.
---

# Creative Concepts (copy ↔ visual ↔ CTA must MATCH)

The unit of work is the **concept**, not a loose asset. A concept = one angle carried identically through:
```
Persona + Awareness  →  ANGLE  →  HOOK
        ↓ (same angle, same words)
   Visual (gemini/gpt-image-2)  +  Copy (primary text + headline)  +  website CTA
```
If the hook says "Penat balas WhatsApp tengah malam?", the visual shows the 3am phone flood AND the page/CTA
continues that pain. **All match, or reject the concept.** Visual and copy are NEVER made independently — they
come from one `brief.json` slot (Copywriter writes copy + image/video prompt together).

## Rules
- **Brand-specific only** — never reuse a PeningBot concept for PeningLab (different product, audience, voice,
  visual identity). Read `_products/peningbot.md` / `_products/peninglab.md`.
- **One concept = a distinct Andromeda entity** (different concept + copy, not a colour swap).
- The 3-ads/ad-set unit = same concept/body, **only the first-3s visual hook varies** (see `creative-andromeda`).
- Video = 10s, ~20–25 words across 3 beats (hook/body/CTA), matched to the visual (see `creative-video`).

## PeningBot starter matrix (B2B SME owners — sell time saved + sales recovered)
| Concept (tool) | Matched hook | Awareness | CTA |
|---|---|---|---|
| 3am phone, 99+ unread WA *(gemini)* | "Customer tanya tengah malam, esok dah beli kat orang lain." | Problem | "Mula di peningbot.com" |
| Founder talking-head *(gemini)* | "Saya owner kedai — dulu balas 100 WA sorang-sorang…" | Solution | "Cuba plan RM35" |
| Before/after inbox *(gpt-image-2)* | "Inbox berderet → settle automatik." | Problem→Sol | "Mula sekarang" |
| Us-vs-them table *(gpt-image-2)* | "Balas lambat = customer lari." | Solution | "Daftar PeningBot" |
| WhatsApp testimonial shot *(gpt-image-2)* | "Dibalas 5 saat — sales naik." | Most-aware | "Mula di peningbot.com" |
| Offer card *(gpt-image-2)* | "Auto-reply 24/7. Dari RM35/bulan." | Most-aware | "Subscribe sekarang" |

## PeningLab starter matrix (TikTok Shop affiliates — sell cheap fast content volume)
| Concept (tool) | Matched hook | Awareness | CTA |
|---|---|---|---|
| Creator overwhelmed shooting *(gemini)* | "Bayar RM300 untuk 1 video je? Bos kau kaya, kau penat." | Problem | "Cuba di peninglab.com" |
| Screen-record: link → 10 videos *(gemini)* | "Paste link, dapat 10 video UGC dalam 3 minit." | Solution | "Subscribe Pro" |
| Before/after cost *(gpt-image-2)* | "BEFORE: 1 minggu, RM500. AFTER: 3 minit, RM4." | Solution | "Mula RM35" |
| Competitor volume *(gpt-image-2)* | "Kompetitor post 10 video sehari guna AI. Kau?" | Problem | "Cuba peninglab" |
| UGC result/affiliate earnings *(gemini)* | "Scale TikTok Shop jadi RM10k/bulan dengan AI." | Product | "Subscribe Pro" |
| Pricing/offer card *(gpt-image-2)* | "Pro RM100 = ~125 video. Bukan RM300 sebijik." | Most-aware | "Subscribe sekarang" |

Run 3 live per brand (one ad set, 3 hooks) + ~3 reserve; rotate weekly. Refresh angles from
`_shared/angles_<brand>` and the win→prompt loop. Visual identity per `_products` brand brief.
