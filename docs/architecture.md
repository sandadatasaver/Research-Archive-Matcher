# Research Archive Matcher (RAM) - Architecture

Research Archive Matcher (RAM) is designed as a modular, offline-first Python application for researchers, librarians, and students to read, index, search, and match folders of PDFs against external target lists.

## System Overview

```
                      +-------------------+
                      |   Input Folder    |
                      |   (bunch of PDFs) |
                      +---------+---------+
                                |
                                v
                      +---------+---------+
                      |   PDF Readers     | (PyMuPDF / pypdf)
                      +---------+---------+
                                |
                                v
                      +---------+---------+
                      | MetadataExtractor | (Title, Authors, DOI, Abstract, Type)
                      +---------+---------+
                                |
                                v
                      +---------+---------+
                      |  SQLite Database  | (index.db)
                      +---------+---------+
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
   +---------+---------+                 +---------+---------+
   |   Search Engine   | (CLI query)     | PublicationMatch  | <-- Target List (Excel/Word/TXT)
   +-------------------+                 +---------+---------+
                                                   |
                                                   v
                                         +---------+---------+
                                         |  Report Generator |
                                         +---------+---------+
                                                   |
                             +---------------------+---------------------+
                             |                     |                     |
                             v                     v                     v
                     +-------+-------+     +-------+-------+     +-------+-------+
                     |  Excel Sheets |     | Word Document |     | Interactive   |
                     |  (report.xlsx)|     | (summary.docx)|     | HTML Dashboard|
                     +---------------+     +---------------+     +---------------+
```

## Core Modules

### 1. Readers (`src/readers/`)
Responsible for reading external file formats securely:
* **`pdf_reader.py`**: Integrates **PyMuPDF (fitz)** for fast and styled first-page font/layout parsing, with a robust fallback to **pypdf** to handle general PDF content extraction.
* **`word_reader.py`**: Uses **python-docx** to extract paragraph and table text from Microsoft Word documents.
* **`excel_reader.py`**: Uses **pandas** and **openpyxl** to parse structured tabular records from spreadsheets.

### 2. Extractors (`src/extractors/`)
Drives deep document understanding:
* **`title.py`**: Analyzes the first page using a combination of **font size analysis** (extracting the largest, most significant, non-boilerplate headers) and heuristic-based text fallback lines.
* **`doi.py`**: Utilizes advanced regular expressions to locate Digital Object Identifiers (DOIs).
* **`authors.py`**: Leverages positional rules and affiliation word filters (e.g. university, department, email checks) to isolate and format author lists.
* **`abstract.py`**: Pinpoints and bounds abstract/summary bodies.
* **`keywords.py`**: Identifies key lists.
* **`metadata.py`**: Combines all components and runs a **structural classifier** to automatically categorize files into:
  - Research Articles
  - Books / Monographs
  - Table of Contents
  - Conference Papers
  - Reports / Miscellaneous
  - Unreadable (scanned images without OCR)
  *Optional: Supports connection to the Crossref API for high-fidelity online metadata enrichment when a DOI is found.*

### 3. Indexer (`src/indexer/`)
Manages persistence:
* **`database.py`**: A **SQLite3** database index storing schema details, generating SHA-256 hashes for fast exact-duplicate file checking, and offering fast case-insensitive query searching.

### 4. Matcher (`src/matcher/`)
Handles list comparisons:
* **`fuzzy_match.py`**: Integrates **rapidfuzz** to calculate multiple text matching dimensions (standard ratio, token-sort ratio, and token-set ratio) for reliable title comparison.
* **`publication_match.py`**: Combines target citations with indexed publications using exact DOI mapping or high-confidence fuzzy title alignment.

### 5. Reports (`src/reports/`)
Produces the deliverables:
* **`excel_report.py`**: Builds clean spreadsheet outputs featuring customized colors, auto-fit columns, and individual sheets for duplicates.
* **`word_report.py`**: Compiles an executive summary and matched publication table in a Microsoft Word document.
* **`html_report.py`**: Builds an interactive, single-page, responsive HTML dashboard that enables searching, filtering, and modern tab switching in any browser.
