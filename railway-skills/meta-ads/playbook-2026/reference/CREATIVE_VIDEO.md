# skills/CREATIVE_VIDEO.md — AI video ad creatives (Veo 3 / Gemini video)

## Hard constraints
- **Max 8s per generated clip** (4/6/8s). No native 10s/15s — build longer ads by **chaining clips** (8s hook + 6s payoff/CTA).
- Always **9:16 vertical, 1080p**. Keep faces in the upper-middle third (platform UI covers top/bottom). Every clip has an invisible SynthID watermark.

## Prompt structure
`[Cinematography: shot + camera move] + [Lens/focus] + [Subject (front-load identity)] + [ONE action] + [Context: location/time/light source] + [Style & ambiance] + [Audio + Dialogue] + [Format: 9:16, 1080p]`
- Name the **shot + camera movement** explicitly (handheld selfie, medium close-up, slow pan) or Veo invents motion.
- **One dominant action per clip** (multiple = physics breaks).
- Name a **light source** + **micro-texture** ("soft window light", "natural skin pores, fabric weave, no gloss") to kill the plastic AI look.
- Label audio: `Ambient noise:` / `SFX:` / dialogue.

## Dialogue / voiceover word count (critical)
Natural speech ≈ **2.5 words/sec (≈150 wpm)**. Punchy ad ≈ 3 wps; calm ≈ 2 wps.
| Duration | Natural | Punchy | Calm |
|---|---|---|---|
| 5s | ~12 words | ~15 | ~10 |
| **8s (max clip)** | **~20 words** | ~24 | ~16 |
| 10s | ~25 words | ~30 | ~20 |
| 15s | ~37 words | ~45 | ~30 |
**Rule: ~15–20 words for an 8s clip** (back to ~16 if you want a pre-speech pause). For 10–15s ads use 2 chained clips, each with its own ~16–20-word line. If lip-sync drifts → shorten the line + regenerate.
- Write dialogue as: `[Character] says: "exact line" (no subtitles).` — the `(no subtitles)` flag stops burned-in captions (add branded captions in post, inside the 9:16 safe zone).
- For MY ads: write the spoken line in casual BM (see COPYWRITING_MY.md), e.g. *"Penat balas WhatsApp tiap malam? Biar PeningBot settle, korang rehat je."* (~12 words ≈ 5s).

## UGC realism + consistency
- UGC cues: "handheld", "slight natural shake", "selfie video", "authentic/candid", "phone camera". Avoid over-cinematic words.
- **Character/product consistency:** supply reference images (Veo 3.1 "ingredients"), OR use last-frame-of-clip-1 → first-frame-of-clip-2 chaining, AND repeat the exact identity anchor (age/build/attire/hair) in every clip.

## Example (PeningBot UGC, 8s)
> Vertical 9:16, handheld selfie, slight shake. A 30-year-old Malaysian woman in a tudung, casual, sits at a home packing table at night with parcels behind her, warm lamp light from the left. She holds her phone to camera, frustrated then relieved, and says: "Dulu penat balas WhatsApp sampai pukul 2 pagi… sekarang PeningBot auto-reply, customer tetap dilayan." Authentic UGC, natural skin texture, no gloss. Ambient: quiet room tone. SFX: phone notification chime. (no subtitles). Format: 9:16, 1080p.

## Avoid
Too many words (fast/slurred, broken lip-sync) · forgetting `(no subtitles)` · multiple actions/clip · exact counts ("3 bottles" → use "a couple") · no light source/texture (plastic look) · vague framing · expecting 10–15s in one gen.

## Practical
Videos are slow/costly → make 1–3 hero videos + the rest images (see CREATIVE_IMAGE.md). Fire generations in PARALLEL; poll for URLs.
