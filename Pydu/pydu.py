#!/usr/bin/env python3
#=====================================================
#============= Python Disk Usage v0.1 ================
#   Analyze storage devices for large files
#   Visually shows which files are using more space
#=====================================================

import os
import sys
import time
import math
import curses
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

###############################################################################
# Utilities
###############################################################################

def human(n: int) -> str:
    try:
        n = float(n)
    except Exception:
        return "?"
    for unit in ["B", "K", "M", "G", "T", "P"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}E"

def ancestors(path: str, stop_at: str) -> list[str]:
    """Return all ancestor directories from path up to and including stop_at."""
    acc = []
    p = path
    stop_at = os.path.abspath(stop_at)
    while True:
        acc.append(p)
        if p == stop_at or p == os.path.dirname(p):
            break
        p = os.path.dirname(p)
    return acc

###############################################################################
# Shared state between scanner and TUI
###############################################################################

class State:
    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        # Sizes are cumulative (bubble up to ancestors as files are sized)
        self.size = defaultdict(int)          # path -> cumulative bytes
        self.exists = set()                   # paths discovered (dirs and files)
        self.children = defaultdict(list)     # dir -> list of immediate children paths
        self.is_dir = {}                      # path -> bool
        self.lock = threading.RLock()

        # Progress
        self.total_files = 1
        self.seen_files = 0
        self.total_dirs  = 1
        self.seen_dirs   = 0
        self.start_time  = time.time()
        self.scanning    = True
        self.errors      = 0

###############################################################################
# Scanner (producer) — populates state while TUI runs
###############################################################################

def pre_count(root: str, st: State):
    """Quick pre-pass: count files/dirs and build children map skeleton."""
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        with st.lock:
            st.exists.add(dirpath)
            st.is_dir[dirpath] = True
            st.children.setdefault(dirpath, [])
            st.total_dirs += 1
        for d in dirnames:
            dp = os.path.join(dirpath, d)
            with st.lock:
                st.exists.add(dp)
                st.is_dir[dp] = True
                st.children[dirpath].append(dp)
        with st.lock:
            st.total_files += len(filenames)

def scan_live(root: str, st: State, max_workers: int | None = None):
    """Multithreaded file sizing with live bubbling to ancestors."""
    pre_count(root, st)

    def file_size(path: str) -> tuple[str, int]:
        try:
            return (path, os.path.getsize(path))
        except Exception:
            with st.lock:
                st.errors += 1
            return (path, 0)

    fut_to_path = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
            with st.lock:
                st.seen_dirs += 1
                st.exists.add(dirpath)
                st.is_dir[dirpath] = True
                st.children.setdefault(dirpath, [])
                for d in dirnames:
                    dp = os.path.join(dirpath, d)
                    if dp not in st.children[dirpath]:
                        st.children[dirpath].append(dp)

            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                with st.lock:
                    st.exists.add(fpath)
                    st.is_dir[fpath] = False
                    st.children[dirpath].append(fpath)
                fut = pool.submit(file_size, fpath)
                fut_to_path[fut] = fpath

        for fut in as_completed(fut_to_path):
            path, sz = fut.result()
            # Bubble size to this file's directory and all ancestors up to root
            with st.lock:
                st.seen_files += 1
                st.size[path] = sz
                for anc in ancestors(os.path.dirname(path), st.root):
                    st.size[anc] += sz
    with st.lock:
        st.scanning = False

###############################################################################
# TUI
###############################################################################

class Browser:
    def __init__(self, stdscr, st: State):
        self.scr = stdscr
        self.st  = st
        self.cwd = st.root
        self.pos = 0
        self.sort_mode = 0  # 0=size desc, 1=name asc, 2=type

#        self.spinner_chars = ['←','↖','↑','↗','→','↘','↓','↙']
#        self.spinner_chars = ['🌀','🌪','💫','✨','🌟','⚡','🔥','💥']
        self.spinner_chars = ['[    ]', '[=   ]', '[==  ]', '[=== ]', '[====]', '[ ===]', '[  ==]', '[   =]']


        self.spinner_idx = 0


    def _format_bar(self, frac: float, width: int) -> str:
        width = max(3, width)
        frac = max(0.0, min(1.0, frac))
        filled = int(frac * width + 0.5)
        return "@" * filled + "-" * (width - filled)

    def _sorted_children(self, path: str) -> list[str]:
        with self.st.lock:
            kids = list(self.st.children.get(path, []))
            # Hide entries that no longer exist (rare)
            kids = [k for k in kids if k in self.st.exists]
            # Provide stable size snapshot for sorting
            sizes = {k: self.st.size.get(k, self.st.size.get(path, 0) if self.st.is_dir.get(k, False) else 0)
                     for k in kids}
            is_dir = {k: self.st.is_dir.get(k, False) for k in kids}

        if self.sort_mode == 1:
            kids.sort(key=lambda p: (not is_dir[p], os.path.basename(p).lower()))
        elif self.sort_mode == 2:
            kids.sort(key=lambda p: (not is_dir[p], -sizes[p], os.path.basename(p).lower()))
        else:
            kids.sort(key=lambda p: (not is_dir[p], -sizes[p], os.path.basename(p).lower()))
        return kids

    def draw(self):
        scr = self.scr
        st  = self.st
        scr.erase()
        h, w = scr.getmaxyx()

        # Header
        with st.lock:
            total = st.size.get(self.cwd, 0)
            seen = st.seen_files + st.seen_dirs
            tot  = st.total_files + st.total_dirs
            pct  = 100.0 * min(1.0, seen / max(1, tot))
            elapsed = time.time() - st.start_time
            rate = seen / elapsed if elapsed > 0 else 0.0
            eta = (tot - seen) / rate if rate > 0 else float("inf")
            scanning = st.scanning
            errs = st.errors
            
        title = f" pydu-live  |  {self.cwd} "
        status_left = f"Total: {human(total)}"
        
        if scanning:
            # animated spinner
            spin = self.spinner_chars[self.spinner_idx % len(self.spinner_chars)]
            eta_txt = "???" if not math.isfinite(eta) else f"{int(eta)}s"
            status_right = f"Examining: {spin} || Scanning {pct:5.1f}% || ETA {eta_txt}  errs:{errs}"
            self.spinner_idx += 1
        else:
            status_right = f"Scan complete  errs:{errs}"

        hdr = (title + " " * (w - len(title)))[:w-1]
        scr.addstr(0, 0, hdr, curses.A_REVERSE)

        sub = (status_left + " " * (w - len(status_left) - len(status_right) - 1) + status_right)[:w-1]
        scr.addstr(1, 0, sub)

        # Column header
        scr.addstr(2, 5, "(↑/↓ select, → enter, ← up, s sort, f files on/off, q quit)")
        scr.addstr(4, 2, "  SIZE    PCT                 \tBAR                \tNAME   ")
        row = 5


        kids = self._sorted_children(self.cwd)

        # Optionally hide files? We’ll show both dirs and files; dirs first via sort key.
        with st.lock:
            parent_total = st.size.get(self.cwd, 0)

        bar_width = max(10, min(40, w // 4))
        max_rows = h - row - 1
        if kids:
            self.pos = max(0, min(self.pos, len(kids) - 1))
        top = 0
        # Simple viewport: keep cursor in view
        if self.pos >= max_rows:
            top = self.pos - max_rows + 1

        for idx in range(top, min(len(kids), top + max_rows)):
            p = kids[idx]
            with st.lock:
                p_is_dir = st.is_dir.get(p, False)
                sz = st.size.get(p, 0)
                pt = parent_total if parent_total > 0 else 1
            frac = sz / pt if pt else 0.0
            bar = self._format_bar(frac, bar_width)
            name = os.path.basename(p) or p
            suffix = "/" if p_is_dir else ""
            line = f"{human(sz):>8}  {frac*100:5.1f}%  [{bar}]  {name}{suffix}"
            if idx == self.pos:
                scr.addstr(row, 0, line[:w-1], curses.A_STANDOUT)
            else:
                scr.addstr(row, 0, line[:w-1])
            row += 1

        # Footer help
        
        footer = (
            " q quit | ↑/↓ move | →/Enter open | ← up | s sort | f toggle files "
        )
        scr.addstr(h-1, 0, footer.ljust(w-1), curses.A_DIM)
        #scr.addstr(h-1, 0, (" q to quit  |  s: sort  |  Enter/→: open  |  ←: up ").ljust(w-1), curses.A_DIM)
        scr.refresh()

    def run(self):
        curses.curs_set(0)
        self.scr.nodelay(True)  # non-blocking getch
        last_draw = 0
        while True:
            now = time.time()
            # Redraw at ~20 FPS or on input
            if now - last_draw > 0.05:
                self.draw()
                last_draw = now

            ch = self.scr.getch()
            if ch == -1:
                time.sleep(0.01)
                continue

            if ch in (ord('q'), 27):  # q or ESC
                break
            elif ch in (curses.KEY_UP, ord('k')):
                self.pos = max(0, self.pos - 1)
            elif ch in (curses.KEY_DOWN, ord('j')):
                self.pos = self.pos + 1
            elif ch in (curses.KEY_RIGHT, ord('\n')):
                kids = self._sorted_children(self.cwd)
                if not kids:
                    continue
                self.pos = max(0, min(self.pos, len(kids)-1))
                sel = kids[self.pos]
                with self.st.lock:
                    if self.st.is_dir.get(sel, False):
                        self.cwd = sel
                        self.pos = 0
            elif ch == curses.KEY_LEFT:
                parent = os.path.dirname(self.cwd)
                if parent and parent in self.st.exists:
                    self.cwd = parent
                    self.pos = 0
            elif ch in (ord('s'),):
                self.sort_mode = (self.sort_mode + 1) % 3

###############################################################################
# Entrypoint
###############################################################################

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "/"
    root = os.path.abspath(root)

    # Validate root
    if not os.path.exists(root):
        print(f"Path does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    st = State(root)

    # Start scanner thread
    t = threading.Thread(target=scan_live, args=(root, st, os.cpu_count()), daemon=True)
    t.start()

    # Launch TUI
    def _run(stdscr):
        Browser(stdscr, st).run()

    try:
        curses.wrapper(_run)
    except KeyboardInterrupt:
        pass
    finally:
        # Allow scanner to finish (optional)
        t.join(timeout=0.1)

if __name__ == "__main__":
    main()

