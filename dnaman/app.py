import subprocess
import time

from . import config
from .win32 import class_of, text_of, wait_for

_app = None
_win = None


def kill():
    subprocess.run(
        ["taskkill", "/F", "/IM", "DNAMAN.EXE"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.0)
    global _app, _win
    _app = None
    _win = None


def launch(timeout=30):
    """Start DNAMAN and return (app, window-wrapper, main_handle, pid)."""
    global _app, _win
    from pywinauto import Application

    subprocess.Popen([config.EXE], cwd=config.DN_DIR)
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.5)
        h = _find_main()
        if h:
            try:
                app = Application(backend="win32").connect(handle=h, timeout=3)
                win = app.window(handle=h)
                if win.exists():
                    _app, _win = app, win
                    return app, win, h, _pid(h)
            except Exception:
                pass
    raise RuntimeError("DNAMAN did not start")


def _find_main():
    """Main frame = visible top-level Afx window of a DNAMAN.EXE process."""
    pids = _dnaman_pids()
    for h in _all_top():
        if _pid(h) in pids and class_of(h).startswith("Afx:") and text_of(h).startswith("DNAMAN"):
            return h
    for h in _all_top():
        if _pid(h) in pids and class_of(h).startswith("Afx:"):
            return h
    return None


def _dnaman_pids():
    out = set()
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq DNAMAN.EXE", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=20,
        )
        for line in r.stdout.splitlines():
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) > 1 and parts[0].upper().startswith("DNAMAN"):
                out.add(int(parts[1]))
    except Exception:
        pass
    return out


def _all_top():
    from .win32 import u32, EnumProc, visible

    found = []

    def _cb(h, _):
        if visible(h):
            found.append(h)
        return True

    u32.EnumWindows(EnumProc(_cb), 0)
    return found


def _pid(h):
    from .win32 import pid_of

    return pid_of(h)


def main_handle():
    h = _find_main()
    if not h:
        raise RuntimeError("DNAMAN main window not found")
    return h


def status_parts(main_h=None):
    """Read status bar parts via handle-based pywinauto (no title ambiguity)."""
    from pywinauto import Application

    h = main_h or main_handle()
    app = Application(backend="win32").connect(handle=h)
    sb = app.window(handle=h).child_window(class_name="msctls_statusbar32")
    return [t for t in sb.texts() if t]


def status_text(main_h=None):
    return " | ".join(status_parts(main_h))


def wait_status(contains, timeout=20, main_h=None):
    def _check():
        try:
            s = status_text(main_h)
        except Exception:
            return None
        return s if contains.upper() in s.upper() else None

    return wait_for(_check, timeout=timeout, interval=0.5)


def message_text(pid=None):
    """Return text of a DNAMAN message box, if any."""
    from .commands import MESSAGE_TITLE

    pids = {pid} if pid else _dnaman_pids()
    for h in _all_top():
        if _pid(h) in pids and class_of(h).startswith("#32770") and text_of(h) == MESSAGE_TITLE:
            from .win32 import child_windows

            return " / ".join(
                text_of(c) for c in child_windows(h) if class_of(c) == "Static" and text_of(c)
            )
    return None


def dismiss_message(pid=None):
    from .commands import MESSAGE_TITLE
    from .win32 import child_windows, click

    pids = {pid} if pid else _dnaman_pids()
    for h in _all_top():
        if _pid(h) in pids and class_of(h).startswith("#32770") and text_of(h) == MESSAGE_TITLE:
            for c in child_windows(h):
                if class_of(c) == "Button":
                    click(c)
                    time.sleep(0.8)
                    return True
    return False


def connected():
    """True when a DNAMAN main window is alive."""
    try:
        return bool(_find_main())
    except Exception:
        return False
