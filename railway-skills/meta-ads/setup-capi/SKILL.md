---
name: meta-setup-capi
description: Guide and scaffold Meta Conversions API (server-side tracking) setup — events, dataset, deduplication with the Pixel. Use when improving tracking/attribution.
---
# Meta Ads — Conversions API (CAPI)
1. Identify the events to track (Purchase, Lead, etc.) and the platform (web/Supabase/Vercel app).
2. Outline: dataset/pixel id, access token, event schema (event_name, event_time, user_data hashed, custom_data, event_id for dedupe).
3. Provide server-side send code (use the project's stack) and Pixel event_id matching for deduplication.
4. Give a test plan via the Events Manager Test Events tool.
