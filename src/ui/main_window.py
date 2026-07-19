import os
import sys
import threading
import logging
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from src.indexer.database import Database
from src.extractors.metadata import MetadataExtractor
from src.matcher.publication_match import PublicationMatcher
from src.reports.excel_report import ExcelReporter
from src.reports.word_report import WordReporter
from src.reports.html_report import HTMLReporter

# Queue for thread-safe GUI updates
gui_queue = queue.Queue()

class QueueHandler(logging.Handler):
    """
    Redirects logger outputs to a queue so the GUI can safely print logs
    from background threads without thread-safety crashes.
    """
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record) + "\n")


class ResearchArchiveMatcherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Research Archive Matcher (RAM)")
        self.root.geometry("1000x700")
        self.root.minimum_size = (900, 600)
        
        # Configure app style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Define clean, professional color scheme (Classic Navy & Cool Gray)
        self.style.configure(".", font=("Segoe UI", 10))
        self.style.configure("TFrame", background="#f5f7fa")
        self.style.configure("TLabel", background="#f5f7fa", foreground="#333333")
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#1F4E79")
        self.style.configure("Sub.TLabel", font=("Segoe UI", 10, "italic"), foreground="#555555")
        
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), borderwidth=1, foreground="#ffffff", background="#1F4E79")
        self.style.map("TButton",
                       foreground=[("active", "#ffffff"), ("disabled", "#999999")],
                       background=[("active", "#153d5a"), ("disabled", "#cccccc")])
                       
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), foreground="#ffffff", background="#2e7d32")
        self.style.map("Accent.TButton",
                       foreground=[("active", "#ffffff")],
                       background=[("active", "#1e5a22")]) # Success green
        
        # DB initialization
        self.db_path = "index.db"
        self.db = Database(self.db_path)
        
        # Build Menu and UI layout
        self.create_menu()
        self.create_widgets()
        
        # Start background polling for queue-driven log updates
        self.root.after(100, self.poll_queue)
        
        # Setup logging redirection
        self.setup_logging()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Initialize Database", command=self.gui_init_db)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About RAM", command=self.show_about_dialog)

    def gui_init_db(self):
        confirm = messagebox.askyesno("Initialize Database", "Are you sure you want to initialize the local SQLite index?\n\nThis will clear any existing document metadata in 'index.db' and start fresh.")
        if confirm:
            self.db.clear()
            self.load_indexed_documents()
            messagebox.showinfo("Success", "Local database index initialized successfully!")

    def show_about_dialog(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About Research Archive Matcher")
        about_window.geometry("500x320")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Center about window relative to root
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        x = root_x + (root_w - 500) // 2
        y = root_y + (root_h - 320) // 2
        about_window.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(about_window, padding=20)
        frame.pack(fill="both", expand=True)
        
        title_lbl = ttk.Label(frame, text="Research Archive Matcher (RAM)", font=("Segoe UI", 14, "bold"), foreground="#1F4E79")
        title_lbl.pack(pady=(0, 5))
        
        ver_lbl = ttk.Label(frame, text="Version 1.0.0 | Open Source (MIT)", font=("Segoe UI", 9, "bold"))
        ver_lbl.pack(pady=(0, 10))
        
        desc_lbl = tk.Text(frame, font=("Segoe UI", 9), wrap="word", bg="#f5f7fa", fg="#333333", height=6, bd=0, highlightthickness=0)
        desc_lbl.insert("1.0", "An offline-first, modern desktop application designed for researchers, lecturers, and librarians. "
                               "RAM allows you to recursively scan folders of PDFs, extract title, authors, DOI, abstract, keywords, "
                               "and year using layout and font-size analysis, automatically check for duplicates (using SHA-256 hashes), "
                               "and match external publication lists (from Excel, Word, or TXT) against your local index using "
                               "high-performance fuzzy NLP similarity metrics.")
        desc_lbl.config(state="disabled")
        desc_lbl.pack(fill="x", pady=5)
        
        pub_lbl = ttk.Label(frame, text="Developer & Publisher: David Sanda (Sandadatasaver)", font=("Segoe UI", 9, "italic"))
        pub_lbl.pack(anchor="w", pady=2)
        
        git_lbl = ttk.Label(frame, text="Website: https://github.com/sandadatasaver/Research-Archive-Matcher", font=("Segoe UI", 9), foreground="#1F4E79", cursor="hand2")
        git_lbl.pack(anchor="w", pady=(0, 15))
        
        # Close button
        close_btn = ttk.Button(frame, text="Close", command=about_window.destroy)
        close_btn.pack(side="bottom")

    def create_widgets(self):
        # Initialize Status Bar Variable at the very beginning to avoid order-of-initialization errors
        self.status_var = tk.StringVar(value="System Ready")
        
        # Header banner frame
        header_frame = ttk.Frame(self.root, padding=15, style="TFrame")
        header_frame.pack(fill="x")
        
        title_lbl = ttk.Label(header_frame, text="Research Archive Matcher", style="Header.TLabel")
        title_lbl.pack(anchor="w")
        sub_lbl = ttk.Label(header_frame, text="Offline Research Document Intelligence & Matching Platform", style="Sub.TLabel")
        sub_lbl.pack(anchor="w")
        
        # Notebook (Tabbed Interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Tab 1: Library Scanner
        self.scan_tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.scan_tab, text=" Library Scanner ")
        self.build_scan_tab()
        
        # Tab 2: Library Explorer
        self.explore_tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.explore_tab, text=" Library Explorer ")
        self.build_explore_tab()
        
        # Tab 3: Target Matcher
        self.match_tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.match_tab, text=" Publication Matcher ")
        self.build_match_tab()
        
        # Status Bar Widget Packing
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w", padding=5)
        status_bar.pack(fill="x", side="bottom")

    def build_scan_tab(self):
        # Folder selection widgets
        folder_frame = ttk.LabelFrame(self.scan_tab, text="Select local PDF Library Folder", padding=10)
        folder_frame.pack(fill="x", pady=(0, 10))
        
        self.scan_folder_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.scan_folder_var, font=("Segoe UI", 10))
        folder_entry.pack(fill="x", side="left", expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(folder_frame, text="Browse Folder", command=self.browse_scan_folder)
        browse_btn.pack(side="right")
        
        # Options
        options_frame = ttk.Frame(self.scan_tab)
        options_frame.pack(fill="x", pady=5)
        
        self.online_enrich_var = tk.BooleanVar(value=False)
        online_chk = ttk.Checkbutton(options_frame, text="Enrich metadata using Crossref API lookup (Online)", variable=self.online_enrich_var)
        online_chk.pack(side="left")
        
        # Action Buttons
        btn_frame = ttk.Frame(self.scan_tab)
        btn_frame.pack(fill="x", pady=10)
        
        self.start_scan_btn = ttk.Button(btn_frame, text="Initialize & Start Scan", command=self.start_library_scan)
        self.start_scan_btn.pack(side="left", padx=(0, 10))
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.scan_tab, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=5)
        
        # Terminal Log Output
        log_frame = ttk.LabelFrame(self.scan_tab, text="Extraction & Scanner Logs Output", padding=5)
        log_frame.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(log_frame, font=("Consolas", 9), wrap="word", bg="#1e1e1e", fg="#d4d4d4")
        self.log_text.pack(fill="both", expand=True, side="left")
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(fill="y", side="right")
        self.log_text.config(yscrollcommand=scrollbar.set)

    def build_explore_tab(self):
        # Search panel
        search_frame = ttk.Frame(self.explore_tab)
        search_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(search_frame, text="Search Index:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_library_explorer())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", padx=5)
        
        ttk.Label(search_frame, text="Field:").pack(side="left", padx=(10, 5))
        self.search_field_var = tk.StringVar(value="all")
        field_cb = ttk.Combobox(search_frame, textvariable=self.search_field_var, values=["all", "title", "authors", "doi", "journal", "year", "document_type"], state="readonly", width=12)
        field_cb.pack(side="left")
        field_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_library_explorer())
        
        refresh_btn = ttk.Button(search_frame, text="Refresh Grid", command=self.load_indexed_documents)
        refresh_btn.pack(side="right")
        
        # Explorer Table (Treeview)
        tree_frame = ttk.Frame(self.explore_tab)
        tree_frame.pack(fill="both", expand=True)
        
        columns = ("title", "authors", "doi", "journal", "year", "type")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        self.tree.heading("title", text="Document Title")
        self.tree.heading("authors", text="Authors")
        self.tree.heading("doi", text="DOI")
        self.tree.heading("journal", text="Journal")
        self.tree.heading("year", text="Year")
        self.tree.heading("type", text="Type")
        
        self.tree.column("title", width=300, minwidth=150, stretch=True)
        self.tree.column("authors", width=150, minwidth=100)
        self.tree.column("doi", width=120, minwidth=80)
        self.tree.column("journal", width=150, minwidth=100)
        self.tree.column("year", width=60, minwidth=50, anchor="center")
        self.tree.column("type", width=100, minwidth=80, anchor="center")
        
        self.tree.pack(fill="both", expand=True, side="left")
        
        scrollbar = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        scrollbar.pack(fill="y", side="right")
        self.tree.config(yscrollcommand=scrollbar.set)
        
        # Initial load
        self.load_indexed_documents()

    def build_match_tab(self):
        # Target list file browser
        target_frame = ttk.LabelFrame(self.match_tab, text="1. Select Target Publication List File (Excel, Word, or TXT)", padding=10)
        target_frame.pack(fill="x", pady=(0, 15))
        
        self.target_file_var = tk.StringVar()
        target_entry = ttk.Entry(target_frame, textvariable=self.target_file_var, font=("Segoe UI", 10))
        target_entry.pack(fill="x", side="left", expand=True, padx=(0, 5))
        
        target_btn = ttk.Button(target_frame, text="Browse File", command=self.browse_target_file)
        target_btn.pack(side="right")
        
        # Matching threshold slider
        thresh_frame = ttk.LabelFrame(self.match_tab, text="2. Configure Alignment Parameters", padding=10)
        thresh_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(thresh_frame, text="Fuzzy Similarity Match Threshold:").pack(side="left", padx=(0, 10))
        self.thresh_var = tk.IntVar(value=70)
        slider = ttk.Scale(thresh_frame, from_=50, to=100, orient="horizontal", variable=self.thresh_var, command=self.update_thresh_label)
        slider.pack(side="left", fill="x", expand=True, padx=10)
        
        self.thresh_lbl = ttk.Label(thresh_frame, text="70%", font=("Segoe UI", 10, "bold"))
        self.thresh_lbl.pack(side="left")
        
        # Output directory selection
        out_frame = ttk.LabelFrame(self.match_tab, text="3. Choose Deliverables Output Folder", padding=10)
        out_frame.pack(fill="x", pady=(0, 20))
        
        self.out_dir_var = tk.StringVar(value="reports")
        out_entry = ttk.Entry(out_frame, textvariable=self.out_dir_var, font=("Segoe UI", 10))
        out_entry.pack(fill="x", side="left", expand=True, padx=(0, 5))
        
        out_btn = ttk.Button(out_frame, text="Browse Folder", command=self.browse_out_dir)
        out_btn.pack(side="right")
        
        # Run Button
        self.run_match_btn = ttk.Button(self.match_tab, text="▶ Run Alignments & Compile Reports", style="Accent.TButton", padding=10, command=self.start_publication_match)
        self.run_match_btn.pack(fill="x", pady=10)

    # --- Button Command Handlers ---
    
    def browse_scan_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.scan_folder_var.set(folder)

    def browse_target_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Supported Formats", "*.xlsx;*.xls;*.docx;*.txt"), ("Excel Sheets", "*.xlsx;*.xls"), ("Word Documents", "*.docx"), ("Text Files", "*.txt")])
        if file_path:
            self.target_file_var.set(file_path)

    def browse_out_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.out_dir_var.set(folder)

    def update_thresh_label(self, val):
        self.thresh_lbl.config(text=f"{int(float(val))}%")

    def setup_logging(self):
        # Redirect custom root log prints to our queue-based logger handler
        self.queue_handler = QueueHandler(gui_queue)
        self.queue_handler.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger().addHandler(self.queue_handler)

    def poll_queue(self):
        # Periodically read log outputs from queue and insert into UI Log screen
        try:
            while True:
                msg = gui_queue.get_nowait()
                self.log_text.insert(tk.END, msg)
                self.log_text.see(tk.END)
                gui_queue.task_done()
        except queue.Empty:
            pass
        self.root.after(100, self.poll_queue)

    # --- Main Workflow Threads ---

    def start_library_scan(self):
        folder = self.scan_folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid directory containing your PDF library files.")
            return
            
        self.start_scan_btn.config(state="disabled")
        self.progress_var.set(0)
        self.log_text.delete("1.0", tk.END)
        self.status_var.set("Scanning PDFs folder...")
        
        # Run scanner logic in a background thread to keep GUI responsive
        thread = threading.Thread(target=self.run_library_scan_worker, args=(folder,))
        thread.daemon = True
        thread.start()

    def run_library_scan_worker(self, folder):
        try:
            pdf_files = []
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        pdf_files.append(os.path.join(root, f))
            
            total_files = len(pdf_files)
            if total_files == 0:
                gui_queue.put("❌ No PDF documents found in selected folder.\n")
                self.root.after(0, lambda: messagebox.showinfo("No Files", "No PDF files were discovered in the selected library directory."))
                self.root.after(0, lambda: self.start_scan_btn.config(state="normal"))
                self.root.after(0, lambda: self.status_var.set("Ready"))
                return
                
            gui_queue.put(f"🔍 Discovered {total_files} PDF papers. Beginning extraction...\n")
            
            online_enrich = self.online_enrich_var.get()
            indexed_count = 0
            
            for i, path in enumerate(pdf_files, 1):
                rel_path = os.path.relpath(path, folder)
                gui_queue.put(f"[{i}/{total_files}] Processing: {rel_path}...")
                
                try:
                    extractor = MetadataExtractor(path)
                    meta = extractor.extract(online_enrich=online_enrich)
                    success = self.db.add_document(meta)
                    if success:
                        gui_queue.put(f" ✔ [{meta['document_type']}]\n")
                        indexed_count += 1
                    else:
                        gui_queue.put(" ❌ (Database Index Error)\n")
                except Exception as e:
                    gui_queue.put(f" ❌ (Parsing Error: {e})\n")
                    
                # Update progress bar safely
                pct = (i / total_files) * 100
                self.root.after(0, lambda p=pct: self.progress_var.set(p))
            
            gui_queue.put(f"\n✔ Process completed! Successfully indexed {indexed_count} papers into local index.\n")
            
            # Auto refresh grid
            self.root.after(0, self.load_indexed_documents)
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Scanning complete!\nSuccessfully indexed {indexed_count} documents."))
            
        except Exception as ex:
            gui_queue.put(f"❌ Core scan thread crashed: {ex}\n")
        finally:
            self.root.after(0, lambda: self.start_scan_btn.config(state="normal"))
            self.root.after(0, lambda: self.status_var.set("Ready"))

    def load_indexed_documents(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        docs = self.db.get_all_documents()
        for doc in docs:
            self.tree.insert("", tk.END, values=(
                doc["title"] or "No Title",
                doc["authors"] or "N/A",
                doc["doi"] or "N/A",
                doc["journal"] or "N/A",
                doc["year"] or "N/A",
                doc["document_type"] or "Unknown"
            ))
        self.status_var.set(value=f"Database loaded: {len(docs)} papers indexed.")

    def filter_library_explorer(self):
        query = self.search_var.get().strip()
        field = self.search_field_var.get()
        
        if not query:
            self.load_indexed_documents()
            return
            
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        results = self.db.search(query, field)
        for doc in results:
            self.tree.insert("", tk.END, values=(
                doc["title"] or "No Title",
                doc["authors"] or "N/A",
                doc["doi"] or "N/A",
                doc["journal"] or "N/A",
                doc["year"] or "N/A",
                doc["document_type"] or "Unknown"
            ))
        self.status_var.set(value=f"Search matches: {len(results)} found.")

    def start_publication_match(self):
        targets_file = self.target_file_var.get().strip()
        out_dir = self.out_dir_var.get().strip()
        
        if self.db.get_document_count() == 0:
            messagebox.showerror("Error", "Your local library index is currently empty. Please run a Library Scan first!")
            return
            
        if not targets_file or not os.path.exists(targets_file):
            messagebox.showerror("Error", "Please specify a valid target publication list file.")
            return
            
        self.run_match_btn.config(state="disabled")
        self.status_var.set("Performing publication alignment matches...")
        
        # Run matching logic in a background thread to prevent GUI freezing
        thread = threading.Thread(target=self.run_publication_match_worker, args=(targets_file, out_dir))
        thread.daemon = True
        thread.start()

    def run_publication_match_worker(self, targets_file, out_dir):
        try:
            threshold = float(self.thresh_var.get())
            matcher = PublicationMatcher(self.db, threshold=threshold)
            results = matcher.match(targets_file)
            
            # Generate sheets and reports
            ExcelReporter.export_matching_results(results, output_dir=out_dir)
            
            exact_dups = self.db.get_exact_duplicates()
            potential_dups = self.db.get_potential_duplicates()
            ExcelReporter.export_duplicates_report(exact_dups, potential_dups, output_dir=out_dir)
            
            db_stats = {"total_docs": self.db.get_document_count()}
            
            word_path = os.path.join(out_dir, "matching_report.docx")
            WordReporter.generate_report(results, db_stats, output_path=word_path)
            
            html_path = os.path.join(out_dir, "matching_report.html")
            HTMLReporter.generate_report(results, db_stats, output_path=html_path)
            
            matched_len = len(results.get("matched", []))
            unmatched_len = len(results.get("unmatched", []))
            
            # Auto-open reports directory in Windows / macOS explorer
            try:
                if sys.platform == "win32":
                    os.startfile(os.path.abspath(out_dir))
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.call(["open", os.path.abspath(out_dir)])
            except Exception:
                pass
                
            self.root.after(0, lambda: messagebox.showinfo(
                "Matching Finished", 
                f"Matching completed successfully!\n\n"
                f" - Successfully Matched: {matched_len} citations\n"
                f" - Unmatched/Missing:    {unmatched_len} citations\n\n"
                f"All reports have been generated in your output directory: '{out_dir}'."
            ))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Matching Error", f"An error occurred during matching: {e}"))
        finally:
            self.root.after(0, lambda: self.run_match_btn.config(state="normal"))
            self.root.after(0, lambda: self.status_var.set("Ready"))


def launch_gui():
    root = tk.Tk()
    app = ResearchArchiveMatcherGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
