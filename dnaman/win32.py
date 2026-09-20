import ctypes
from ctypes import wintypes

u32 = ctypes.WinDLL("user32", use_last_error=True)

WPARAM = ctypes.c_size_t
LPARAM = ctypes.c_ssize_t

u32.GetDlgItem.restype = wintypes.HWND
u32.GetDlgItem.argtypes = [wintypes.HWND, ctypes.c_int]
u32.GetDlgCtrlID.restype = ctypes.c_int
u32.GetDlgCtrlID.argtypes = [wintypes.HWND]
u32.GetWindowThreadProcessId.restype = wintypes.DWORD
u32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
u32.IsWindowVisible.restype = wintypes.BOOL
u32.IsWindowVisible.argtypes = [wintypes.HWND]
u32.IsWindowEnabled.restype = wintypes.BOOL
u32.IsWindowEnabled.argtypes = [wintypes.HWND]
u32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
u32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
u32.SetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
u32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, WPARAM, LPARAM]
u32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, WPARAM, LPARAM]
u32.SendMessageW.restype = ctypes.c_ssize_t
u32.FindWindowExW.restype = wintypes.HWND
u32.FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
u32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
u32.PrintWindow.restype = wintypes.BOOL
u32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
u32.GetWindowDC.restype = wintypes.HDC
u32.GetWindowDC.argtypes = [wintypes.HWND]
u32.GetForegroundWindow.restype = wintypes.HWND

EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, LPARAM)
u32.EnumWindows.argtypes = [EnumProc, LPARAM]
u32.EnumChildWindows.argtypes = [wintypes.HWND, EnumProc, LPARAM]

WM_COMMAND = 0x0111
WM_CHAR = 0x0102
WM_SETTEXT = 0x000C
WM_CLOSE = 0x0010
WM_SYSCOMMAND = 0x0112
BM_CLICK = 0x00F5
BM_GETCHECK = 0x00F0
SC_MAXIMIZE = 0xF030

LB_GETCOUNT = 0x018B
LB_GETTEXT = 0x0189
LB_SETCURSEL = 0x0186


def text_of(h):
    buf = ctypes.create_unicode_buffer(512)
    u32.GetWindowTextW(h, buf, 512)
    return buf.value


def class_of(h):
    buf = ctypes.create_unicode_buffer(256)
    u32.GetClassNameW(h, buf, 256)
    return buf.value


def ctrl_id(h):
    return u32.GetDlgCtrlID(h)


def visible(h):
    return bool(u32.IsWindowVisible(h))


def enabled(h):
    return bool(u32.IsWindowEnabled(h))


def pid_of(h):
    p = wintypes.DWORD()
    u32.GetWindowThreadProcessId(h, ctypes.byref(p))
    return p.value


def top_windows(pid):
    found = []

    def _cb(h, _):
        if pid_of(h) == pid and visible(h):
            found.append(h)
        return True

    u32.EnumWindows(EnumProc(_cb), 0)
    return found


def child_windows(parent):
    found = []

    def _cb(h, _):
        found.append(h)
        return True

    u32.EnumChildWindows(parent, EnumProc(_cb), 0)
    return found


def child_by_id(parent, cid):
    h = u32.GetDlgItem(parent, cid)
    if h:
        return h
    for c in child_windows(parent):
        if ctrl_id(c) == cid:
            return c
    return None


def child_by_text(parent, needle):
    for c in child_windows(parent):
        if needle.lower() in text_of(c).lower():
            return c
    return None


def click(h):
    """Async click - safe for buttons that open modal dialogs."""
    u32.PostMessageW(h, BM_CLICK, 0, 0)


def send_cmd(main_h, cmd):
    u32.PostMessageW(main_h, WM_COMMAND, cmd, 0)


def type_text(h, text, delay=0.03):
    import time

    u32.SetWindowTextW(h, "")
    time.sleep(0.15)
    for ch in text:
        u32.PostMessageW(h, WM_CHAR, ord(ch), 1)
        time.sleep(delay)
    time.sleep(0.4)


def set_edit_value(h, text, delay=0.05):
    """Write a value into DNAMAN's custom (spin-style) edit fields.

    SetWindowText updates only the display, not DNAMAN's internal model; these
    fields must be written via EM_SETSEL + WM_CHAR (used by 347 region,
    348 mutation position/base and the 430 numeric fields)."""
    import time

    EM_SETSEL = 0x00B1
    u32.SendMessageW(h, EM_SETSEL, 0, -1)
    time.sleep(0.15)
    for ch in str(text):
        u32.PostMessageW(h, WM_CHAR, ord(ch), 1)
        time.sleep(delay)
    time.sleep(0.3)


def maximize(h):
    import time

    u32.SendMessageW(h, WM_SYSCOMMAND, SC_MAXIMIZE, 0)
    time.sleep(0.8)


def find_top(pid, title=None, cls=None, cid=None):
    for h in top_windows(pid):
        if title is not None and title not in text_of(h):
            continue
        if cls is not None and not class_of(h).startswith(cls):
            continue
        if cid is not None and not child_by_id(h, cid):
            continue
        return h
    return None


def wait_for(pred, timeout=20, interval=0.25):
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        value = pred()
        if value:
            return value
        time.sleep(interval)
    return None
