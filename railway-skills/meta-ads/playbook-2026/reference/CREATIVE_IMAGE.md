# skills/CREATIVE_IMAGE.md — static ad images (GPT-Image-2 + nano-banana)

## Route by task (use BOTH, pick per job)
| Task | Use | Why |
|---|---|---|
| On-image text (headline/offer/price), logos, UI labels | **gpt-image-2** | near-100% character accuracy; clean kerning |
| Photoreal product / UGC / portrait / lifestyle | **nano-banana** (Gemini 2.5 Flash Image / -pro) | best realism + micro-texture |
| Strict layout / brand-consistent series | **gpt-image-2** | follows brief, holds geometry |
| Edit a real photo / before-after / character consistency | **nano-banana** | reference blending, semantic edits |

Best pipeline: **photoreal base in nano-banana → add the text layer with a gpt-image-2 edit pass** ("add headline …, keep everything else identical").

## Prompt order (write a brief, not a tech spec)
`intended use → scene/background → subject → composition/lighting/color/style → on-image text (verbatim, quoted) → negatives`
- State intended use up front ("a Meta Stories ad", "IG feed ad").
- Subject: concrete + material ("navy tweed jacket", not "jacket").
- Composition: camera language + leave **negative space** where the headline goes ("rule-of-thirds, copy space top-left").
- Lighting: name the source ("soft window light from left", "golden-hour backlight").
- Color/mood: brand **hex codes** + a grade ("warm editorial").
- Photoreal cue: include "photorealistic", "real photograph", film grain, pores/fabric wear; a camera body for a look ("shot on Fujifilm").

## On-image text (make-or-break) — prefer gpt-image-2
- Put copy in quotes, ALL-CAPS, demand "EXACT, verbatim, no extra characters".
- Specify font/weight/color/size/placement/kerning. Use `quality:"high"` for small/dense text.
- Spell tricky brand words letter-by-letter. Keep copy SHORT.
- If text warps, do a dedicated text-only edit pass on gpt-image-2.

## Recipes (MY-localized — see COPYWRITING_MY.md; show the messy-inbox pain)
- **Phone-screen / WhatsApp pain (gpt-image-2):** photoreal hand holding a phone, screen shows a WhatsApp list FLOODED with unread "Berminat 😊 / ada stock? / harga?" chats + red badges, night bedroom blur, 9:16. On-image text: hook line in bold BM.
- **UGC seller testimonial (nano-banana):** candid front-camera selfie of an everyday MY seller (rotate Malay/Chinese/Indian) packing parcels at home, imperfect lighting, real skin texture, 9:16, no studio polish.
- **Before/After (nano-banana base + gpt-image-2 labels):** split image identical framing — left "9 missed chats / penat", right "auto-replied / customer happy"; labels "BEFORE"/"AFTER".
- **Bold promo (gpt-image-2):** solid brand-hex bg, huge "FREE 7 HARI" + subline + CTA pill "Cuba Sekarang", flat design, perfect legibility.
- **Product/app UI (gpt-image-2):** clean PeningBot dashboard/chat UI mockup on a phone, pixel-sharp legible labels.

## Sizes
Feed **1:1** (1024² or 2K) · Stories/Reels **9:16** (1024×1536 or 2K) · max-feed **4:5**. Always state exact pixels + ratio; keep text/subject in the central safe zone (top ~14% / bottom ~20% covered by UI). Generate at 2K for crisp text, downscale to spec.

## Avoid
Warped text (→gpt-image-2 + quoted/short) · "too-polished UGC" tell (→amateur phone selfie, imperfect light, real texture; vary the face across the batch) · hands/face artifacts (→close/medium framing, negatives "no extra fingers") · generic stock look (→named aesthetic + negatives) · drift across a series (→gpt-image-2, change one variable/iteration). Andromeda: every slot = a DIFFERENT concept (see ANDROMEDA.md).
