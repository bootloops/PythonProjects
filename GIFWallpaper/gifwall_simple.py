import sys
import threading
import time
import subprocess
from PIL import Image, ImageSequence
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog

import os
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog
from PIL import Image, ImageSequence
import threading, time

class GIFWallpaperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF Wallpaper")
        self.setGeometry(100, 100, 400, 150)
        self.wallpaper_thread = None
        self.running = False
        self.previous_wallpaper = None

        self.btn_select = QPushButton("Select GIF", self)
        self.btn_select.setGeometry(50, 20, 300, 40)
        self.btn_select.clicked.connect(self.select_gif)

        self.btn_stop = QPushButton("Stop Wallpaper", self)
        self.btn_stop.setGeometry(50, 80, 300, 40)
        self.btn_stop.clicked.connect(self.stop_wallpaper)

    def detect_monitors(self):
        result = subprocess.run(['xrandr', '--listmonitors'], stdout=subprocess.PIPE, text=True)
        monitors = []
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 4:
                monitors.append(parts[2])
        return monitors

    def get_current_wallpaper(self):
        # GNOME
        try:
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.background', 'picture-uri'],
                                    stdout=subprocess.PIPE, text=True)
            uri = result.stdout.strip().strip("'")
            if uri.startswith("file://"):
                return uri[7:]
            return uri
        except:
            return None

    def restore_wallpaper(self):
        if self.previous_wallpaper and os.path.exists(self.previous_wallpaper):
            monitors = self.detect_monitors()
            for _ in monitors:
                subprocess.run(["feh", "--bg-scale", self.previous_wallpaper])

    def select_gif(self):
        gif_path, _ = QFileDialog.getOpenFileName(self, "Choose GIF", "", "GIF Files (*.gif)")
        if gif_path:
            # Save current wallpaper
            self.previous_wallpaper = self.get_current_wallpaper()
            self.start_wallpaper(gif_path)

    def start_wallpaper(self, gif_path):
        if self.wallpaper_thread:
            self.running = False
            self.wallpaper_thread.join()

        self.running = True
        self.wallpaper_thread = threading.Thread(target=self.animate_gif, args=(gif_path,))
        self.wallpaper_thread.start()

    def stop_wallpaper(self):
        self.running = False
        if self.wallpaper_thread:
            self.wallpaper_thread.join()
            self.wallpaper_thread = None
        self.restore_wallpaper()

    def animate_gif(self, gif_path):
        img = Image.open(gif_path)
        frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
        monitors = self.detect_monitors()

        while self.running:
            for frame in frames:
                if not self.running:
                    break
                frame_path = "/tmp/frame.png"
                frame.save(frame_path)
                for mon in monitors:
                    subprocess.run(["feh", "--bg-scale", frame_path])
                time.sleep(0.05)


# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GIFWallpaperApp()
    window.show()
    sys.exit(app.exec_())