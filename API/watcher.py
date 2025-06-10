import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests

# Impor fungsi logika
from src.deteksi_pohon import detect_trees_and_health

# --- Konfigurasi ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCH_PATH = os.path.join(BASE_DIR, 'data_input', 'orthophoto')
# URL ini memanggil endpoint di server LOKAL Anda sendiri.
API_ENDPOINT_URL = "http://192.168.186.6:9000/api/send-full-results"

class OrthophotoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.tif', '.tiff')):
            print(f"✅ Gambar orthophoto baru terdeteksi: {os.path.basename(event.src_path)}")
            time.sleep(2)
            
            # 1. Jalankan deteksi pohon & kesehatan
            print("Memulai proses deteksi pohon & kesehatan...")
            success, message = detect_trees_and_health(event.src_path)

            # 2. Jika sukses, picu API untuk mengirim semua hasil
            if success:
                print("\n✅ Deteksi berhasil. Memicu API lokal untuk mengirim semua hasil...")
                
                try:
                    # Timeout bisa pendek karena API merespons segera
                    response = requests.post(API_ENDPOINT_URL, timeout=30)
                    response.raise_for_status() 
                    print(f"Pemicuan API berhasil! Respons: {response.json()}")
                except requests.exceptions.RequestException as e:
                    print(f"❌ GAGAL MEMICU API LOKAL. Pastikan api_server.py berjalan. Detail: {e}")
            else:
                print(f"❌ Deteksi pohon gagal. Pesan: {message}. Pengiriman dibatalkan.")

if __name__ == "__main__":
    os.makedirs(WATCH_PATH, exist_ok=True)
    event_handler = OrthophotoHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_PATH, recursive=False)
    print(f"Memantau folder: {WATCH_PATH}")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Pemantau dihentikan.")
    observer.join()
