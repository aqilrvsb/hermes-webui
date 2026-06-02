---
name: whatsapp-whacenter
description: Send a WhatsApp message/report via whacenter (unofficial WA API). Use when the marketer needs to WhatsApp a report or alert to the user or a client.
---
# Send WhatsApp via whacenter

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
