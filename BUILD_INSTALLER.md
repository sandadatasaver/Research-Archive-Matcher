# Building the Windows Installer — RAM v1.2.0

Two updated files are ready: `installer.iss` and `installer_info.txt`.
I pulled the originals from your live repo and edited those, so no copying
and pasting was needed.

---

## 1. First — the OCR PNGs

**Yes, delete them.**

```powershell
cd C:\Projects\ResearchArchiveMatcher
```

```powershell
del ocr_page_2.png, ocr_page_302.png
```

They are OCR test output from earlier debugging, already removed from Git,
and now covered by the `ocr_page_*.png` rule you added. If the OCR code ever
writes them again they will simply be ignored.

---

## 2. Install the updated files

Copy `installer.iss` and `installer_info.txt` into your project folder,
replacing the existing ones.

### What changed in `installer.iss`

| Change | Why |
|---|---|
| Version `1.0.0` to `1.2.0` | Reflects page search, OCR and the icon fix |
| `LicenseFile=LICENSE` enabled | Was commented out; MIT licence now shown |
| Output name includes the version | `ResearchArchiveMatcher_Setup_1.2.0.exe` — no more overwriting old builds |
| Installs `docs\usage.md` and `docs\faq.md` | The in-app Help dialog reads these at runtime |
| Installs `README.md` and `LICENSE` | Standard practice |

### What changed in `installer_info.txt`

- Version updated to 1.2.0.
- Added the features that existed but were never mentioned: page-aware
  full-text search, phrase search, the highlighted PDF preview.
- Added a clear **OCR section** explaining that it is optional, where to get
  Tesseract, and that RAM works fully without it.
- Added a "New in this version" summary.
- Stated explicitly that documents are never uploaded.

Both were validated: sections balanced, no undefined macros, and every
referenced file present.

---

## 3. Build the executable

**Important:** the standard PyInstaller command **will not include OCR
support.** `pytesseract` is imported lazily inside a function, so PyInstaller
cannot detect it by scanning the code.

Use this command, which adds the hidden imports:

```powershell
cd C:\Projects\ResearchArchiveMatcher
```

```powershell
pip install pyinstaller pytesseract
```

```powershell
pyinstaller --onefile --noconsole --paths=. --add-data "docs;docs" --add-data "logo.ico;." --icon=logo.ico --hidden-import=pytesseract --hidden-import=PIL._tkinter_finder --name "RAM" ram.py
```

The three additions versus your GitHub Actions workflow:

- `--hidden-import=pytesseract` — without it, ticking the OCR box in the
  packaged app fails even when Tesseract is installed.
- `--hidden-import=PIL._tkinter_finder` — needed by `ImageTk`, which the PDF
  preview and the icon loader both use.
- `docs;docs` already covers `docs\logo_small.png`, so the new icon is
  bundled automatically.

Confirm the build:

```powershell
dir dist\RAM.exe
```

---

## 4. Test the executable before packaging

```powershell
.\dist\RAM.exe
```

Check:

1. The window opens with the RAM logo in the title bar.
2. The Library Scanner tab shows **"Enable OCR for image-only pages"**.
3. The label beside it reads `Tesseract 5.5.0 detected.`
4. Help / FAQ opens and shows the OCR sections.

**Point 3 is the one that matters.** If it says Tesseract was not found while
it works in PowerShell, the `--hidden-import=pytesseract` flag did not take
effect — rebuild.

---

## 5. Compile the installer

Open `installer.iss` in Inno Setup and press **Build → Compile**, or:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

Output:

```text
Output\ResearchArchiveMatcher_Setup_1.2.0.exe
```

Install it on a clean machine if you can, ideally one **without** Tesseract,
to confirm RAM still runs normally with the OCR option disabled. That is the
experience most of your users will have.

---

## 6. Also update the GitHub Actions workflow

`.github/workflows/build.yml` has the same gap. Line 43 installs:

```text
pymupdf openpyxl pandas pypdf python-docx rapidfuzz pillow pyinstaller
```

`pytesseract` is missing, so **every automated release build lacks OCR
support.** Add it:

```yaml
pip install pymupdf openpyxl pandas pypdf python-docx rapidfuzz pillow pytesseract pyinstaller
```

And add the hidden imports to all three PyInstaller lines (Windows, macOS,
Linux):

```text
--hidden-import=pytesseract --hidden-import=PIL._tkinter_finder
```

Without this, tagging `v1.2.0` would publish three platform builds where the
OCR checkbox never works.

---

## 7. Version numbering

I used **1.2.0** on the basis that:

- `v1.0.x` was the original release series.
- `v1.1.0` was branding and cleanup.
- Page search, OCR and the icon fix are substantial new features, so a minor
  bump rather than a patch.

Change the two `1.2.0` references if you prefer a different number — one in
`installer.iss` line 5, one in `installer_info.txt` line 11.

---

## 8. Suggested order

1. Delete the two PNGs.
2. Copy in the updated `installer.iss` and `installer_info.txt`.
3. Merge `feature/ocr-support` into `main` — the release should come from
   `main`.
4. Fix `.github/workflows/build.yml`.
5. Commit and push.
6. Build and test locally with the command in section 3.
7. Compile the installer, test the setup file.
8. Tag `v1.2.0` to trigger the automated multi-platform release.

Steps 1 to 5 are quick. Take your time over 6 and 7 — a packaged build
behaves differently from running from source, so the checks in section 4
matter.
