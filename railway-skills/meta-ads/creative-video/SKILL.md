---
name: creative-video
description: Produce ad VIDEOS with the gemini/Veo model (and the AI-UGC pipeline) via the peninglab MCP. Covers prompt structure, dialogue word-count per clip, 9:16, realism levers, the AI-UGC workflow (consistent actor + product composite + animate + edit), scene cadence, and voiceover. Use whenever generating video creatives for PeningBot/PeningLab.
---

# Creative — VIDEO generation (gemini / Veo + AI-UGC)

Generate via the **peninglab** MCP. Default video model = the **gemini** model (user preference); Veo 3.1 is
the realism/consistency benchmark for the pipeline. Fire ~3–4 generations in parallel; on timeout recover via
`get_status(task_id)` (still charged — don't regenerate). Ask before spend > RM5.

## Prompt structure
`[subject] · [action] · [camera: shot type + movement] · [lighting] · [lens/mood] · [setting] · [audio /
spoken dialogue] · [style]`. Name a **real light source + texture + minor imperfection** ("handheld iPhone
look, soft window light, slight grain") to kill the AI sheen.

## Dialogue / voiceover (lip-sync)
- Put spoken lines in quotes. **Rule of thumb: ~16–20 words of dialogue per 8-second clip** (~2–2.5 words/sec);
  ~20–25 words per 10s. Don't overstuff or lip-sync breaks.
- **Avoid burned-in subtitles** from the model: add `(no subtitles)` / negative prompt; add your own
  native-style captions in the edit instead.
- For voiceover ads: generate B-roll, then layer a separate VO (ElevenLabs supports BM/Manglish accents).

## Clip length & format
- Native clip ≈ **8s** (extend by chaining start/reference frames). **9:16** for Reels/Stories (primary);
  also 1:1 / 4:5 for feed. 1080-wide minimum.

## The AI-UGC pipeline (Andy/Jordan/Nick — produces dozens of ads cheaply)
1. Build ONE consistent **AI actor** matching the ICP (e.g. MY SME owner, 30s–40s). Reuse across all clips.
2. Composite the **real product/app screen** into the scene with nano-banana-pro (don't let it redraw the UI).
3. Generate 2–3 distinct scenes (at desk, holding phone, before/after).
4. **Animate** with the gemini/Veo model (start-frame or reference-frame = most consistent).
5. **Edit UGC-style** (CapCut look, NOT Hollywood): scene change every **2–3s** (1s for young), native
   captions, 50/50 talking-head/B-roll. Emulate a proven competitor's cut pacing.
- Use AI to find the **winning angle cheaply**, then hand the proven concept to a **real local creator** to
  scale (AI-look is now an objection — mix in real footage). AI does ~85%, human polishes the last 15%.

## Video concepts to produce (for PeningBot/PeningLab, CTWA)
- Phone-screen recording: WhatsApp inbox flooding at 3am → PeningBot auto-replies in 2s.
- Founder/owner talking-head: problem → solution → "jom cuba free 7 hari".
- Before/after: messy inbox → handled; stressed owner → calm.
- Live screen-record of the bot replying / qualifying a lead.
- Local UGC testimonial (real face, BM/Manglish).
- Data/text-on-screen: response-time / sales-recovered chart.

## Rules (Andromeda)
- Hook = **first 3s** (track hook rate ≥30%). Each video = a **distinct entity** (different concept + copy).
- The 3-ads/ad-set unit: same video/body, **only the first-3s visual hook differs** (see `creative-andromeda`).
- 1–3 videos per batch is fine if statics fill the rest; video is the bulk of spend at scale.
