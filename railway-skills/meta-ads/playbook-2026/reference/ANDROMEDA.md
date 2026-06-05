# skills/ANDROMEDA.md — Meta "Andromeda" creative-diversity rules (2026)

Meta's **Andromeda** AI now runs targeting/optimization. The advertiser's job is
almost entirely **creative**. Andromeda has one behavior that breaks most accounts:

> It **collapses near-identical creatives into ONE "entity"** and only serves one of
> them. Same image with a tweaked headline / background colour / B&W-vs-colour = treated
> as the SAME ad → the others get **zero spend**. So "10 ads" become 1 → no reach
> diversity → "Surround Sound" never fires → CPL stays high and creative fatigues fast.

## The rule: every ad must be a DIFFERENT entity
For each creative "slot" to fill, the brief MUST specify a **distinct visual concept**
AND **unique copy** — not a variation of another slot. Aim for **10–20 genuinely
different ads** per ad set.

### Visual-concept diversity (each slot = a different one)
Rotate across concept types so no two share an entity:
1. Phone-screen recording (e.g. WhatsApp inbox flooding at 3am)
2. Founder/owner talking-head (problem → solution)
3. Before/after (messy inbox → auto-handled)
4. Screen-record of the product/bot replying live
5. UGC / customer testimonial (real face)
6. Text-on-screen data viz (response-time / sales chart)
7. Whiteboard / explainer
8. Split-screen (without bot vs with bot)
9. Meme / pattern-interrupt hook
10. Founder "counting on fingers" / list-style

### Copy diversity (one emotion per slot, never reuse a body)
| Emotion | Tone | CTA |
|---|---|---|
| Fear | loss framing ("customer tunggu, bos tidur?") | TRY_FREE |
| Urgency | time pressure / FOMO | TRY_FREE |
| Hope | dream state / reward | LEARN_MORE |
| Emotional | story / relatable | SIGN_UP |
| General | benefit-first / factual | LEARN_MORE |
| Social proof | validation / peer pressure | SIGN_UP |

Each ad = unique headline + unique body + matched CTA. **Never** reuse a body across slots.

## The hook is everything
- The **first ~3 seconds** of a video = the single biggest lever (sets "hook rate" = 3s-views ÷ impressions; good ≈ 20–33%, weak ≈ 7–9%).
- **Winner recombination:** take a proven *body* (good cost/result, weak hook) + graft on a proven *hook* (high hook rate) → near-guaranteed winner.
- Cold audiences → benefit/problem in the hook; warm → objection-led openers are OK.

## Testing (test BIG first)
Order: **Offer → Angle → Style → Hook → (last) copy/headline/colour.** Use a dedicated
testing campaign or Meta's Creative Testing Tool so Andromeda actually spends on new
creative; expect most tests to fail (think VC: one winner pays for many losers).

## Surround Sound = the goal
10+ distinct entities (different concept + angle) → Meta delivers all of them → a
prospect sees your brand across many formats/angles → trust + lower CPL. This is the
entire point of the diversity requirement.

## Brief schema Agent 5 must output (per slot) — `state/brief.json`
```json
{ "date":"YYYY-MM-DD","project":"peningbot","slots":[
  { "emotion":"fear","concept":"phone screen 3am WhatsApp flood","format":"video",
    "hook_2s":"Tiga customer WhatsApp pukul 3 pagi...","headline":"Customer tunggu, bos tidur?",
    "body":"Esok cuti. Tiada siapa jawab. Sales turun. PeningBot auto-reply dalam 2 saat.",
    "cta":"TRY_FREE","image_prompt":"dark bedroom, phone glowing 3am, 3 unread WhatsApp, red badges",
    "entity_note":"unique: night phone screen — different from all existing ads" } ] }
```
