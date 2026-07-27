# Research Archive Matcher (RAM) — User Guide

## 1. Scan and index PDFs

1. Open the **Library Scanner** tab.
2. Choose the folder containing your PDF archive.
3. Optionally enable Crossref enrichment.
4. Optionally tick **Enable OCR for image-only pages**.
5. Click **Initialize & Start Scan**.

RAM extracts metadata and page text, then stores both in the local SQLite index.

### Scanning scanned or image-only PDFs

Tick **Enable OCR for image-only pages** to read pages that contain no
extractable text. The checkbox is available only when Tesseract is installed;
the label beside it always reports the current status, for example
`Tesseract 5.5.0 detected.`

While an OCR scan runs, RAM shows a second progress bar with the page being
processed, and the scan log records each OCR page:

```text
🔤 OCR enabled (Tesseract 5.5.0). Only image-only pages will be processed.
[1/1] Processing: scanned_paper.pdf...
    OCR page 3/3 -> 62 characters recovered
 ✔ [Journal Article] (3 pages indexed, 1 via OCR)
🔤 OCR summary: 1 page(s) recovered through OCR, 0 failure(s).
```

Notes:

- Only image-only pages are processed. Blank pages are skipped.
- Recovered text is added to the page search index, so scanned pages become
  searchable in **Full-Text Search**.
- Your PDF files are never modified.
- OCR makes scanning considerably slower, so leave it off for archives that
  already contain digital text.

## 2. Explore the library

Use **Library Explorer** to search indexed metadata such as title, author, DOI, journal, year, and document type.

## 3. Search PDF page text

1. Open **Full-Text Search**.
2. Enter a word, phrase, or sentence.
3. Select **Exact phrase** when word order and adjacency matter.
4. Set a minimum score if required.
5. Search and double-click a result to open its matching page in the RAM preview window.

The preview highlights the search words and shows the page number, score, snippet, and PDF file.

## 4. Match publication lists

Use **Publication Matcher** to compare Excel, Word, or text publication lists against the local PDF index. RAM produces Excel, Word, and HTML reports.

## 5. Keep your data private

RAM works offline by default. Keep `index.db`, PDF archives, generated reports, and private source material outside public Git repositories.
