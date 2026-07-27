"""Tests for the GUI OCR checkbox and OCR progress reporting.

These tests are skipped automatically when no display is available, so they
stay safe on headless build servers.
"""

import os
import unittest

try:
    import tkinter as tk

    _root = tk.Tk()
    _root.destroy()
    DISPLAY_AVAILABLE = True
except Exception:
    DISPLAY_AVAILABLE = False


@unittest.skipUnless(DISPLAY_AVAILABLE, "No display available for Tk tests")
class TestGUIOCROption(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep the test database out of the developer's real index.
        cls.db_path = "gui_ocr_test.db"

    def setUp(self):
        import tkinter as tk
        from src.ui.main_window import ResearchArchiveMatcherGUI

        self.root = tk.Tk()
        self.root.withdraw()
        self.app = ResearchArchiveMatcherGUI(self.root)

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

        for name in ("index.db", self.db_path):
            if os.path.exists(name):
                try:
                    os.remove(name)
                except OSError:
                    pass

    def test_ocr_checkbox_exists_and_defaults_to_off(self):
        self.assertFalse(self.app.ocr_enabled_var.get())

    def test_ocr_availability_is_reported(self):
        # The status label must always say something useful.
        self.assertTrue(self.app.ocr_status_var.get())

    def test_checkbox_is_disabled_when_tesseract_is_missing(self):
        if self.app.ocr_available:
            self.skipTest("Tesseract is installed on this machine")

        self.assertIn("disabled", self.app.ocr_checkbox.state())
        self.assertFalse(self.app.ocr_enabled_var.get())

    def test_ocr_progress_helpers_update_the_bar(self):
        self.app.update_ocr_progress(42.0, "OCR page 3/7")

        self.assertAlmostEqual(self.app.ocr_progress_var.get(), 42.0)
        self.assertEqual(self.app.ocr_progress_label_var.get(), "OCR page 3/7")

    def test_progress_callback_counts_ocr_pages(self):
        callback = self.app.build_ocr_progress_callback("paper.pdf", 1, 1)

        callback(
            {
                "page_number": 1,
                "page_total": 2,
                "characters": 0,
                "ocr_attempted": False,
                "ocr_used": False,
                "ocr_error": None,
            }
        )
        callback(
            {
                "page_number": 2,
                "page_total": 2,
                "characters": 120,
                "ocr_attempted": True,
                "ocr_used": True,
                "ocr_error": None,
            }
        )

        self.assertEqual(callback.state["ocr_pages"], 1)
        self.assertEqual(callback.state["failed_pages"], 0)

    def test_progress_callback_counts_failures(self):
        callback = self.app.build_ocr_progress_callback("paper.pdf", 1, 1)

        callback(
            {
                "page_number": 1,
                "page_total": 1,
                "characters": 0,
                "ocr_attempted": True,
                "ocr_used": False,
                "ocr_error": "tesseract crashed",
            }
        )

        self.assertEqual(callback.state["ocr_pages"], 0)
        self.assertEqual(callback.state["failed_pages"], 1)

    def test_ocr_progress_bar_can_be_shown_and_hidden(self):
        self.app.show_ocr_progress(True)
        self.root.update_idletasks()
        self.assertTrue(self.app.ocr_progress_frame.winfo_manager())

        self.app.show_ocr_progress(False)
        self.root.update_idletasks()
        self.assertFalse(self.app.ocr_progress_frame.winfo_manager())


if __name__ == "__main__":
    unittest.main()
