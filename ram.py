#!/usr/bin/env python3
import os
import sys
import argparse
import logging
from src.indexer.database import Database
from src.extractors.metadata import MetadataExtractor
from src.matcher.publication_match import PublicationMatcher
from src.reports.excel_report import ExcelReporter
from src.reports.word_report import WordReporter
from src.reports.html_report import HTMLReporter

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("RAM")

def print_banner():
    banner = """
========================================================================
    ____                                 __       ___                  _               __  ___      __che_r
   / __ \___  ________  ____ ___________/ /_     /   |  ______________/ /_  _   _____  /  |/  /___ _/ /_ ____  _  __
  / /_/ / _ \/ ___/ _ \/ __ `/ ___/ ___/ __ \   / /| | / ___/ ___/ __  / __ \| | / / _ \/ /|_/ / __ `/ __/ ___/ _ \| |/_/
 / _, _/  __(__  )  __/ /_/ / /  / /__/ / / /  / ___ |/ /  / /__/ /_/ / / / /| |/ /  __/ /  / / /_/ / /_/ /__/  __/>  <  
/_/ |_|\___/____/\___/\__,_/_/   \___/_/ /_/  /_/  |_/_/   \___/\__,_/_/ /_/_|___/\___/_/  /_/\__,_/\__/\___/\___/_/|_|  
                                                                                                                        
========================================================================
              Offline Research Document Intelligence Platform
========================================================================
"""
    print(banner)

def handle_init(args):
    db_path = args.db
    if os.path.exists(db_path):
        confirm = input(f"Database '{db_path}' already exists. Overwrite? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Initialization cancelled.")
            return
        os.remove(db_path)
    
    Database(db_path)
    print(f"✔ Local SQLite index database initialized successfully at: {db_path}")

def handle_scan(args):
    folder = args.folder
    if not os.path.isdir(folder):
        print(f"❌ Error: Scanned folder does not exist: {folder}")
        sys.exit(1)
        
    db = Database(args.db)
    
    # Gather PDF paths
    pdf_files = []
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, f))
                
    total_files = len(pdf_files)
    if total_files == 0:
        print(f"No PDF documents found in folder: {folder}")
        return
        
    print(f"🔍 Found {total_files} PDFs to process. Starting offline scan and metadata extraction...")
    print("------------------------------------------------------------------------")
    
    indexed_count = 0
    errors_count = 0
    
    for i, path in enumerate(pdf_files, 1):
        rel_path = os.path.relpath(path, folder)
        print(f"[{i}/{total_files}] Extracting & indexing: {rel_path}...", end="", flush=True)
        
        try:
            extractor = MetadataExtractor(path)
            meta = extractor.extract(online_enrich=args.online)
            
            success = db.add_document(meta)
            if success:
                print(f" ✔ [{meta['document_type']}]")
                indexed_count += 1
            else:
                print(" ❌ (DB Error)")
                errors_count += 1
        except Exception as e:
            print(f" ❌ (Error: {e})")
            errors_count += 1
            
    print("------------------------------------------------------------------------")
    print(f"✔ Scan complete!")
    print(f" - Successfully indexed: {indexed_count} documents")
    if errors_count > 0:
        print(f" - Failed to process: {errors_count} documents")

def handle_search(args):
    db = Database(args.db)
    query = args.query
    field = args.field
    
    results = db.search(query, field)
    total = len(results)
    
    print(f"🔍 Found {total} matches searching for '{query}' in field '{field}':")
    print("------------------------------------------------------------------------")
    
    if total == 0:
        print("No documents matched your query.")
        return
        
    for i, doc in enumerate(results, 1):
        print(f"{i:2d}. {doc['title'] or 'No Title'}")
        print(f"    Authors:  {doc['authors'] or 'N/A'}")
        print(f"    Journal:  {doc['journal'] or 'N/A'} ({doc['year'] or 'N/A'})")
        print(f"    DOI:      {doc['doi'] or 'N/A'}")
        print(f"    Path:     {doc['file_path']}")
        print(f"    Doc Type: {doc['document_type']} | Pages: {doc['page_count']}")
        print("    " + "-"*60)

def handle_match(args):
    db = Database(args.db)
    if db.get_document_count() == 0:
        print("❌ Error: The local database is empty. Please run 'ram.py scan <folder>' first.")
        sys.exit(1)
        
    targets_file = args.targets
    if not os.path.exists(targets_file):
        print(f"❌ Error: Target publication file not found: {targets_file}")
        sys.exit(1)
        
    print(f"🔄 Matching target publications from: {targets_file}")
    print(f"   Threshold similarity: {args.threshold}%")
    print("------------------------------------------------------------------------")
    
    matcher = PublicationMatcher(db, threshold=args.threshold)
    results = matcher.match(targets_file)
    
    matched = results["matched"]
    unmatched = results["unmatched"]
    
    print(f"✔ Matching complete!")
    print(f"   - Successfully Matched: {len(matched)} publications")
    print(f"   - Unmatched:            {len(unmatched)} publications")
    
    # Calculate stats for reports
    db_stats = {
        "total_docs": db.get_document_count()
    }
    
    # Generate reports
    out_dir = args.out_dir
    print(f"📁 Saving reports to directory: '{out_dir}'...")
    
    # 1. Excel Sheets (report.xlsx, unmatched.xlsx)
    matched_path, unmatched_path = ExcelReporter.export_matching_results(results, output_dir=out_dir)
    print(f"   ✔ Excel Matching Report:  {matched_path}")
    print(f"   ✔ Excel Unmatched Report: {unmatched_path}")
    
    # 2. Duplicate detection & Excel Duplicates Report
    exact_dups = db.get_exact_duplicates()
    potential_dups = db.get_potential_duplicates()
    
    dup_path = ExcelReporter.export_duplicates_report(exact_dups, potential_dups, output_dir=out_dir)
    print(f"   ✔ Excel Duplicates Report: {dup_path} (Detected {len(exact_dups)} exact hash and {len(potential_dups)} potential title duplicates)")
    
    # 3. Microsoft Word Report
    word_path = os.path.join(out_dir, "matching_report.docx")
    WordReporter.generate_report(results, db_stats, output_path=word_path)
    print(f"   ✔ Word Summary Report:    {word_path}")
    
    # 4. Standalone Interactive HTML Report
    html_path = os.path.join(out_dir, "matching_report.html")
    HTMLReporter.generate_report(results, db_stats, output_path=html_path)
    print(f"   ✔ HTML Dashboard Report:  {html_path}")

def handle_stats(args):
    db = Database(args.db)
    docs = db.get_all_documents()
    total = len(docs)
    
    print("========================================================================")
    print("                      LIBRARY INDEX STATISTICS                         ")
    print("========================================================================")
    print(f"Total Indexed Documents: {total}")
    if total == 0:
        return
        
    # Breakdown by document type
    doc_types = {}
    total_pages = 0
    with_doi = 0
    with_authors = 0
    with_journal = 0
    
    for d in docs:
        dtype = d["document_type"] or "Unknown"
        doc_types[dtype] = doc_types.get(dtype, 0) + 1
        total_pages += d["page_count"] or 0
        if d["doi"]:
            with_doi += 1
        if d["authors"]:
            with_authors += 1
        if d["journal"]:
            with_journal += 1
            
    print("\nDocument Type Breakdown:")
    for dtype, count in doc_types.items():
        percentage = (count / total * 100)
        print(f"  - {dtype:<20}: {count:4d} ({percentage:5.1f}%)")
        
    print("\nMetadata Completeness Stats:")
    print(f"  - Documents with DOI:       {with_doi:4d} ({(with_doi/total*100):5.1f}%)")
    print(f"  - Documents with Authors:   {with_authors:4d} ({(with_authors/total*100):5.1f}%)")
    print(f"  - Documents with Journal:   {with_journal:4d} ({(with_journal/total*100):5.1f}%)")
    print(f"  - Total Pages in Library:    {total_pages:4d} (Avg {total_pages/total:.1f} per doc)")
    
    exact_dups = len(db.get_exact_duplicates())
    pot_dups = len(db.get_potential_duplicates())
    print(f"  - Exact Duplicate Groups:   {exact_dups:4d}")
    print(f"  - Potential Title Duplicates:{pot_dups:4d}")
    print("========================================================================")

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="Research Archive Matcher (RAM) - Offline Research Document Intelligence Platform"
    )
    parser.add_argument("--db", default="index.db", help="Path to SQLite index database file (default: index.db)")
    
    subparsers = parser.add_subparsers(title="Commands", dest="command")
    
    # gui
    subparsers.add_parser("gui", help="Launch the Graphical User Interface (default)")
    
    # init
    subparsers.add_parser("init", help="Initialize or clean-start the local index database")
    
    # scan
    parser_scan = subparsers.add_parser("scan", help="Scan a directory for PDF files and index them")
    parser_scan.add_argument("folder", help="Directory containing PDF files")
    parser_scan.add_argument("--online", action="store_true", help="Enrich metadata using online Crossref API lookup (optional)")
    
    # search
    parser_search = subparsers.add_parser("search", help="Search indexed publications")
    parser_search.add_argument("query", help="Text query to search for")
    parser_search.add_argument("--field", default="all", choices=["all", "title", "authors", "doi", "journal", "abstract", "keywords", "year"],
                               help="Field to restrict search to (default: all)")
    
    # match
    parser_match = subparsers.add_parser("match", help="Match target publications list against local index and generate reports")
    parser_match.add_argument("targets", help="File containing target publications to match (Excel, Word, or Text)")
    parser_match.add_argument("--threshold", type=float, default=70.0, help="Similarity match threshold percentage (default: 70.0)")
    parser_match.add_argument("--out-dir", default="reports", help="Directory where output reports will be saved (default: reports)")
    
    # stats
    subparsers.add_parser("stats", help="Show statistics of the indexed library")
    
    args = parser.parse_args()
    
    # Fallback to GUI if no command is specified
    if not args.command:
        try:
            from src.ui.main_window import launch_gui
            print("🚀 Launching the Graphical User Interface...")
            launch_gui()
            sys.exit(0)
        except Exception as e:
            print(f"⚠️ Could not launch GUI (headless environment or tkinter missing). Showing CLI help:\n")
            parser.print_help()
            sys.exit(1)
        
    if args.command == "gui":
        try:
            from src.ui.main_window import launch_gui
            print("🚀 Launching the Graphical User Interface...")
            launch_gui()
        except Exception as e:
            print(f"❌ Error: Could not launch GUI. Tkinter or display server may be unavailable: {e}")
            sys.exit(1)
    elif args.command == "init":
        handle_init(args)
    elif args.command == "scan":
        handle_scan(args)
    elif args.command == "search":
        handle_search(args)
    elif args.command == "match":
        handle_match(args)
    elif args.command == "stats":
        handle_stats(args)

if __name__ == "__main__":
    main()
