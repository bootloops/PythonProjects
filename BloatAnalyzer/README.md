# Bloat Analyzer (linux) 

Interactive Linux Bloatware Auditor

This Python script helps Linux users identify and optionally remove unnecessary packages (bloatware) from desktop environments (DEs) or window managers (WMs) they do not primarily use.

---

## Features

* Detects installed DEs/WMs including GNOME, KDE, XFCE, i3, LXDE
* Lists packages associated with non-primary DEs/WMs
* Interactive prompt to select packages to keep or remove
* Supports major package managers: `apt`, `dnf`, `pacman`
* Generates removal commands or simulates with `--dry-run`

---

## Requirements

* Python 3.x
* Linux system with `apt`, `dnf`, or `pacman` package manager
* Sudo privileges to remove packages

---

## Usage

Run the script with Python:

```bash
python3 analyze-bloat2.py
```

Optional dry-run mode (does not actually remove packages):

```bash
python3 analyze-bloat2.py --dry-run
```

### Example Flow

1. The script scans your system for installed DEs/WMs.
2. It prompts you to select your primary DE/WM.
3. Lists packages from other DEs/WMs that could be considered bloat.
4. Asks interactively for each package whether to keep or remove it.
5. Outputs the appropriate removal command based on your package manager.

---

## Supported Desktop Environments / Window Managers

* GNOME
* KDE
* XFCE
* i3
* LXDE

Packages from DEs not selected as primary are suggested for removal.

---

## Supported Package Managers

* `apt` (Debian/Ubuntu)
* `dnf` (Fedora/RHEL)
* `pacman` (Arch Linux)

---

## Limitations

* Only detects DE/WMs listed in `DE_PACKAGES`
* Assumes standard package names; custom or minimal installs may not be fully detected
* Interactive removal only generates the command; script does not execute removal unless user runs the generated command
* Requires read access to package database and sudo privileges for actual removal

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
