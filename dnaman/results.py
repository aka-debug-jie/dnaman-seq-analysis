import ctypes
import os
import time
from ctypes import wintypes

from . import commands as C
from .win32 import child_windows, class_of, text_of, u32

gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT,
                            wintypes.UINT, ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]


class _BMIH(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG), ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD),
    ]


def docs(win):
    """{hwnd: (class, title)} for the frame's child windows."""
    out = {}
    try:
        children = win.children()
    except Exception:
        return out
    for c in children:
        try:
            out[c.handle] = (c.class_name(), c.window_text())
        except Exception:
            pass
    return out


def all_docs(main_h):
    """ctypes-only variant (no pywinauto wrapper needed)."""
    out = {}
    for h in child_windows(main_h):
        cls = class_of(h)
        if cls.startswith("Afx:400000:b") or cls == C.RICHEDIT_CLASS:
            out[h] = (cls, text_of(h))
    return out


def rich_of(h):
    if class_of(h) == C.RICHEDIT_CLASS:
        return h
    return u32.FindWindowExW(h, 0, C.RICHEDIT_CLASS, None)


def read_text(h):
    from pywinauto.controls.hwndwrapper import HwndWrapper

    try:
        return HwndWrapper(h).window_text()
    except Exception:
        return None


def capture_png(hwnd, path):
    rect = wintypes.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    if w <= 0 or h <= 0:
        return False
    hdc = u32.GetWindowDC(hwnd)
    memdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(memdc, bmp)
    u32.PrintWindow(hwnd, memdc, 2)
    bmi = _BMIH()
    bmi.biSize = ctypes.sizeof(_BMIH)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(memdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    ok = False
    try:
        from PIL import Image

        Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB").save(path)
        ok = True
    except Exception:
        pass
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(memdc)
    return ok


def trim(path, margin=8):
    try:
        from PIL import Image, ImageChops

        im = Image.open(path).convert("RGB")
        for bg_color in ((0, 0, 0), (255, 255, 255)):
            box = ImageChops.difference(im, Image.new("RGB", im.size, bg_color)).getbbox()
            if box:
                im = im.crop(box)
        w, h = im.size
        im.crop((max(0, margin), max(0, margin), max(0, w - margin), max(0, h - margin))).save(path)
    except Exception:
        pass


def clipboard_get():
    import tkinter

    r = tkinter.Tk()
    r.withdraw()
    try:
        return r.clipboard_get()
    except Exception:
        return ""
    finally:
        r.destroy()


def clipboard_set(text):
    import tkinter

    r = tkinter.Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(text)
    r.update()
    r.destroy()


def copy_view_to_clipboard(main_h, doc_h, settle=2.0):
    """Select All + Copy from the active MDI document (assembly editor trick)."""
    mdi = u32.FindWindowExW(main_h, 0, C.MDI_CLIENT, None)
    if mdi:
        u32.SendMessageW(mdi, 0x0222, doc_h, 0)
    time.sleep(0.8)
    u32.PostMessageW(main_h, C.WM_COMMAND, C.CMD["select_all"], 0)
    time.sleep(0.6)
    u32.PostMessageW(main_h, C.WM_COMMAND, C.CMD["copy"], 0)
    time.sleep(settle)
    return clipboard_get()


def save_text(text, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text.replace("\u7648", "\u2103"))
    return path
