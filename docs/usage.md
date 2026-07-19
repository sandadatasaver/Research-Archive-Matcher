# Research Archive Matcher (RAM) - Usage Guide

This guide describes how to run and make the most of **Research Archive Matcher (RAM)**.

## Running the Graphical User Interface (GUI)

RAM features a modern, fully responsive, multi-tab Graphical User Interface designed using Python's standard `tkinter` library. It requires zero third-party GUI dependencies, making it extremely lightweight and stable.

To launch the GUI, simply run the executable or Python launcher with no arguments:
```bash
python ram.py
```
Or use the explicit subcommand:
```bash
python ram.py gui
```

### GUI Layout & Features
1. **Library Scanner Tab**:
   * Choose a local folder of PDFs.
   * Toggle **Online Enrichment** (with Crossref API lookup).
   * Progress bar and real-time scrolling logging terminal showing layout and metadata parsing.
2. **Library Explorer Tab**:
   * View all indexed publications in an interactive grid (`ttk.Treeview`).
   * Search box filters through your library instantly by any field (Title, Author, DOI, Journal, Type, etc.).
3. **Publication Matcher Tab**:
   * Select a target publication list (Excel, Word, or TXT).
   * Use the fuzzy threshold slider (50% to 100%) to set matching strictness.
   * Run matching to compile results and automatically open the reports directory.

---

## Packaging the App as a Standalone Executable (.exe / Binary)

To share the app with Windows, macOS, or Linux users who don't have Python installed, you can compile the app using **PyInstaller**.

### Windows Packaging (Creating .exe)
1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. For a clean **Desktop GUI App** (no CMD window popup):
   ```bash
   pyinstaller --onefile --noconsole --name "RAM" ram.py
   ```
3. If you want to keep the **Console window open** in the background for debugging logs:
   ```bash
   pyinstaller --onefile --console --name "RAM" ram.py
   ```

### macOS & Linux Packaging (Creating native binaries)
1. Install PyInstaller on your target macOS or Linux system.
2. Run the build command:
   ```bash
   pyinstaller --onefile --noconsole --name "RAM" ram.py
   ```
3. This creates a native binary file called `RAM` (no extension on macOS/Linux) inside the `dist/` folder which can be launched instantly by double-clicking!

---

## Creating the Windows Installer (using Inno Setup)

Once you compile `RAM.exe` on Windows under the `dist/` folder:
1. Install [Inno Setup Compiler](https://jrsoftware.org/isdl.php).
2. Open `installer.iss` inside Inno Setup.
3. Click **Build ➔ Compile** (or `Ctrl + F9`).
4. An installer setup executable called `ResearchArchiveMatcher_Setup.exe` will be built inside the root directory!

---

## Command Line Interface (CLI)

If you prefer to run RAM inside headless environments (like servers or container arrays) or automate matching via shell scripts, use the command-line subcommands:

### 1. Initialize the Database
Initialize a clean local SQLite index database (`index.db`):
```bash
python ram.py init
```

### 2. Scan a Folder of PDFs
```bash
python ram.py scan /path/to/pdf/folder
```
*Optional Online Enrichment*:
```bash
python ram.py scan /path/to/pdf/folder --online
```

### 3. Display Library Statistics
```bash
python ram.py stats
```

### 4. Search Your Library
```bash
python ram.py search "Newcastle Disease"
python ram.py search "Doe" --field authors
```

### 5. Match a Target Publication List
```bash
python ram.py match samples/target_publications.xlsx --threshold 75.0 --out-dir reports
```

