#!/usr/bin/env python3
import subprocess
import shutil
import sys

# ---------------------------
# Configuration
# ---------------------------

# Map DE/WM to known package names
DE_PACKAGES = {
    "gnome": ["gnome-shell", "gnome-session", "gnome-terminal", "evince", "nautilus"],
    "kde": ["plasma-desktop", "kde-baseapps", "okular", "kdeconnect"],
    "xfce": ["xfce4-session", "xfce4-terminal", "thunar"],
    "i3": ["i3", "i3status", "i3lock"],
    "lxde": ["lxsession", "lxterminal", "pcmanfm"]
}

# Detect package manager
if shutil.which("apt"):
    PKG_MANAGER = "apt"
elif shutil.which("dnf"):
    PKG_MANAGER = "dnf"
elif shutil.which("pacman"):
    PKG_MANAGER = "pacman"
else:
    print("No supported package manager found (apt, dnf, pacman). Exiting.")
    sys.exit(1)

# ---------------------------
# Helper Functions
# ---------------------------
def check_installed(pkg):
    """Check if a package is installed"""
    try:
        if PKG_MANAGER == "apt":
            subprocess.run(["dpkg", "-s", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        elif PKG_MANAGER == "dnf":
            subprocess.run(["dnf", "list", "installed", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        elif PKG_MANAGER == "pacman":
            subprocess.run(["pacman", "-Qi", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def scan_installed_desktops():
    """Scan system for installed DEs/WMs"""
    detected = []
    print("Scanning installed DEs/WMs...")
    for de, pkgs in DE_PACKAGES.items():
        for pkg in pkgs:
            if check_installed(pkg):
                detected.append(de)
                break
    return detected

def interactive_remove(packages):
    """Ask user whether to keep or remove packages"""
    to_remove = []
    for pkg in packages:
        while True:
            choice = input(f"Keep or remove '{pkg}'? [k/r]: ").strip().lower()
            if choice in ("k", "r"):
                break
        if choice == "r":
            to_remove.append(pkg)
    return to_remove

def generate_removal_command(packages):
    """Generate command for removing packages"""
    if PKG_MANAGER == "apt":
        return f"sudo apt remove --purge {' '.join(packages)}"
    elif PKG_MANAGER == "dnf":
        return f"sudo dnf remove {' '.join(packages)}"
    elif PKG_MANAGER == "pacman":
        return f"sudo pacman -Rns {' '.join(packages)}"

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    detected_desktops = scan_installed_desktops()
    if not detected_desktops:
        print("No desktop environments or window managers detected.")
        sys.exit(0)

    print("Detected installed DEs/WMs:", ", ".join(detected_desktops))
    primary_de = input(f"Which DE/WM do you primarily use? [{'/'.join(detected_desktops)}]: ").strip().lower()
    if primary_de not in DE_PACKAGES:
        print("Invalid DE/WM choice. Exiting.")
        sys.exit(1)

    # Identify potential bloat
    potential_bloat = []
    for de, pkgs in DE_PACKAGES.items():
        if de != primary_de:
            for pkg in pkgs:
                if check_installed(pkg):
                    potential_bloat.append(pkg)

    if not potential_bloat:
        print("No potential bloatware detected.")
        sys.exit(0)

    print("\nPotential bloatware packages detected (outside your primary DE):")
    to_remove = interactive_remove(potential_bloat)

    if to_remove:
        cmd = generate_removal_command(to_remove)
        print("\nSuggested removal command (dry-run):")
        print(cmd)
    else:
        print("No packages selected for removal.")
