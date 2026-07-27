# Research Archive Matcher (RAM) — User Guide

## 1. Scan and index PDFs

1. Open the **Library Scanner** tab.
2. Choose the folder containing your PDF archive.
3. Optionally enable Crossref enrichment.
4. Click **Initialize & Start Scan**.

RAM extracts metadata and page text, then stores both in the local SQLite index.

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
