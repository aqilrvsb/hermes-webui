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
- `number` = recipient phone incl. country code (e.g. 60123456789), or the client's `whatsapp_report_to` from its AGENTS.md.
- Account API key (for managing devices) is `WHACENTER_API_KEY`.
- A non-error HTTP 200 = sent. If it returns `status:false`, surface the error.

For a client report: build the summary (use meta-weekly-report), then send it to that client's `whatsapp_report_to`.
