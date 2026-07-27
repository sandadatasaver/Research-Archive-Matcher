"""Shared window-icon handling for Research Archive Matcher.

Windows uses ``logo.ico``. Linux and macOS use a Tk ``iconphoto`` image.

The master artwork ``docs/logo_final.png`` is 2461x2449 pixels. Passing an
image that large to ``iconphoto`` sends roughly 24 MB in a single X11
request, which exceeds the maximum request length of some X servers and
raises a fatal ``BadLength`` error that cannot be caught in Python.

This module therefore always feeds ``iconphoto`` a small image:

1. ``docs/logo_small.png`` is used when present.
2. Otherwise the master logo is downscaled in memory with Pillow.
3. If neither route works the icon is skipped, because a missing icon must
   never stop the application from starting.
"""

from __future__ import annotations

import os
import sys
import tkinter as tk


# Icons above roughly 512x512 give no visual benefit and risk oversized
# X11 requests, so the shared icon is capped here.
MAX_ICON_SIZE = 256


def get_resource_path(relative_path: str) -> str:
    """Resolve assets in both source and PyInstaller layouts."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    path = os.path.join(base_path, relative_path)
    if not os.path.exists(path):
        path = os.path.join(os.path.abspath("."), relative_path)

    return path


def _photo_image_from_small_file():
    """Return a PhotoImage from the pre-scaled logo when it is safe to use."""
    small_path = get_resource_path("docs/logo_small.png")
    if not os.path.exists(small_path):
        return None

    try:
        image = tk.PhotoImage(file=small_path)
    except Exception:
        return None

    # Guard against the small logo being replaced by a large file later.
    if max(image.width(), image.height()) > MAX_ICON_SIZE * 2:
        return None

    return image


def _photo_image_from_master_logo():
    """Downscale the master logo in memory as a fallback."""
    master_path = get_resource_path("docs/logo_final.png")
    if not os.path.exists(master_path):
        return None

    try:
        import io

        from PIL import Image, ImageTk

        with Image.open(master_path) as source:
            image = source.copy()

        image.thumbnail((MAX_ICON_SIZE, MAX_ICON_SIZE), Image.LANCZOS)

        try:
            return ImageTk.PhotoImage(image)
        except Exception:
            # ImageTk needs a live Tk instance; fall back to raw PNG bytes.
            buffer = io.BytesIO()
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            image.save(buffer, format="PNG")
            return tk.PhotoImage(data=buffer.getvalue())
    except Exception:
        return None


def load_icon_photo():
    """Return a small PhotoImage for iconphoto, or None when unavailable."""
    return _photo_image_from_small_file() or _photo_image_from_master_logo()


def apply_window_icon(window):
    """Apply the RAM logo to any Tk window.

    The PhotoImage is stored on the window because Tk keeps only a weak
    reference to image data; without this the icon would be garbage
    collected and disappear.
    """
    ico_path = get_resource_path("logo.ico")

    if sys.platform == "win32" and os.path.exists(ico_path):
        try:
            window.iconbitmap(ico_path)
            return True
        except Exception:
            pass

    photo = load_icon_photo()
    if photo is None:
        return False

    try:
        window.iconphoto(False, photo)
    except Exception:
        return False

    window._ram_icon_photo = photo
    return True
