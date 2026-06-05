---
name: read-documents
description: Read PDFs (including scanned/image-only PDFs), images/screenshots, and files behind a link (including Google Drive). Use whenever the user gives a link, attaches/drops a PDF or image, or asks you to read a document — especially when plain text extraction returns little or nothing.
---

# read-documents

**You run on a multimodal Claude model (via APIPod) — you can SEE images, like Claude Code.**
So your FIRST choice for anything visual is to *look at the image itself*, not OCR it.
For image/PDF reading the recommended model is **claude-sonnet-4-5** (strong, cheap vision) — if you're
on a non-vision model, switch the chat model to **claude-sonnet-4-5** in the picker before reading.
PDFs aren't a native image type, so render their pages to images first, then view them.

Terminal tools available (no MCP, no extra model needed):
`curl`, `file`, `pdftotext`, `pdftoppm`, `pdfinfo` (poppler), and `tesseract` (OCR fallback, English + Malay).

## Vision-first principle (how Claude Code does it)
- An **image** (png/jpg/screenshot/photo) → **view it directly** with your vision. If your file-read
  tool can return the image to your context, do that and read/describe it. Only if you literally
  cannot load images into context, fall back to `tesseract` OCR (text only).
- A **PDF** → models don't ingest PDF bytes. Convert each page to an image with `pdftoppm`
  (below), then **view the page images** with your vision. Use `pdftotext` first only as a quick
  shortcut for clearly text-based PDFs.

## Decide the path

1. If the user gave a **URL/link** → download it first (see *Download a link*), then treat the downloaded file by type.
2. If a **file was attached/dropped** → it is already in your workspace; find it (`ls -lt`), then go by type.
3. By type:
   - **PDF** → *Read a PDF* (text first, OCR fallback).
   - **Image** (png/jpg/webp/screenshot) → *Read an image* (OCR).

Always run `file <path>` first to confirm the real type (extensions lie).

## Download a link

Plain URL:
```bash
curl -L -o /tmp/dl "<URL>"
file /tmp/dl
```

**Google Drive** share links like `https://drive.google.com/file/d/FILE_ID/view?usp=sharing`
— extract `FILE_ID` (the part after `/d/`) and download the actual file (handles the
large-file confirm-token page):
```bash
ID="FILE_ID"
curl -sL -c /tmp/gck "https://drive.google.com/uc?export=download&id=$ID" -o /tmp/probe
# small files download directly; large files return an HTML confirm page:
if file /tmp/probe | grep -qi 'html'; then
  CONF=$(grep -o 'confirm=[^&"]*' /tmp/probe | head -1 | cut -d= -f2)
  UUID=$(grep -o 'name="uuid" value="[^"]*"' /tmp/probe | sed 's/.*value="//;s/"//')
  curl -sL -b /tmp/gck "https://drive.usercontent.google.com/download?id=$ID&export=download&confirm=$CONF&uuid=$UUID" -o /tmp/dl
else
  mv /tmp/probe /tmp/dl
fi
file /tmp/dl   # confirm it's a PDF/image, not HTML
```
If it still comes back as HTML, the file isn't publicly shared — ask the user to set the
link to **"Anyone with the link"**, or to attach the file directly in chat.

## Read a PDF

Quick shortcut for clearly text-based PDFs:
```bash
pdftotext -layout /tmp/dl /tmp/out.txt && wc -c /tmp/out.txt && head -c 3000 /tmp/out.txt
```
If `out.txt` is **empty or tiny** (e.g. < 100 chars), the PDF is **scanned images** →
render the pages to images and **VIEW them** (you are multimodal):
```bash
pdfinfo /tmp/dl | grep Pages
pdftoppm -png -r 200 /tmp/dl /tmp/pg            # one PNG per page, e.g. /tmp/pg-1.png …
ls -1 /tmp/pg-*.png
```
Now **open those PNGs as images and read them with your vision** — describe/extract exactly
what's on each page, like Claude Code reading a PDF. Do them in page order.
If (and only if) you cannot load images into your context, fall back to OCR:
```bash
for f in /tmp/pg-*.png; do tesseract "$f" "${f%.png}" -l eng+msa; done
cat /tmp/pg-*.txt | head -c 4000     # eng+msa = English + Malay; use -r 400 for tiny text
```
Clean up afterwards: `rm -f /tmp/pg-*.png /tmp/pg-*.txt`.

## Read an image / screenshot

**View it directly with your vision** (minimax-m3 is multimodal) — read any text, describe
the layout, charts, product, design, whatever is asked. That is the Claude-Code path.
Only if you genuinely cannot load the image into context, OCR the text:
```bash
tesseract /path/to/image.png /tmp/img -l eng+msa && cat /tmp/img.txt
```

## Rules
- Never claim a document is empty after only `pypdf`/`pdftotext` — if it returns little, **always try the OCR fallback** before concluding.
- After extracting, summarize what you actually read and cite page numbers when relevant.
- Clean up `/tmp/pg-*.png` after OCR to save space.
