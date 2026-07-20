# Research Archive Matcher (RAM)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

**Research Archive Matcher (RAM)** is a robust, offline-first research document intelligence platform and desktop workflow tool. Built for researchers, lecturers, students, and librarians, RAM allows you to easily index thousands of PDFs in a local folder, search them instantly, detect duplicate files, and match external publication lists (from Excel, Word, or TXT) against your local archive to generate comprehensive reports.

---

## 🚀 The Mission: Read ➔ Understand ➔ Index ➔ Search ➔ Match ➔ Report

Instead of spending hours manually aligning lists of publications against unstructured folders of PDFs, RAM automates the entire pipeline:
1. **Read**: Parses PDF, Word, and Excel files with high-performance parsers.
2. **Understand**: Extracts deep metadata (Titles, Authors, DOIs, Abstracts, Keywords, Years) and classifies PDFs structurally.
3. **Index**: Organizes your entire library into a high-performance local SQLite database.
4. **Search**: Provides instant, offline full-text and field-specific search capabilities.
5. **Match**: Performs exact DOI mappings and fuzzy title comparisons to link external citation lists to your offline PDFs.
6. **Report**: Generates polished, customized deliverables (Excel sheets, Word summaries, and interactive HTML dashboards).

---

## ✨ Key Features

* **Modern Graphical User Interface (GUI)**: Designed a clean, multi-tab window with a responsive layout. Features real-time log scrolling, an interactive index explorer table (with on-the-fly text searching), and point-and-click matching configurations.
* **Smart Title & Metadata Extraction**: Uses PyMuPDF's font/layout parsing to identify article titles by font-size hierarchy, ignoring journal boilerplate. Corrects and falls back elegantly to standard NLP text rules.
* **Document Structural Classifier**: Automatically categorizes files into:
  - *Research Articles*
  - *Books & Monographs*
  - *Table of Contents (TOC)*
  - *Conference Papers*
  - *Reports / Miscellaneous*
  - *Unreadable (scanned images without OCR)*
* **Deduplication Engine**: Automatically aggregates and isolates exact duplicates (via SHA-256 file hashes) and potential duplicates (via fuzzy title alignment).
* **Multi-Format Target Support**: Seamlessly matches publication lists supplied as Excel spreadsheets (`.xlsx`, `.xls`), Word documents (`.docx`), or plain text files (`.txt`).
* **Five-Star Report Suite**: Generates four complete matching reports:
  - `report.xlsx`: Beautifully formatted spreadsheet of matched targets and file mappings.
  - `unmatched.xlsx`: Isolated spreadsheet of targets that couldn't be matched (with closest suggestions).
  - `duplicates.xlsx`: Dual-sheet report detailing hash and title duplicates in your folder.
  - `matching_report.docx`: Executive summary document suitable for printing or sharing.
  - `matching_report.html`: An interactive, modern, and search-friendly browser dashboard.
* **100% Offline First**: All processing runs entirely on your local machine. No data or document text is sent to external servers. If an internet connection is available, RAM can optionally enrich metadata via secure Crossref API lookups.

---

## 🛠 Tech Stack

* **Python 3.10+**
* **PyMuPDF (fitz)** & **pypdf** (Robust PDF processing)
* **python-docx** (Word read/write)
* **pandas** & **openpyxl** (Excel processing & styling)
* **rapidfuzz** (High-speed C-based Levenshtein & token-ratio comparison)
* **SQLite3** (Lightweight local index database)

---

## 📦 Installation

Clone this repository and install the required dependencies:

```bash
git clone https://github.com/sandadatasaver/Research-Archive-Matcher.git
cd Research-Archive-Matcher
pip install pymupdf openpyxl pandas pypdf python-docx rapidfuzz
```

---

## 📖 Quick Start Guide

You can run RAM in two modes: **GUI Mode** (highly recommended for desktop use) or **CLI Mode** (ideal for headless servers or automated scripts).

### 🚀 Running the GUI
To start the beautiful desktop interface, simply double-click the executable or run the script with no arguments:
```bash
python ram.py
```
*(Optionally, use: `python ram.py gui`)*

---

### 💻 Running the Command Line Interface (CLI)

#### 1. Initialize the Index Database
Initialize a clean local SQLite database (`index.db`):
```bash
python ram.py init
```

### 2. Scan a PDF Directory
Scan and index all publications in a local folder.
```bash
./ram.py scan /path/to/my/pdfs
```
*To enable optional online Crossref metadata enrichment, append the `--online` flag:*
```bash
./ram.py scan /path/to/my/pdfs --online
```

### 3. Display Library Statistics
View structural category breakdown and metadata completeness:
```bash
./ram.py stats
```

### 4. Search Locally
Instantly search your local indexed papers:
```bash
./ram.py search "Newcastle Disease"
./ram.py search "Doe" --field authors
```

### 5. Match External Publication Lists
Compare a target citation list (Word, Excel, or Text) against your local index and export all reports:
```bash
./ram.py match samples/target_publications.xlsx --threshold 70.0 --out-dir reports
```

This generates five beautiful deliverables in `reports/`:
* `reports/report.xlsx` — Matched records with similarity scores and file paths.
* `reports/unmatched.xlsx` — Target list of missing articles with best-found index candidates.
* `reports/duplicates.xlsx` — Exact hash and potential title duplicate groups in your scan folder.
* `reports/matching_report.docx` — Word document summary report.
* `reports/matching_report.html` — Interactive browser-based search dashboard.

---

## 🧪 Running Unit Tests

We maintain a comprehensive suite of unit tests with 100% passing guarantees. Run them using python's built-in test runner:

```bash
python3 -m unittest tests/test_ram.py
```

---

## 📂 Project Organization

```
Research-Archive-Matcher/
│
├── docs/                      # Documentation
│   ├── architecture.md        # Deep architectural design
│   └── usage.md               # Advanced command-line options
│
├── samples/                   # Pre-bundled mock list inputs
│   ├── target_publications.xlsx
│   ├── target_publications.docx
│   └── target_publications.txt
│
├── src/                       # Source Code
│   ├── extractors/            # NLP & Layout Extraction
│   │   ├── abstract.py
│   │   ├── authors.py
│   │   ├── doi.py
│   │   ├── keywords.py
│   │   ├── metadata.py
│   │   └── title.py
│   │
│   ├── indexer/               # Local persistence
│   │   └── database.py
│   │
│   ├── matcher/               # Alignment engine
│   │   ├── fuzzy_match.py
│   │   └── publication_match.py
│   │
│   ├── readers/               # High-performance formats readers
│   │   ├── excel_reader.py
│   │   ├── pdf_reader.py
│   │   └── word_reader.py
│   │
│   └── reports/               # Deliverables compilation
│       ├── excel_report.py
│       ├── html_report.py
│       └── word_report.py
│
├── tests/                     # Test Suite
│   └── test_ram.py
│
├── LICENSE                    # MIT License
├── README.md                  # This file
└── ram.py                     # Primary executable script
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
