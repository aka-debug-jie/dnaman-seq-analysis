import ctypes
import time

from . import commands as C
from .win32 import (LB_GETCOUNT, LB_GETTEXT, LB_SETCURSEL, WM_CLOSE, WM_COMMAND,
                    child_by_id, child_by_text, class_of, click, enabled, text_of,
                    top_windows, type_text, u32, visible, wait_for)

_sa_done = set()


def is_file_dialog(h):
    return bool(
        h and class_of(h).startswith(C.FILE_DIALOG_CLASS)
        and child_by_id(h, C.DLG["file_name_edit"]) and visible(h)
    )


def find_file_dialog(pid, main_h=None):
    if main_h:
        popup = u32.GetLastActivePopup(main_h)
        if is_file_dialog(popup):
            return popup
    for h in top_windows(pid):
        if is_file_dialog(h):
            return h
    return None


def visible_dialogs(pid):
    out = []
    for h in top_windows(pid):
        if not class_of(h).startswith(C.DIALOG_CLASS):
            continue
        if child_by_id(h, C.DLG["file_name_edit"]):
            continue
        out.append(h)
    return out


def close_stray_dialogs(pid):
    for h in top_windows(pid):
        if is_file_dialog(h):
            u32.PostMessageW(h, WM_CLOSE, 0, 0)
    time.sleep(0.5)


def open_file_dialog(pid, main_h, cmd, path, timeout=25):
    """Send a load command, fill the file dialog, click Open."""
    u32.PostMessageW(main_h, WM_COMMAND, cmd, 0)
    dlg = wait_for(lambda: find_file_dialog(pid, main_h), timeout=timeout)
    if not dlg:
        raise RuntimeError("file dialog not found (cmd %s)" % cmd)
    type_text(child_by_id(dlg, C.DLG["file_name_edit"]), path)
    click(child_by_id(dlg, C.DLG["ok"]))
    if not wait_for(lambda: not visible(dlg), timeout=timeout):
        raise RuntimeError("file dialog did not close")
    return dlg


def handle_genbank_dialog(pid, timeout=25):
    """The GenBank import dialog: pick the first entry and press Load."""
    def _find():
        for h in top_windows(pid):
            if class_of(h).startswith(C.DIALOG_CLASS) and C.GENBANK_DIALOG_TITLE in text_of(h):
                return h
        return None

    dlg = wait_for(_find, timeout=timeout)
    if not dlg:
        raise RuntimeError("GenBank Sequence dialog not found")
    lst = child_by_id(dlg, C.DLG["genbank_list"])
    names = []
    if lst:
        n = u32.SendMessageW(lst, LB_GETCOUNT, 0, 0)
        for i in range(max(0, n)):
            buf = ctypes.create_unicode_buffer(256)
            u32.SendMessageW(lst, LB_GETTEXT, i, ctypes.cast(buf, ctypes.c_void_p).value)
            names.append(buf.value)
        if names:
            u32.SendMessageW(lst, LB_SETCURSEL, 0, 0)
            time.sleep(0.2)
    click(child_by_id(dlg, C.DLG["ok"]))
    wait_for(lambda: not visible(dlg), timeout=15)
    return names


def handle_sequence_type(pid, protein=False, timeout=20):
    """Answer DNAMAN's 'Is <name> a DNA sequence?' prompt."""
    def _find():
        for h in top_windows(pid):
            if class_of(h).startswith(C.DIALOG_CLASS) and text_of(h) == C.SEQUENCE_TYPE_TITLE:
                return h
        return None

    dlg = wait_for(_find, timeout=timeout)
    if not dlg:
        return False
    click(child_by_id(dlg, 7 if protein else 6))
    time.sleep(1.2)
    return True


def handle_wizard(pid, budget=15.0, log=None):
    """Click Select All once per dialog, then Next / Finish / OK until gone."""
    global _sa_done
    deadline = time.time() + budget
    while time.time() < deadline:
        dlgs = visible_dialogs(pid)
        _sa_done &= set(dlgs)
        if not dlgs:
            return True
        acted = False
        for d in dlgs:
            if d not in _sa_done:
                sa = child_by_text(d, "Select All")
                if sa and visible(sa) and enabled(sa):
                    _sa_done.add(d)
                    click(sa)
                    if log:
                        log("dialog: Select All")
                    acted = True
                    time.sleep(0.6)
                    break
            nxt = child_by_id(d, C.DLG["wizard_next"])
            if nxt and enabled(nxt):
                click(nxt)
                if log:
                    log("dialog: Next")
                acted = True
                time.sleep(0.8)
                break
            fin = child_by_id(d, C.DLG["wizard_finish"])
            if fin and enabled(fin):
                click(fin)
                if log:
                    log("dialog: Finish")
                acted = True
                time.sleep(0.8)
                break
            ok = child_by_id(d, C.DLG["ok"])
            if ok and enabled(ok):
                click(ok)
                if log:
                    log("dialog: OK")
                acted = True
                time.sleep(0.8)
                break
        if not acted:
            time.sleep(0.5)
    return False


def reset_wizard_state():
    global _sa_done
    _sa_done = set()
