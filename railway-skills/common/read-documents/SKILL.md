---
name: read-documents
description: Read the contents of PDFs (including scanned/image-only PDFs via OCR), images/screenshots with text (OCR), and files behind a link (including Google Drive). Use whenever the user gives a link, attaches/drops a PDF or image, or asks you to read a document and plain text extraction returns little or nothing.
---

# read-documents

You can read links, PDFs, and images **without any MCP server and without a vision model** — using the terminal CLI tools baked into this container:
`curl`, `file`, `pdftotext`, `pdftoppm`, `pdfinfo` (poppler), and `tesseract` (OCR, English + Malay).

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

Try the fast text path first:
```bash
pdftotext -layout /tmp/dl /tmp/out.txt && wc -c /tmp/out.txt && head -c 3000 /tmp/out.txt
```
If `out.txt` is **empty or tiny** (e.g. < 100 chars), the PDF is **scanned images** → OCR it:
```bash
pdftoppm -png -r 300 /tmp/dl /tmp/pg            # rasterize each page at 300 dpi
for f in /tmp/pg-*.png; do tesseract "$f" "${f%.png}" -l eng+msa; done
cat /tmp/pg-*.txt > /tmp/ocr.txt
wc -c /tmp/ocr.txt && head -c 4000 /tmp/ocr.txt
```
`-l eng+msa` reads both English and Malay (Bahasa). Use `-r 400` for small/blurry text.

## Read an image / screenshot (text inside it)

```bash
tesseract /path/to/image.png /tmp/img -l eng+msa && cat /tmp/img.txt
```
Pre-clean blurry/low-contrast images for better OCR if needed (ImageMagick/`convert` if
present): grayscale + sharpen, then OCR.

## When OCR is NOT enough

OCR only extracts **text**. If the user needs you to *understand a picture visually*
(describe a photo, read a chart's shape, judge a design) and there is little/no text,
that needs a **vision-capable model**, which is a separate setting — tell the user plainly
rather than guessing from the filename. For documents, invoices, ads, screenshots, and
forms (text trapped in images), **OCR above is the correct and sufficient tool.**

## Rules
- Never claim a document is empty after only `pypdf`/`pdftotext` — if it returns little, **always try the OCR fallback** before concluding.
- After extracting, summarize what you actually read and cite page numbers when relevant.
- Clean up `/tmp/pg-*.png` after OCR to save space.
