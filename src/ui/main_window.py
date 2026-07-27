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
from src.readers.pdf_reader import PDFReader
from src.search.page_search import PageSearchService
from src.reports.excel_report import ExcelReporter
from src.reports.word_report import WordReporter
from src.reports.html_report import HTMLReporter
from src.ui.pdf_preview import PDFPreviewWindow

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


def get_resource_path(relative_path):
    """
    Gets absolute path to resources, supporting both local execution
    and bundled PyInstaller environments.
    """
    try:
        # PyInstaller creates a temporary directory and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Resolve to workspace root
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Try different fallbacks if not found
    path = os.path.join(base_path, relative_path)
    if not os.path.exists(path):
        # Fallback to local execution directory
        path = os.path.join(os.path.abspath("."), relative_path)
    return path


class ResearchArchiveMatcherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Research Archive Matcher (RAM)")
        self.root.geometry("1000x600")
        self.root.minimum_size = (900, 500)
        
        # Configure app style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Define clean, professional color scheme (Classic Navy, Gold, & Cool Gray)
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
        
        # Set Window Taskbar and Application Icons
        ico_path = get_resource_path("logo.ico")
        logo_path = get_resource_path("docs/logo_final.png")
        
        # Windows-specific native titlebar and taskbar icon
        if sys.platform == "win32" and os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception as e:
                print(f"ICO load error: {e}")
        elif os.path.exists(logo_path):
            try:
                self.icon_photo = tk.PhotoImage(file=logo_path)
                self.root.iconphoto(False, self.icon_photo)
            except Exception as e:
                print(f"PNG Icon load error: {e}")
                
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
        help_menu.add_command(label="User Guide / Navigation Help", command=self.show_help_dialog)
        help_menu.add_command(label="Frequently Asked Questions (FAQ)", command=self.show_faq_dialog)
        help_menu.add_separator()
        help_menu.add_command(label="About RAM", command=self.show_about_dialog)

    def set_window_icon(self, window):
        """Apply the RAM logo to child windows as well as the main window."""
        ico_path = get_resource_path("logo.ico")
        png_path = get_resource_path("docs/logo_final.png")

        if sys.platform == "win32" and os.path.exists(ico_path):
            try:
                window.iconbitmap(ico_path)
                return
            except Exception:
                pass

        if os.path.exists(png_path):
            try:
                window._ram_icon = tk.PhotoImage(file=png_path)
                window.iconphoto(False, window._ram_icon)
            except Exception:
                pass

    def gui_init_db(self):
        confirm = messagebox.askyesno("Initialize Database", "Are you sure you want to initialize the local SQLite index?\n\nThis will clear any existing document metadata in 'index.db' and start fresh.")
        if confirm:
            self.db.clear()
            self.load_indexed_documents()
            messagebox.showinfo("Success", "Local database index initialized successfully!")

    def show_about_dialog(self):
        about_window = tk.Toplevel(self.root)
        self.set_window_icon(about_window)
        about_window.title("About Research Archive Matcher")
        about_window.geometry("680x600")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()

        frame = ttk.Frame(about_window, padding=24)
        frame.pack(fill="both", expand=True)

        logo_path = get_resource_path("docs/logo_final.png")
        if os.path.exists(logo_path):
            try:
                self.about_logo = tk.PhotoImage(file=logo_path).subsample(20, 20)
                ttk.Label(frame, image=self.about_logo).pack(pady=(0, 8))
            except Exception:
                pass

        ttk.Label(
            frame,
            text="Research Archive Matcher (RAM)",
            font=("Segoe UI", 17, "bold"),
            foreground="#1F4E79",
        ).pack()
        ttk.Label(
            frame,
            text="Version 1.0.2 | MIT License",
            font=("Segoe UI", 9, "bold"),
            foreground="#555555",
        ).pack(pady=(3, 14))

        vision_frame = tk.LabelFrame(
            frame,
            text="Our Purpose",
            font=("Segoe UI", 9, "bold"),
            bg="#fff9e6",
            fg="#b38600",
            padx=14,
            pady=10,
        )
        vision_frame.pack(fill="x", pady=(0, 14))
        tk.Label(
            vision_frame,
            text=(
                "This open source tool is Provided for Students, Lecturers, "
                "Editors and Researchers alike 100% Free for the glory of Jesus my Saviour"
            ),
            font=("Segoe UI", 10, "bold", "italic"),
            fg="#1F4E79",
            bg="#fff9e6",
            wraplength=580,
            justify="center",
        ).pack()

        description = (
            "RAM is an offline-first research document intelligence platform. "
            "It scans PDF archives, extracts metadata and page text, stores a "
            "local SQLite index, searches words and phrases by page, matches "
            "external publication lists, detects duplicates, and produces Excel, "
            "Word, and HTML reports."
        )
        ttk.Label(frame, text=description, wraplength=610, justify="left").pack(
            anchor="w", pady=(0, 12)
        )

        features = (
            "Current capabilities:\n"
            "• Page-aware PDF full-text search\n"
            "• Article, page, snippet, and similarity results\n"
            "• Metadata extraction and SQLite indexing\n"
            "• DOI and optional Crossref enrichment\n"
            "• Exact and potential duplicate detection\n"
            "• Excel, Word, and HTML reporting\n"
            "• Windows, Linux, and macOS build support"
        )
        ttk.Label(frame, text=features, justify="left").pack(
            anchor="w", pady=(0, 12)
        )

        ttk.Label(
            frame,
            text="Developed and published by Bishop David Sanda Ph.D",
            font=("Segoe UI", 9, "bold"),
            foreground="#1F4E79",
        ).pack(anchor="w")
        ttk.Label(
            frame,
            text="GitHub: https://github.com/sandadatasaver/Research-Archive-Matcher",
            foreground="#1F4E79",
        ).pack(anchor="w", pady=(2, 12))
        ttk.Button(frame, text="Close", command=about_window.destroy).pack()

    def _read_help_file(self, relative_path):
        path = get_resource_path(relative_path)
        try:
            with open(path, "r", encoding="utf-8") as stream:
                return stream.read()
        except OSError:
            return "Help content is not available."

    def _make_help_text(self, parent, content):
        text_area = tk.Text(
            parent,
            font=("Segoe UI", 10),
            wrap="word",
            bg="#ffffff",
            fg="#333333",
            padx=12,
            pady=12,
        )
        text_area.pack(fill="both", expand=True, side="left", padx=(0, 5))
        scrollbar = ttk.Scrollbar(parent, command=text_area.yview)
        scrollbar.pack(fill="y", side="right")
        text_area.config(yscrollcommand=scrollbar.set)

        text_area.tag_configure(
            "heading",
            foreground="#1F4E79",
            font=("Segoe UI", 13, "bold"),
            spacing1=8,
            spacing3=5,
        )
        text_area.tag_configure(
            "subheading",
            foreground="#1F4E79",
            font=("Segoe UI", 11, "bold"),
            spacing1=6,
            spacing3=3,
        )
        text_area.tag_configure(
            "question",
            foreground="#1F4E79",
            font=("Segoe UI", 10, "bold"),
        )

        for line in content.splitlines():
            stripped = line.strip()
            tag = None
            if stripped.startswith("# "):
                line = stripped[2:]
                tag = "heading"
            elif stripped.startswith("## "):
                line = stripped[3:]
                tag = "subheading"
            elif stripped.startswith("Q:"):
                tag = "question"

            start_index = text_area.index("end-1c")
            text_area.insert("end", line + "\n")
            end_index = text_area.index("end-1c")
            if tag:
                text_area.tag_add(tag, start_index, end_index)

        text_area.config(state="disabled")
        return text_area

    def show_help_dialog(self, selected_tab=0):
        help_window = tk.Toplevel(self.root)
        self.set_window_icon(help_window)
        help_window.title("RAM - Help and FAQ")
        help_window.geometry("760x600")
        help_window.transient(self.root)
        help_window.grab_set()

        frame = ttk.Frame(help_window, padding=16)
        frame.pack(fill="both", expand=True)

        logo_path = get_resource_path("docs/logo_final.png")
        if os.path.exists(logo_path):
            try:
                self.help_logo = tk.PhotoImage(file=logo_path).subsample(24, 24)
                ttk.Label(frame, image=self.help_logo).pack(pady=(0, 5))
            except Exception:
                pass

        ttk.Label(
            frame,
            text="Research Archive Matcher — Help and FAQ",
            font=("Segoe UI", 14, "bold"),
            foreground="#1F4E79",
        ).pack(pady=(0, 10))

        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True)
        help_tab = ttk.Frame(notebook, padding=6)
        faq_tab = ttk.Frame(notebook, padding=6)
        notebook.add(help_tab, text="Quick Help")
        notebook.add(faq_tab, text="FAQ")
        self._make_help_text(help_tab, self._read_help_file("docs/usage.md"))
        self._make_help_text(faq_tab, self._read_help_file("docs/faq.md"))
        notebook.select(selected_tab)

        ttk.Button(frame, text="Close", command=help_window.destroy).pack(
            pady=(10, 0)
        )

    def show_faq_dialog(self):
        self.show_help_dialog(selected_tab=1)

    def create_widgets(self):
        # Initialize Status Bar Variable at the very beginning to avoid order-of-initialization errors
        self.status_var = tk.StringVar(value="System Ready")
        
        # Header banner frame
        header_frame = ttk.Frame(self.root, padding=15, style="TFrame")
        header_frame.pack(fill="x")
        
        # Pack Logo on left and titles on right inside the header banner
        logo_path = get_resource_path("docs/logo_final.png")
        if os.path.exists(logo_path):
            try:
                self.header_logo = tk.PhotoImage(file=logo_path).subsample(24, 24)
                logo_lbl = ttk.Label(header_frame, image=self.header_logo)
                logo_lbl.pack(side="left", padx=(0, 15))
            except Exception:
                pass
                
        text_banner_frame = ttk.Frame(header_frame, style="TFrame")
        text_banner_frame.pack(side="left", fill="both", expand=True)
        
        title_lbl = ttk.Label(text_banner_frame, text="Research Archive Matcher", style="Header.TLabel")
        title_lbl.pack(anchor="w")
        sub_lbl = ttk.Label(text_banner_frame, text="Offline Research Document Intelligence & Matching Platform", style="Sub.TLabel")
        sub_lbl.pack(anchor="w")

        # Reserved header action area for About and future user preferences.
        header_actions = ttk.Frame(header_frame, style="TFrame")
        header_actions.pack(side="right", padx=(10, 0))
        ttk.Button(
            header_actions,
            text="About",
            command=self.show_about_dialog,
        ).pack(side="right", padx=3)
        ttk.Button(
            header_actions,
            text="Help / FAQ",
            command=self.show_help_dialog,
        ).pack(side="right", padx=3)
        
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

        # Tab 3: Page Full-Text Search
        self.search_tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.search_tab, text=" Full-Text Search ")
        self.build_fulltext_search_tab()
        
        # Tab 4: Target Matcher
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
        
        # Fix Sidebar Scroller Responsiveness: Pack Scrollbar first to anchor it to the absolute right side
        scrollbar = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        scrollbar.pack(fill="y", side="right")
        
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.config(yscrollcommand=scrollbar.set)
        
        # Initial load
        self.load_indexed_documents()

    def build_fulltext_search_tab(self):
        """Build the page-level full-text search tab."""
        query_frame = ttk.LabelFrame(
            self.search_tab,
            text="Search PDF Page Text",
            padding=10,
        )
        query_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(query_frame, text="Query:").pack(side="left", padx=(0, 5))
        self.page_search_var = tk.StringVar()
        query_entry = ttk.Entry(
            query_frame,
            textvariable=self.page_search_var,
            width=48,
        )
        query_entry.pack(side="left", fill="x", expand=True, padx=5)
        query_entry.bind("<Return>", lambda event: self.start_page_search())

        self.page_phrase_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            query_frame,
            text="Exact phrase",
            variable=self.page_phrase_var,
        ).pack(side="left", padx=8)

        ttk.Label(query_frame, text="Minimum score:").pack(side="left")
        self.page_score_var = tk.IntVar(value=70)
        ttk.Spinbox(
            query_frame,
            from_=0,
            to=100,
            textvariable=self.page_score_var,
            width=5,
        ).pack(side="left", padx=5)

        self.page_search_button = ttk.Button(
            query_frame,
            text="Search",
            command=self.start_page_search,
        )
        self.page_search_button.pack(side="right")

        results_frame = ttk.LabelFrame(
            self.search_tab,
            text="Page-Level Results",
            padding=5,
        )
        results_frame.pack(fill="both", expand=True)

        columns = ("title", "page", "score", "match", "snippet", "path")
        self.page_search_tree = ttk.Treeview(
            results_frame,
            columns=columns,
            show="headings",
        )
        headings = {
            "title": "Article",
            "page": "Page",
            "score": "Score",
            "match": "Match Type",
            "snippet": "Snippet",
            "path": "PDF Path",
        }
        widths = {
            "title": 220,
            "page": 55,
            "score": 70,
            "match": 120,
            "snippet": 430,
            "path": 260,
        }
        for column in columns:
            self.page_search_tree.heading(column, text=headings[column])
            self.page_search_tree.column(column, width=widths[column])

        scrollbar = ttk.Scrollbar(
            results_frame,
            command=self.page_search_tree.yview,
        )
        scrollbar.pack(fill="y", side="right")
        self.page_search_tree.pack(fill="both", expand=True, side="left")
        self.page_search_tree.config(yscrollcommand=scrollbar.set)
        self.page_search_tree.bind(
            "<Double-1>",
            self.open_page_search_result,
        )

        ttk.Label(
            self.search_tab,
            text="Double-click a result to open its PDF. The page number is shown in the result table.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(8, 0))

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

    def start_page_search(self):
        query = self.page_search_var.get().strip()

        if not query:
            messagebox.showwarning(
                "Search",
                "Enter a word, phrase, or sentence to search.",
            )
            return

        if self.db.get_page_count() == 0:
            messagebox.showwarning(
                "Page index is empty",
                "Run a PDF scan with the page-aware version of RAM first.",
            )
            return

        self.page_search_button.config(state="disabled")
        self.status_var.set("Searching PDF pages...")

        thread = threading.Thread(
            target=self.run_page_search_worker,
            args=(query,),
            daemon=True,
        )
        thread.start()

    def run_page_search_worker(self, query):
        try:
            results = PageSearchService(self.db).search(
                query,
                exact_phrase=self.page_phrase_var.get(),
                minimum_score=float(self.page_score_var.get()),
                limit=100,
            )
            self.root.after(
                0,
                lambda: self.show_page_search_results(results),
            )
        except Exception as error:
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Page Search Error",
                    str(error),
                ),
            )
        finally:
            self.root.after(
                0,
                lambda: self.page_search_button.config(state="normal"),
            )
            self.root.after(
                0,
                lambda: self.status_var.set("Ready"),
            )

    def show_page_search_results(self, results):
        for item in self.page_search_tree.get_children():
            self.page_search_tree.delete(item)

        for result in results:
            self.page_search_tree.insert(
                "",
                tk.END,
                values=(
                    result.title,
                    result.page_number,
                    f"{result.score:.1f}%",
                    result.match_type,
                    result.snippet,
                    result.file_path,
                ),
            )

        self.status_var.set(f"Page matches: {len(results)} found.")

    def open_page_search_result(self, _event=None):
        selection = self.page_search_tree.selection()
        if not selection:
            return

        values = self.page_search_tree.item(selection[0], "values")
        file_path = values[5]
        page_number = int(values[1])

        try:
            PDFPreviewWindow(
                self.root,
                file_path=file_path,
                page_number=page_number,
                query=self.page_search_var.get().strip(),
                exact_phrase=self.page_phrase_var.get(),
            )
        except Exception as error:
            messagebox.showerror("PDF Preview Error", str(error))

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
                        page_reader = PDFReader(path)
                        try:
                            pages = page_reader.get_page_texts()
                            stored_pages = self.db.replace_page_texts(
                                path,
                                pages,
                            )
                        finally:
                            page_reader.close()

                        gui_queue.put(
                            f" ✔ [{meta['document_type']}] "
                            f"({stored_pages} pages indexed)\n"
                        )
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
