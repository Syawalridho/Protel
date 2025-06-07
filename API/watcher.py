# watcher.py
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Impor fungsi logika
from src.deteksi_pohon import detect_trees_and_health

# Tentukan path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCH_PATH = os.path.join(BASE_DIR, 'data_input', 'orthophoto')

class OrthophotoHandler(FileSystemEventHandler):
    """Handler untuk event pada folder orthophoto."""
    def on_created(self, event):
        # Dipicu ketika file atau folder baru dibuat
        if not event.is_directory:
            # Pastikan file adalah gambar
            if event.src_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
                print(f"✅ Gambar baru terdeteksi: {event.src_path}")
                print("🚀 Memulai proses deteksi pohon dan kesehatan...")
                # Panggil fungsi deteksi
                detect_trees_and_health(event.src_path)
            else:
                print(f"File non-gambar terdeteksi, diabaikan: {event.src_path}")

if __name__ == "__main__":
    # Pastikan folder yang dipantau ada
    os.makedirs(WATCH_PATH, exist_ok=True)
    
    event_handler = OrthophotoHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_PATH, recursive=False) # recursive=False agar tidak memantau subfolder
    
    print(f"👀 Memantau folder: {WATCH_PATH}")
    print("Letakkan file gambar (misal: map.tif) ke folder tersebut untuk memulai deteksi.")
    print("Tekan Ctrl+C untuk berhenti.")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Pemantau dihentikan.")
    observer.join()