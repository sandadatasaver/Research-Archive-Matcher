# Research Archive Matcher (RAM) - Project Handover

Welcome to the official handover document for **Research Archive Matcher (RAM)**! This document serves as a complete checkpoint, listing all accomplishments, architectural blueprints, packaging guides, and instructions on how to finalize and merge this project.

---

## 📌 Project Status Checkpoint

We have successfully transitioned RAM from a simple script into a **production-ready, modern, offline-first Desktop and Command-Line Application** with zero external GUI dependencies. 

### 1. Completed Milestone Delivery
* **Modular Codebase**: Organized into a strict single-responsibility package structure (`readers/`, `extractors/`, `indexer/`, `matcher/`, `reports/`, and `ui/`).
* **Layout-Aware NLP Title Extractor**: Primary extraction analyzes PyMuPDF first-page font sizes to isolate document titles while filtering out journal boilerplate headers. Corrects and falls back elegantly to standard NLP text rules.
* **Auto Document Structural Classifier**: Automatically groups documents into *Research Articles*, *Books & Monographs*, *Table of Contents*, *Conference Papers*, *Reports*, and *Unreadable* files.
* **100% Offline SQLite Indexer**: Builds a fast, local index database (`index.db`) containing complete document metadata and text samples, with SHA-256 binary file hashing to aggregate exact duplicates.
* **High-Performance Fuzzy Matcher**: Computes weighted string similarities (Ratio, Token-Sort, and Token-Set metrics via rapidfuzz) to align external citation lists (from Excel, Word, or TXT) to local indexed PDFs.
* **Interactive HTML & Word Reports**: In addition to standard styled Excel sheets (`report.xlsx`, `unmatched.xlsx`, `duplicates.xlsx`), RAM now automatically compiles a Microsoft Word Executive Summary and a gorgeous, responsive, searchable HTML Browser Dashboard.
* **Polished Desktop GUI**: Features multi-tab navigation, background thread execution (prevents window freezing), live scrolling progress log terminal, interactive filter-on-the-fly index explorer grid, andHelp/FAQ windows.
* **Vision Statement & Publisher Dedication**: Centered and styled as a prominent golden vision box:
  > *"This open source tool is Provided for Students, Lecturers, Editors and Researchers alike 100% Free for the glory of Jesus my Saviour"*
* **App Branding & Logos**: Four professional logo designs built, including the finalized Saturn's ring metallic gold curved lettering design (`docs/logo_final.png`).

---

## 📂 Project Organization

```
ResearchArchiveMatcher/
│
├── docs/                      # Documentation & Visuals
│   ├── architecture.md        # Deep architectural design
│   ├── usage.md               # Advanced command-line options
│   ├── logo_final.png         # Master Software Logo (Saturn ring gold style)
│   ├── logo_option_a.png      # Logo Option A (Navy/teal horn)
│   ├── logo_option_b.png      # Logo Option B (Emerald/navy nodes)
│   ├── logo_option_c.png      # Logo Option C (Blue/purple/gold horn)
│   └── logo_option_d.png      # Logo Option D (Sapphire/purple arcs)
│
├── samples/                   # Pre-bundled mock inputs
│   ├── target_publications.xlsx
│   ├── target_publications.docx
│   └── target_publications.txt
│
├── src/                       # Application Core Packages
│   ├── extractors/            # NLP & Layout Extraction
│   │   ├── abstract.py, authors.py, doi.py, keywords.py, title.py, metadata.py
│   │
│   ├── indexer/               # SQLite Persistence Index
│   │   └── database.py
│   │
│   ├── matcher/               # NLP Similarity Matching
│   │   ├── fuzzy_match.py and publication_match.py
│   │
│   ├── readers/               # High-Performance Document Readers
│   │   ├── excel_reader.py, pdf_reader.py, and word_reader.py
│   │
│   ├── reports/               # Deliverables compilation
│   │   ├── excel_report.py, html_report.py, and word_report.py
│   │
│   └── ui/                    # Graphical User Interface
│       └── main_window.py
│
├── tests/                     # Unit Test Suite
│   └── test_ram.py
│
├── .gitignore                 # Safe list of ignored directories
├── LICENSE                    # MIT Open Source License
├── README.md                  # Comprehensive user manual
├── ram.py                     # Main CLI/GUI launch entrypoint
├── installer.iss              # Windows Inno Setup Compiler Script
└── HANDOVER.md                # This document
```

---

## 🔀 Finalizing & Merging to `main`

To ensure that your work is correctly tracked and recorded by the Arena.ai environment, **this session is locked to the branch `arena/019f7c23-research-archive-matcher`**. 

I have already created and configured a official **Pull Request (PR #1)** to merge this branch into your `main` branch. 

### How to Merge Your Work on GitHub:
1. Go to your GitHub repository: `https://github.com/sandadatasaver/Research-Archive-Matcher`
2. Click on the **Pull Requests** tab.
3. Select the PR named **"Implement Research Archive Matcher (RAM)"**.
4. Scroll down and click the green **Merge Pull Request** button, then confirm.
5. On your local PC Git Bash, switch back to main and pull everything:
   ```bash
   git checkout main
   git pull origin main
   ```

---

## 💻 Packaging and Releasing Your App

Here is the quick sequence of commands to execute on your Windows PC to build your final `.exe` and Inno Setup installer:

1. **Pull the latest codebase**:
   ```bash
   git pull origin arena/019f7c23-research-archive-matcher
   ```
2. **Convert Logo to `.ico`**: Convert `docs/logo_final.png` to `logo.ico` using an online converter (e.g. [icoconvert.com](https://icoconvert.com)) and place it in the root folder.
3. **Compile with PyInstaller**:
   ```bash
   pyinstaller --onefile --noconsole --icon=logo.ico --paths=. --add-data "docs;docs" --name "RAM" ram.py
   ```
4. **Compile Inno Setup Installer**:
   * Open `installer.iss` in Inno Setup.
   * Add `SetupIconFile=logo.ico` and `UninstallDisplayIcon={app}\RAM.exe` under the `[Setup]` block.
   * Press `Ctrl + F9` to compile.
   * Your final distributable file `ResearchArchiveMatcher_Setup.exe` is ready to share!
