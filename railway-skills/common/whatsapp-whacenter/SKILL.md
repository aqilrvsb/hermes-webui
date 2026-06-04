---
name: whatsapp-whacenter
description: Send a WhatsApp message/report via whacenter. WhatsApp is ALREADY CONNECTED here — use this to deliver any WhatsApp report/alert. Never ask the user to set up WhatsApp or which channel.
---
# Send WhatsApp via whacenter

**STATUS: ALREADY CONNECTED & TESTED.** whacenter is THE WhatsApp channel for this Hermes.
Do **NOT** ask the user "which WhatsApp channel?", do **NOT** ask for setup steps, do **NOT**
offer Zernio/Telegram alternatives — it's done. The device + owner number are already env vars
(`$WHACENTER_DEVICE`, `$WHACENTER_DEFAULT_TO`). For any "send WhatsApp / daily report" task, just send:

whacenter unofficial API. Send with the terminal (curl):

```
curl -s -X POST https://api.whacenter.com/api/send \
  --data-urlencode "device_id=$WHACENTER_DEVICE" \
  --data-urlencode "number=<recipient_with_country_code>" \
  --data-urlencode "message=<the report text>"
```

- `device_id` = the whacenter **instance** (env var `WHACENTER_DEVICE`, from your whacenter admin -> device).
- `number` = pick in this order: the client's `whatsapp_report_to` from its AGENTS.md → else `$WHACENTER_DEFAULT_TO` (the owner's number) when the user says "WhatsApp **me**" → else ask. Always include country code (e.g. 60123456789).
- Account API key (for managing devices) is `WHACENTER_API_KEY`.
- Success = HTTP 200 with `{"status":true,...}`. If `status:false`, surface the error (usually the device is disconnected — tell the user to re-scan the QR in whacenter).

"WhatsApp ME the report" (default recipient = owner):
```
curl -s -X POST https://api.whacenter.com/api/send \
  --data-urlencode "device_id=$WHACENTER_DEVICE" \
  --data-urlencode "number=$WHACENTER_DEFAULT_TO" \
  --data-urlencode "message=$REPORT"
```

For a client report: build the summary (use meta-weekly-report), then send it to that client's `whatsapp_report_to`.
