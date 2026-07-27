"""Tests for cross-platform window icon handling.

The master logo is far too large to pass to Tk's iconphoto on X11. These
tests lock in the small-icon behaviour so the regression cannot return.
"""

import os
import sys
import unittest

from PIL import Image

from src.ui.app_icon import (
    MAX_ICON_SIZE,
    get_resource_path,
    load_icon_photo,
    apply_window_icon,
)

try:
    import tkinter as tk

    _probe = tk.Tk()
    _probe.destroy()
    DISPLAY_AVAILABLE = True
except Exception:
    DISPLAY_AVAILABLE = False


class TestSmallLogoAsset(unittest.TestCase):
    """These checks need no display."""

    def test_small_logo_is_shipped(self):
        path = get_resource_path("docs/logo_small.png")
        self.assertTrue(
            os.path.exists(path),
            "docs/logo_small.png must be committed for Linux and macOS icons",
        )

    def test_small_logo_is_within_the_size_cap(self):
        path = get_resource_path("docs/logo_small.png")
        with Image.open(path) as image:
            width, height = image.size

        self.assertLessEqual(max(width, height), MAX_ICON_SIZE)

    def test_small_logo_is_a_fraction_of_the_master_size(self):
        small = get_resource_path("docs/logo_small.png")
        master = get_resource_path("docs/logo_final.png")

        if not os.path.exists(master):
            self.skipTest("Master logo is not present")

        self.assertLess(os.path.getsize(small), os.path.getsize(master) / 5)

    def test_master_logo_would_have_been_unsafe(self):
        # Documents precisely why the small logo exists.
        master = get_resource_path("docs/logo_final.png")
        if not os.path.exists(master):
            self.skipTest("Master logo is not present")

        with Image.open(master) as image:
            width, height = image.size

        self.assertGreater(max(width, height), MAX_ICON_SIZE)


@unittest.skipUnless(DISPLAY_AVAILABLE, "No display available for Tk tests")
class TestIconApplication(unittest.TestCase):
    def setUp(self):
        import tkinter as tk

        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_load_icon_photo_returns_a_small_image(self):
        photo = load_icon_photo()

        self.assertIsNotNone(photo)
        self.assertLessEqual(
            max(photo.width(), photo.height()),
            MAX_ICON_SIZE * 2,
        )

    def test_apply_window_icon_succeeds_on_the_main_window(self):
        self.assertTrue(apply_window_icon(self.root))

    def test_apply_window_icon_succeeds_on_a_child_window(self):
        import tkinter as tk

        child = tk.Toplevel(self.root)
        try:
            self.assertTrue(apply_window_icon(child))
        finally:
            child.destroy()

    def test_icon_reference_is_retained_when_a_photo_is_used(self):
        """The PhotoImage must be kept alive on the window.

        Windows normally takes the native ``iconbitmap`` path, which creates
        no PhotoImage and therefore has nothing to retain. The retention rule
        only applies when the PNG path is used, so the ICO path is disabled
        here to exercise it on every platform.
        """
        import src.ui.app_icon as app_icon

        original = app_icon.get_resource_path

        def without_ico(relative_path):
            if relative_path == "logo.ico":
                return os.path.join("does-not-exist", "logo.ico")
            return original(relative_path)

        app_icon.get_resource_path = without_ico
        try:
            self.assertTrue(apply_window_icon(self.root))
            # Tk keeps only a weak reference; the app must hold a strong one.
            self.assertTrue(hasattr(self.root, "_ram_icon_photo"))
        finally:
            app_icon.get_resource_path = original

    def test_windows_uses_the_native_ico(self):
        """On Windows the ICO path is preferred and needs no PhotoImage."""
        if sys.platform != "win32":
            self.skipTest("Windows-only behaviour")

        ico_path = get_resource_path("logo.ico")
        if not os.path.exists(ico_path):
            self.skipTest("logo.ico is not present")

        self.assertTrue(apply_window_icon(self.root))
        # The native icon is set directly, so no PhotoImage is retained.
        self.assertFalse(hasattr(self.root, "_ram_icon_photo"))


if __name__ == "__main__":
    unittest.main()
