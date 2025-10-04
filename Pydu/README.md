# PyDU - Python Disk Usage Analyzer

**PyDU** (pydu.py / pydu-live) is a terminal-based, interactive, and multithreaded disk usage analyzer written in Python. It provides a live, ncdu-inspired view of file and directory sizes, allowing users to explore storage usage in real-time.

---

## Features

* **Interactive Terminal Interface (TUI):** Navigate directories using keyboard controls.
* **Live Multithreaded Analysis:** Scans directories in parallel for faster performance.
* **Human-readable Sizes:** Displays sizes in B, K, M, G, T, P units.
* **Visual Bars:** Graphical bar representation of relative size.
* **Progress Indicators:** Shows scanning progress, ETA, and errors.
* **Sorting Options:** Sort entries by size, name, or type.
* **Responsive Controls:** Arrow keys, Vim-style keys (`j`/`k`), and shortcuts (`s`, `f`, `q`).

---

## Installation

Requires Python 3.8 or later.

```bash
git clone <repo_url>
cd <repo_directory>
python3 pydu.py [path]
```

No external dependencies are required beyond the Python standard library.

---

## Usage

```bash
python3 pydu.py /path/to/analyze
```

* If no path is provided, the root directory `/` is used by default.

### Controls

| Key           | Action                                 |
| ------------- | -------------------------------------- |
| `↑` / `k`     | Move selection up                      |
| `↓` / `j`     | Move selection down                    |
| `→` / `Enter` | Enter selected directory               |
| `←`           | Go up to parent directory              |
| `s`           | Cycle sorting modes (size, name, type) |
| `f`           | Toggle display of files                |
| `q` / `ESC`   | Quit the program                       |

---

## Notes

* Scanning is multithreaded for faster performance.
* Progress is displayed with spinner, percentage, ETA, and error count.
* TUI refreshes at ~20 FPS for smooth updates.
* Large directories may take longer to scan completely.
* Errors in reading files are counted and displayed.

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

---

## Example

```bash
$ python3 pydu.py /home/user
```

You will see a terminal-based interface showing directories, sizes, percentage usage, visual bars, and navigation options.
