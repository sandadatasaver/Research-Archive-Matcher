# Research Archive Matcher (RAM) — Handover

**Date:** 2026-07-28
**Owner:** Bishop David Sanda Ph.D
**Location:** Abuja, Nigeria
**GitHub account:** `sandadatasaver`
**Repository:** https://github.com/sandadatasaver/Research-Archive-Matcher
**Branch:** `feature/ocr-support` @ `11f3697`
**Tests:** 37 passing
**Platform:** Windows, Python 3.14.6

---

# 1. Current state

RAM is an offline-first research document intelligence platform. It scans
folders of PDFs, extracts metadata, builds a local SQLite index, searches
page text, matches external publication lists, detects duplicates, and
generates Excel, Word and HTML reports.

Everything runs locally. No document ever leaves the machine.

## Completed and stable

**Core engine**

- PDF reading with PyMuPDF, `pypdf` fallback.
- Metadata extraction: layout-aware title, authors, DOI, abstract, keywords.
- Document type classification.
- SQLite index with `documents`, `pdf_pages`, and an FTS5 `page_search` table.
- SHA-256 exact duplicate detection, fuzzy title duplicate detection.
- RapidFuzz publication matching.
- Excel, Word and HTML reports.
- Optional Crossref enrichment.

**Search**

- Page-by-page text extraction and storage.
- FTS5 full-text search across all pages.
- Exact phrase search, including across PDF line breaks.
- All-query-words search.
- Similarity scores, page numbers, text snippets.

**GUI (Tkinter)**

- Four tabs: Library Scanner, Library Explorer, Full-Text Search,
  Publication Matcher.
- Background scanning with progress and live log.
- Built-in PDF preview with highlighted search terms and page navigation.
- Help / FAQ and About dialogs, driven by `docs/usage.md` and `docs/faq.md`.

**OCR**

- Blank-page versus image-only page detection.
- Optional Tesseract provider, degrades gracefully when absent.
- GUI checkbox with live availability status.
- Dedicated OCR progress bar and per-page logging.
- Per-page error isolation: one failed page never aborts a scan.

**Packaging**

- Inno Setup script, PyInstaller, GitHub Actions for Windows, macOS, Linux.

## Test suite — 37 tests

| File | Tests | Covers |
|---|---|---|
| `test_ram.py` | 8 | Extraction, database, matching, reporting |
| `test_app_icon.py` | 9 | Cross-platform window icons |
| `test_gui_ocr_option.py` | 7 | OCR checkbox and progress |
| `test_ocr_progress.py` | 5 | Per-page OCR callbacks and failures |
| `test_pdf_reader.py` | 2 | Page extraction |
| `test_page_search.py` | 2 | Phrase and word search |
| `test_ocr_provider.py` | 2 | Tesseract availability |
| `test_ocr_detection.py` | 1 | Blank versus image pages |
| `test_page_index.py` | 1 | Page storage |

```powershell
python -m unittest discover -s tests -p "test*.py" -v
```

GUI tests skip automatically when no display is available.

---

# 2. Architecture

```text
ram.py                        CLI entry point and GUI launcher
src/
  extractors/                 title, authors, doi, abstract, keywords, metadata
  indexer/database.py         SQLite schema and all queries
  matcher/                    fuzzy_match, publication_match
  ocr/tesseract_ocr.py        optional OCR provider
  readers/                    pdf_reader, excel_reader, word_reader
  reports/                    excel_report, word_report, html_report
  search/page_search.py       FTS5 page search service
  ui/
    main_window.py            main GUI, ~1200 lines
    pdf_preview.py            highlighted PDF preview window
    app_icon.py               shared cross-platform icon handling
tests/                        9 test files, 37 tests
docs/                         usage.md and faq.md feed the in-app Help
```

## Database schema

```sql
documents(id, file_name, file_path UNIQUE, title, authors, doi, journal,
          year, abstract, keywords, document_type, page_count, file_hash,
          indexed_at)

pdf_pages(id, document_id, page_number, page_text,
          UNIQUE(document_id, page_number))

page_search  -- FTS5 virtual table
  (document_id, page_number, file_path, title UNINDEXED, page_text)
```

Indexes exist on `doi`, `file_hash` and `title`.

## CLI

```bash
python ram.py gui                                   # default
python ram.py init --db index.db
python ram.py scan <folder> [--online] [--ocr]
python ram.py search <query> [--field FIELD]
python ram.py search-text <query> [--phrase] [--limit N]
python ram.py ocr-status <pdf>
python ram.py match <targets-file> [--threshold N]
python ram.py stats
```

---

# 3. Environment

```text
Python 3.14.6
PyMuPDF 1.28.0
pytesseract 0.3.13
Tesseract 5.5.0.20241111
  C:\Users\David Sanda\AppData\Local\Programs\Tesseract-OCR
```

Runtime dependencies are in `requirements.txt`; OCR extras in
`requirements-ocr.txt`.

---

# 4. Privacy and repository hygiene

**The PDF archive is private and must never be committed or uploaded.**
Keep it outside the repository folder, as is current practice.

A history purge was completed on 2026-07-28. `Publications.docx` and
`PDFs/` were removed from all branches and tags. Because pull request refs
are owned by GitHub and cannot be force-pushed, the repository was deleted
and recreated. Verified afterwards: zero hits on every ref, zero matching
objects, no pull request refs, 59 MB down to 12 MB.

Never commit: PDF archives, `Publications.docx`, `index.db`,
`page_search_test.db`, output reports, `Output/`, `build/`, `dist/`,
generated installers, `ocr_page_*.png`.

Local backups retained: `RAM-backup-2026-07-27.bundle`,
`ResearchArchiveMatcher-before-history-purge.bundle`,
`RAM-old-prototype.zip`.

---

# 5. Known issues and immediate tasks

**Repository housekeeping**

1. Default branch points at `arena/019f7c23-research-archive-matcher`.
   Change to `main` in Settings, then delete that branch.
2. `main` is 8 commits behind `feature/ocr-support`. Merge it.
3. `.gitignore` lists `Publications.docx` twice, lines 17 and 19. Cosmetic.

**Build correctness — important**

4. `.github/workflows/build.yml` does not install `pytesseract`, and no
   PyInstaller line declares hidden imports. Because `pytesseract` is
   imported lazily inside a function, **packaged builds ship without working
   OCR.** Add to the pip line and to all three PyInstaller commands:

```text
pip install ... pytesseract ...
--hidden-import=pytesseract --hidden-import=PIL._tkinter_finder
```

**Documentation**

5. `README.md` still lists `Unreadable (scanned images without OCR)` and
   does not mention OCR, page search or the PDF preview.
6. Updated `installer.iss` and `installer_info.txt` for v1.2.0 are prepared
   and ready to commit.

---

# 6. Roadmap — recommended order

The original four-phase roadmap is essentially complete. What follows is
ordered by benefit to real users rather than by feature count.

## Priority 1 — Incremental scanning

**The single highest-value change.**

`Database.add_document` uses `ON CONFLICT(file_path) DO UPDATE`, so a
re-scan re-extracts, re-reads and **re-OCRs every file**, even when nothing
changed. On a 500-PDF archive with OCR enabled, that is the difference
between minutes and hours.

The fix is small because the schema already stores `file_hash`:

1. Before extraction, compute the file hash.
2. Compare with the stored hash for that `file_path`.
3. If unchanged, skip extraction, page storage and OCR entirely.
4. Add `--force` to override.
5. Report `X new, Y updated, Z unchanged` at the end.

Also detect deleted files and offer to prune them from the index.

## Priority 2 — Parallel scanning

Scanning is a serial loop in `ram.py` and in the GUI worker. PDF parsing is
CPU-bound and independent per file, so a `ProcessPoolExecutor` over files
would give a near-linear speed-up on multi-core machines.

Combined with Priority 1, a large archive becomes genuinely quick to
maintain. Keep a `--jobs` flag so users can limit it.

## Priority 3 — Citation export

The one Phase 3 item never built. Researchers live in reference managers.

- Export selected or all documents as **BibTeX** and **RIS**.
- Formatted citations in APA, MLA and Chicago.
- "Copy citation" from the Library Explorer right-click menu.

Most of the data already exists: title, authors, year, journal, DOI.

## Priority 4 — Search quality

- **Boolean operators** — `AND`, `OR`, `NOT`, already supported natively by
  FTS5 and currently unexposed.
- **Field-scoped page search**, for example `author:Sanda malaria`.
- **Search history** and saved searches.
- **Export search results** to CSV or Excel.
- **Result grouping by document** rather than a flat page list.

## Priority 5 — OCR maturity

- OCR a whole document on demand from the Library Explorer, not only during
  a scan.
- Language selection, since Tesseract supports many.
- Persist which pages were OCR'd, so re-scans skip them. The `ocr_used` flag
  is computed but never stored — add a column to `pdf_pages`.
- Confidence scores, to flag poor OCR for review.

## Priority 6 — Reliability and scale

- Structured logging to a rotating file, invaluable for diagnosing user
  reports.
- A crash-safe scan that can resume after interruption.
- Benchmark on 1000+ PDFs and record the numbers.
- Consider SQLite `VACUUM` and index maintenance commands.

## Priority 7 — Distribution

- Publish v1.2.0 with the corrected build workflow.
- A short screen-recorded walkthrough would help adoption more than any
  further feature.
- Sample dataset of open-access PDFs so new users can try RAM immediately.
- Consider PyPI packaging, `pip install research-archive-matcher`.

---

# 7. Suggested next session

A focused, high-value block of work:

1. Merge to `main`, fix the default branch.
2. Fix `build.yml` so OCR works in packaged builds.
3. Commit the v1.2.0 installer files.
4. Update `README.md`.
5. Tag and publish **v1.2.0**.
6. Then begin **Priority 1, incremental scanning**, with tests.

Steps 1 to 5 are half a session and close out everything outstanding.
Step 6 is the change users will notice most.

---

# 8. Development conventions

- Write the test first, or alongside. The suite went 16 to 37 this session
  and every regression was caught by it.
- GUI tests must skip cleanly when no display is present.
- New features stay optional and degrade gracefully, as OCR does.
- Never modify the user's PDF files.
- Keep `docs/usage.md` and `docs/faq.md` current — they are the in-app help.
- Verify against a real repository or real files rather than assumptions.
