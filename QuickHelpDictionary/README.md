# Quick Help Dictionary

### Discover what you already have and learn a quick bit about them

## Dictionary Generator (`dictionary_generator.py`)

**Generates a JSON dictionary of system commands using `whatis` (man database).**

This script scans your system for executable commands and fetches a one-line description for each using `whatis`. It outputs a structured, human-friendly JSON file named `auto_dictionary.json` containing entries for commands that have `whatis` descriptions.

---

## How It Works

1. Scans standard executable directories:

   ```
   /bin, /usr/bin, /usr/local/bin, /sbin, /usr/sbin
   ```

2. Runs `whatis <command>` for each discovered executable.

3. Parses the one-line description if available (e.g., `ls (1) - list directory contents`).

4. Builds JSON entries with fields:

   * `title` — command name
   * `description` — short description (text after the first `-`)
   * `example` — default usage suggestion (`<cmd> --help`)
   * `tags` — empty list for future categorization

5. Saves the result to `auto_dictionary.json` in the current working directory.

---

## Requirements

* Python 3.x
* `whatis` / `man-db` installed and updated on the system

> On Debian/Ubuntu, ensure the database is up-to-date:

```bash
sudo mandb
```

---

## Usage

Run the script in the directory where you want `auto_dictionary.json`:

```bash
python3 dictionary_generator.py
```

Example output:

```
Discovered 994 commands. Fetching descriptions...
✅ Generated 632 entries in auto_dictionary.json
```

---

## Output Format

Each JSON entry looks like:

```json
{
  "title": "ls",
  "description": "list directory contents",
  "example": "ls --help",
  "tags": []
}
```

* `title` — command name
* `description` — parsed from `whatis`
* `example` — default usage suggestion
* `tags` — currently empty; reserved for future tagging

---

## Notes & Limitations

* Depends on `whatis` entries. Commands without `whatis` entries are skipped.
* `whatis` output may vary; splitting on the first `-` may miss some commands.
* Requires read access to system bin directories (no root needed).
* Tags are currently unused; auto-categorization is planned for future versions.

---

## Troubleshooting

* If many commands are skipped, refresh the man database:

```bash
sudo mandb
# Install man-db if missing
sudo apt install man-db
```

* To debug a skipped command, run `whatis <command>` manually.

---

## Suggested Improvements

* Fallback to `man <cmd>` snippet when `whatis` is missing
* Auto-tagging based on description keywords (e.g., `filesystem`, `networking`)
* Alternative outputs: Markdown cheatsheet, SQLite DB, or searchable JSON
* Add CLI options: `--out` to specify output filename, `--dirs` to customize scanned directories

---

## License

### MIT License

```
MIT License

Copyright (c) 2025 Bootloops(CG)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

