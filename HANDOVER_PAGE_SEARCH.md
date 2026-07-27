# RAM Page-Aware Search Handover

## Current branch

`feature/page-fulltext-search`

## Completed in this milestone

- `PDFReader.get_page_texts()` returns one-based page text records.
- SQLite stores page text in `pdf_pages`.
- SQLite FTS5 stores searchable page content in `page_search`.
- GUI scanning automatically stores page text while indexing PDFs.
- CLI command `search-text` returns article, page, snippet, score, and match type.
- Exact phrase search handles PDF line breaks through normalized fallback matching.
- RAM Full-Text Search GUI tab is available.
- Double-clicking a result opens a branded in-app PDF preview at the matching page.
- Search terms are highlighted in the preview.
- RAM logo appears in the PDF preview title bar.
- GUI Help and About layout remain functional.

## Tests

The RAM page-search branch currently passes the baseline tests plus page extraction, storage, and search tests. Run:

```bash
python -m unittest discover -s tests -p 'test*.py' -v
```

## Usage

Scan the private PDF archive through the GUI or CLI. The GUI uses `index.db` by default:

```bash
python ram.py --db index.db scan /path/to/private/pdfs
python ram.py --db index.db search-text "PowerShell automation" --phrase
```

A phrase search requires adjacent words in the same page. A multi-word search without `--phrase` finds pages containing all query words even when separated.

## Current limitations

- OCR is not yet implemented for scanned image-only PDFs.
- Search results are page-level; semantic search is not yet implemented.
- The preview highlights text using PDF text extraction and cannot highlight image-only scanned text.
- The GUI currently opens the preview and supports page navigation; a richer PDF annotation/zoom toolbar can be added later.

## Next milestones

1. Commit the page-aware search and GUI-preview work.
2. Add richer search controls and filters.
3. Add OCR support for scanned PDFs.
4. Add optional embedded PDF zoom and page navigation controls.
5. Add advanced similarity and semantic search.
