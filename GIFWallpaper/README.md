# GIFWallpaper

Animated GIF Wallpaper Application for Linux. Set animated GIFs as your desktop wallpaper with a simple GUI.

## Features

* Set animated GIFs as your desktop wallpaper
* Supports multiple monitors
* Simple PyQt5 GUI to select GIFs
* Runs in the background using threading
* Compatible with i3wm and other lightweight window managers

## Requirements

* Python 3.10+
* PyQt5
* Pillow
* feh (for setting wallpapers on Linux)

Install dependencies:

```bash
pip install PyQt5 Pillow
sudo apt install feh  # Debian/Ubuntu
```

## Usage

```bash
python3 gifwall.py
```

1. Click `Select GIF` and choose your animated GIF.
2. The GIF will start playing as your wallpaper.

## Systemd Service (Optional)

Run GIFWallpaper as a background service:

1. Create `~/.config/systemd/user/gifwall.service`:

```ini
[Unit]
Description=GIF Wallpaper Service

[Service]
ExecStart=/usr/bin/python3 /home/user/GIFWallpaper/gifwall.py
Restart=always

[Install]
WantedBy=default.target
```

2. Enable and start the service:

```bash
systemctl --user daemon-reload
systemctl --user enable gifwall.service
systemctl --user start gifwall.service
```

## Limitations

* Only works on Linux systems
* Depends on `feh` for setting wallpapers
* May not work with some desktop environments or compositors
* I use it with i3wm

## License

This project is licensed under the [GNU General Public License v3 (GPL-3.0)](https://www.gnu.org/licenses/gpl-3.0.html).
