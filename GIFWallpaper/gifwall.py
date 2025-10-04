import sys
import threading
import time
import subprocess
from PIL import Image, ImageSequence
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout,
    QHBoxLayout, QComboBox, QSlider
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

DEBUG = True  # <-- set to True to enable debug logging

# ---------------------------
# Debug function
# ---------------------------
def log_debug(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

# ---------------------------
# Monitor detection helper
# ---------------------------
def detect_monitors():
    """Return list of monitor resolutions from xrandr"""
    result = subprocess.run(['xrandr', '--listmonitors'], stdout=subprocess.PIPE, text=True)
    monitors = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 4:
            monitors.append(parts[2])
    log_debug(f"Detected monitors: {monitors}")
    return monitors

# ---------------------------
# Convert PIL Image -> QPixmap
# ---------------------------
def pil2pixmap(im):
    if im.mode == "RGB":
        r, g, b = im.split()
        im = Image.merge("RGB", (b, g, r))
        data = im.tobytes("raw", "RGB")
        qimg = QImage(data, im.width, im.height, QImage.Format_RGB888)
    else:
        im = im.convert("RGBA")
        data = im.tobytes("raw", "RGBA")
        qimg = QImage(data, im.width, im.height, QImage.Format_RGBA8888)
    return QPixmap.fromImage(qimg)

# ---------------------------
# GIF Wallpaper Application
# ---------------------------
class GIFWallpaperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF Wallpaper Selector")
        self.setGeometry(100, 100, 400, 350)

        self.wallpaper_thread = None
        self.running = False
        self.frames = []
        self.gif_path = None
        self.monitors = detect_monitors()

        # Layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # GIF preview
        self.preview_label = QLabel("No GIF selected")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.preview_label)

        # Select button
        self.btn_select = QPushButton("Select GIF")
        self.btn_select.clicked.connect(self.select_gif)
        self.layout.addWidget(self.btn_select)

        # Monitor selection
        self.monitor_box = QComboBox()
        self.monitor_box.addItem("All monitors")
        self.monitor_box.addItems(self.monitors)
        self.layout.addWidget(self.monitor_box)

        self.speed_label = QLabel("Speed: 20 ms per frame")
        self.layout.addWidget(self.speed_label)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(5)     # fastest 5ms
        self.speed_slider.setMaximum(200)   # slowest 200ms
        self.speed_slider.setValue(50)      # default
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        self.layout.addWidget(self.speed_slider)

        # Store delay
        self.frame_delay = self.speed_slider.value() / 1000.0  # convert ms → seconds

        # Start/Stop buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Wallpaper")
        self.btn_start.clicked.connect(self.start_wallpaper_btn)
        btn_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Stop Wallpaper")
        self.btn_stop.clicked.connect(self.stop_wallpaper)
        btn_layout.addWidget(self.btn_stop)

        self.layout.addLayout(btn_layout)

        # service
        self.btn_service = QPushButton("Start Service")
        self.btn_service.setCheckable(True)
        self.btn_service.clicked.connect(self.toggle_service)
        btn_layout.addWidget(self.btn_service)

    # ---------------------------
    # Update speed label
    def update_speed_label(self):
        self.frame_delay = self.speed_slider.value() / 1000.0
        self.speed_label.setText(f"Speed: {self.speed_slider.value()} ms per frame")

    # ---------------------------
    # GIF Selection
    # ---------------------------
    def select_gif(self):
        gif_path, _ = QFileDialog.getOpenFileName(self, "Choose GIF", "", "GIF Files (*.gif)")
        if not gif_path:
            log_debug("No GIF selected")
            return

        log_debug(f"Selected GIF: {gif_path}")
        self.gif_path = gif_path
        self.frames = []

        try:
            img = Image.open(gif_path)  # do NOT convert yet
            i = 0
            while True:
                img.seek(i)
                frame = img.convert("RGBA").copy()  # convert here per-frame
                self.frames.append(frame)
                i += 1
        except EOFError:
            pass  # end of sequence

        log_debug(f"Loaded {len(self.frames)} frames")

        # Show preview using first frame
        pixmap = pil2pixmap(self.frames[0])
        self.preview_label.setPixmap(pixmap.scaled(300, 200, Qt.KeepAspectRatio))


    # ---------------------------
    # Start wallpaper from button
    # ---------------------------
    def start_wallpaper_btn(self):
        log_debug("Start wallpaper button clicked")
        if not self.frames:
            log_debug("No GIF loaded or frames missing")
            return

        self.stop_wallpaper()  # stop previous thread if running

        self.running = True
        self.wallpaper_thread = threading.Thread(target=self.animate_gif, args=(self.gif_path,), daemon=True)
        self.wallpaper_thread.start()
        log_debug("Wallpaper thread started")

    # ---------------------------
    # Stop wallpaper
    # ---------------------------
    def stop_wallpaper(self):
        if self.running:
            log_debug("Stopping wallpaper thread")
        self.running = False
        if self.wallpaper_thread:
            self.wallpaper_thread.join(timeout=1)
            log_debug("Wallpaper thread joined")
            self.wallpaper_thread = None

    # ---------------------------
    # Animate GIF
    # ---------------------------
    def animate_gif(self, gif_path):
        monitors = self.monitors if self.monitor_box.currentIndex() == 0 else [self.monitor_box.currentText()]
        while self.running:
            for i, frame in enumerate(self.frames):
                if not self.running:
                    break
                frame_path = "/tmp/frame.png"
                frame.save(frame_path)
                for mon in monitors:
                    subprocess.run(["feh", "--bg-scale", frame_path])
                
                # read current slider value for live speed adjustment
                delay = self.speed_slider.value() / 1000.0
                time.sleep(delay)
                print(f"[DEBUG] Frame {i+1}/{len(self.frames)} displayed, delay={delay}s")

    def toggle_service(self):
        if self.btn_service.isChecked():
            log_debug("Starting wallpaper service...")
            self.btn_service.setText("Stop Service")
            if not self.frames:
                log_debug("No GIF loaded; cannot start service")
                self.btn_service.setChecked(False)
                self.btn_service.setText("Start Service")
                return
            self.start_wallpaper_service()
        else:
            log_debug("Stopping wallpaper service...")
            self.btn_service.setText("Start Service")
            self.stop_wallpaper()

    def start_wallpaper_service(self):
        """Start wallpaper in service mode (background thread, daemon=True)."""
        if self.wallpaper_thread and self.running:
            self.stop_wallpaper()
        self.running = True
        self.wallpaper_thread = threading.Thread(target=self.animate_gif, args=(self.gif_path,), daemon=True)
        self.wallpaper_thread.start()
        log_debug("Wallpaper service thread started")

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GIFWallpaperApp()
    window.show()
    sys.exit(app.exec_())
