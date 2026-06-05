---
name: creative-image
description: Produce ad IMAGES with gpt-image-2 (best in-image text/layout) and nano-banana / nano-banana-pro (best photorealism, product compositing, character consistency) via the peninglab MCP. Covers prompt structure, static-ad frameworks, ad sizes/safe zones, product compositing, and batching. Use whenever generating image creatives for PeningBot/PeningLab.
---

# Creative — IMAGE generation (gpt-image-2 / nano-banana)

Generate via the **peninglab** MCP (`list_models` → `get_balance` → `generate_image`). Ask before spend > RM5.

## Fire-and-Poll (NEVER double-charge — mandatory)
A timeout does NOT mean failure — the job is still running on the server and is **already paid for**. So:
1. **Check state first.** Before calling `generate_image`, check `state.json` / `task_status.json` for this
   slot. **If a `task_id` already exists → call `get_status(task_id)`** to recover the asset. **Never** start a
   new generation when a `task_id` exists (that's the double-billing trap). This is the **Safety Lock**.
2. **Fire.** No `task_id` yet → call `generate_image`, immediately **log the returned `task_id`** to state.
3. **Ignore the timeout.** If the MCP/socket times out, take the `task_id` from the error trace as the source
   of truth and **poll `get_status(task_id)`** — do NOT retry the prompt.
4. **Parallel dispatch.** Trigger ~3–4 generations at once in one turn — they run concurrently on the server,
   so wall-clock = the slowest one, not the sum. Shrink the batch if it returns rate-limit/overload.
Decision rule per slot: *task_id exists? → `get_status`. No/failed? → `generate_image` + log new task_id.*

## Model choice
- **gpt-image-2** = best **in-image TEXT, headlines, layout, infographics, data viz, product-with-copy** ad
  creatives. Use for any static where words must render correctly.
- **nano-banana / nano-banana-pro** = best **photorealism, UGC-style, product compositing into a hand/scene,
  character/face consistency, editing/inpainting**. Use for realistic lifestyle/UGC stills.

## Prompt structure (both models)
`[subject + who they are] · [action/pose] · [setting] · [composition/shot] · [lighting] · [style/mood] ·
[on-image text, in quotes] · [aspect ratio] · [brand colour]`. Be concrete. Name a **light source + a texture**
for realism (e.g. "soft window light, slight skin texture, real-phone-photo look") to avoid the AI sheen.

## Getting TEXT right (gpt-image-2 strength)
- Put the exact words in **quotes**; keep headlines short; specify placement ("headline top-third, large bold").
- One headline + one sub max per image. Specify font vibe ("clean sans-serif"). Re-prompt if garbled — don't edit.

## Product / character consistency (nano-banana)
- Feed the **real product photo as a reference** ("make the woman hold THIS product, presenting to camera") —
  never let the model redraw the product/logo. Generate **1 image first**, then variations; **max 1 edit**
  then re-prompt fresh (Jordan/Andy). Reuse one AI actor across a batch (multiple faces "feels weird").

## Static-ad frameworks (what to actually make)
- **Identity/age hook:** "Saya owner kedai, 40-an…" with a relatable local face.
- **Progress timeline:** Day 1 / Day 3 / Day 7 (chat backlog → inbox zero).
- **Us-vs-them comparison** (manual reply vs PeningBot auto-reply).
- **Problem screenshot:** phone at 3am, flood of unread WhatsApp, red badges (proven concept — Andromeda notes).
- **Proof/social:** WhatsApp testimonial screenshot, "dibalas dalam 5 minit", specific numbers.
- **Polarising lifestyle + product** (stressed owner vs calm owner).
Make image versions of winning videos (statics scale efficiency). 15–20 distinct concepts per batch.

## Ad sizes & safe zones
- **1:1** 1080×1080 (feed) · **4:5** 1080×1350 (feed, most real estate) · **9:16** 1080×1920 (Reels/Stories).
- Upload both **square (feeds)** and **vertical (Reels/Stories)** — most impressions are vertical.
- Keep headline text in the **safe zone** (away from top/bottom ~14% for 9:16 to dodge UI overlap).

## Diversity rule (Andromeda)
Every static must be a **distinct entity** — different concept + different copy, not a colour swap (see
`creative-andromeda`). Avoid AI-obvious renders; mix in real local photography where possible.
