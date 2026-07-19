# Research Archive Matcher (RAM) - Usage Guide

This guide describes how to run and make the most of **Research Archive Matcher (RAM)**.

## Installation

### Prerequisites
* Python 3.10 or higher
* Recommended libraries:
  ```bash
  pip install pymupdf openpyxl pandas pypdf python-docx rapidfuzz
  ```

## Getting Started (Quick Command Sequence)

### 1. Initialize the Database
Initialize a clean local SQLite index database (`index.db`):
```bash
./ram.py init
```

### 2. Scan a Folder of PDFs
Point RAM to any folder containing PDF research publications. It will recursively discover, parse, classify, and index them.
```bash
./ram.py scan /path/to/pdf/folder
```
*Optional Online Enrichment*: To connect to the Crossref API and automatically enrich metadata (title, authors, year) for PDFs with valid DOIs, pass the `--online` flag:
```bash
./ram.py scan /path/to/pdf/folder --online
```

### 3. Display Library Statistics
View a beautiful summary of your indexed document types, completeness percentage, average page count, and duplicate groups:
```bash
./ram.py stats
```

### 4. Search Your Library
Query your library instantly. Search across all fields or restrict your search to fields like `title`, `authors`, `doi`, `journal`, or `abstract`:
```bash
./ram.py search "Newcastle Disease"
./ram.py search "Doe" --field authors
```

### 5. Match a Target Publication List
Match an external list of publications (citations, spreadsheets, or bibliographies) against your local indexed PDFs:
```bash
./ram.py match samples/target_publications.xlsx --threshold 75.0 --out-dir reports
```
This accepts Excel (`.xlsx`, `.xls`), Word (`.docx`), or Plain Text (`.txt`) lists and produces 5 output deliverables in the specified directory:
1. `reports/report.xlsx` - Successfully matched publications.
2. `reports/unmatched.xlsx` - Target publications that were not found in your index.
3. `reports/duplicates.xlsx` - Exact file hash duplicates and potential title duplicates found in your PDF folder.
4. `reports/matching_report.docx` - A formal Microsoft Word summary report.
5. `reports/matching_report.html` - An interactive, responsive HTML dashboard.
