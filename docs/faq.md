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

Scanned image-only PDFs require OCR before their text can be searched. OCR support is a future enhancement.

## Where is the local database?

The default database is `index.db` in the RAM project folder. Do not commit it to GitHub if it contains private archive metadata.

## What reports does RAM create?

Publication matching creates Excel, Word, and HTML reports, including matched items, unmatched items, and duplicate groups.
