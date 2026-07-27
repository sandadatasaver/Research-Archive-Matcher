# RAM FAQ

## Does RAM upload my PDFs?

No. RAM processes documents locally. Crossref enrichment is optional and only uses online lookup when you explicitly enable it.

## Why do page searches return no results?

The PDF folder must be scanned using the page-aware RAM version first. The scan creates page text in SQLite.

## What is the difference between word and phrase search?

A word search finds pages containing a term. An exact phrase search requires the words to occur together in the same order on one page. A multi-word search without Exact phrase finds pages containing all query words even when separated.

## What does the percentage mean?

An exact phrase receives 100%. Pages containing all query words receive a high score. Other results use fuzzy text similarity.

## How do I open the matching page?

Double-click a result in Full-Text Search. RAM opens an internal PDF preview at the matching page and highlights the searched terms.

## Can RAM search scanned PDFs?

Yes, when OCR is enabled. Tick **Enable OCR for image-only pages** on the Library Scanner tab before scanning. RAM then reads scanned pages with Tesseract and adds the recovered text to the page search index.

OCR requires Tesseract to be installed. If RAM cannot find it, the checkbox is disabled and the reason is shown beside it.

## When does RAM use OCR?

Only where it is needed. RAM OCRs a page only when that page has almost no extractable text and does contain an image. Pages that already contain text are never re-processed, and genuinely blank pages are skipped, so a scan stays as fast as possible.

Your PDF files are never modified. OCR text is written only to the local index.

## Why is scanning slower with OCR enabled?

OCR renders each image-only page and analyses it, which takes far longer than reading embedded text. The scan log and the OCR progress bar show which page is being processed so you can monitor a long run.

## How do I install Tesseract?

Install Tesseract for your operating system, then restart RAM.

On Windows the usual location is:

```text
C:\Users\<you>\AppData\Local\Programs\Tesseract-OCR
```

Verify the installation from a terminal:

```bash
tesseract --version
```

## Where is the local database?

The default database is `index.db` in the RAM project folder. Do not commit it to GitHub if it contains private archive metadata.

## What reports does RAM create?

Publication matching creates Excel, Word, and HTML reports, including matched items, unmatched items, and duplicate groups.
