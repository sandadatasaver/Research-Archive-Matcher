"""Tkinter PDF page preview with highlighted search terms."""

from __future__ import annotations

import os
import re
import sys
import tkinter as tk
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageTk
from tkinter import ttk


def get_resource_path(relative_path: str) -> str:
    """Resolve assets in source and PyInstaller layouts."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    return os.path.join(base_path, relative_path)


class PDFPreviewWindow:
    """Render one PDF page and highlight the active query."""

    def __init__(
        self,
        parent,
        file_path: str,
        page_number: int,
        query: str,
        exact_phrase: bool = False,
    ):
        self.file_path = file_path
        self.page_number = max(1, int(page_number))
        self.query = query
        self.exact_phrase = exact_phrase
        self.document = fitz.open(file_path)
        self.window = tk.Toplevel(parent)
        self.window.title(
            f"PDF Preview — Page {self.page_number} — "
            f"{Path(file_path).name}"
        )
        self._set_window_icon()
        self.window.geometry("1000x500")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self._build_ui()
        self._render_page()

    def _set_window_icon(self):
        """Apply the RAM logo to the preview window."""
        ico_path = get_resource_path("logo.ico")
        png_path = get_resource_path("docs/logo_final.png")

        if sys.platform == "win32" and os.path.exists(ico_path):
            try:
                self.window.iconbitmap(ico_path)
                return
            except Exception:
                pass

        if os.path.exists(png_path):
            try:
                self.preview_icon = tk.PhotoImage(file=png_path)
                self.window.iconphoto(False, self.preview_icon)
            except Exception:
                pass

    def _build_ui(self):
        toolbar = ttk.Frame(self.window, padding=8)
        toolbar.pack(fill="x")

        self.info = ttk.Label(toolbar)
        self.info.pack(side="left", fill="x", expand=True)

        ttk.Button(
            toolbar,
            text="Previous",
            command=self.previous_page,
        ).pack(side="left", padx=3)
        ttk.Button(
            toolbar,
            text="Next",
            command=self.next_page,
        ).pack(side="left", padx=3)
        ttk.Button(
            toolbar,
            text="Close",
            command=self.close,
        ).pack(side="left", padx=3)

        frame = ttk.Frame(self.window)
        frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(frame, background="#333333")
        vertical = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.canvas.yview,
        )
        horizontal = ttk.Scrollbar(
            frame,
            orient="horizontal",
            command=self.canvas.xview,
        )
        self.canvas.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _search_rectangles(self, page):
        terms = [self.query]

        if not self.exact_phrase:
            terms = re.findall(r"[\w'-]+", self.query)

        rectangles = []

        for term in terms:
            if not term.strip():
                continue
            rectangles.extend(page.search_for(term))

        return rectangles

    def _render_page(self):
        page_index = min(self.page_number - 1, len(self.document) - 1)
        page = self.document[page_index]
        scale = 1.6
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(scale, scale),
            alpha=False,
        )
        image = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples,
        )
        draw = ImageDraw.Draw(image, "RGBA")

        for rectangle in self._search_rectangles(page):
            draw.rectangle(
                [
                    rectangle.x0 * scale,
                    rectangle.y0 * scale,
                    rectangle.x1 * scale,
                    rectangle.y1 * scale,
                ],
                fill=(255, 220, 0, 110),
                outline=(190, 120, 0, 230),
                width=2,
            )

        self.photo = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.canvas.configure(scrollregion=(0, 0, image.width, image.height))
        self.info.configure(
            text=(
                f"{Path(self.file_path).name}  |  Page {self.page_number} "
                f"of {len(self.document)}  |  Search: {self.query}"
            )
        )

    def previous_page(self):
        if self.page_number > 1:
            self.page_number -= 1
            self._render_page()

    def next_page(self):
        if self.page_number < len(self.document):
            self.page_number += 1
            self._render_page()

    def close(self):
        self.document.close()
        self.window.destroy()
