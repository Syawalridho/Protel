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
# PENTING: URL ini menunjuk ke API server LOKAL Anda dengan endpoint BARU.
API_ENDPOINT_URL = "http://localhost:000/api/send-full-results"

class OrthophotoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.tif', '.tiff')):
            print(f"✅ Gambar orthophoto baru terdeteksi: {os.path.basename(event.src_path)}")
            time.sleep(2)
            
            # TAHAP 1: JALANKAN DETEKSI
            print("🚀 Memulai proses deteksi pohon...")
            success, message = detect_trees_and_health(event.src_path)

            # TAHAP 2: KIRIM HASIL JIKA DETEKSI SUKSES
            if success:
                print("\n✅ Deteksi berhasil. Memicu API lokal untuk mengirim BUNDLE LENGKAP...")
                
                max_retries = 3 
                retry_delay = 20 
                
                for attempt in range(max_retries):
                    try:
                        response = requests.post(API_ENDPOINT_URL, timeout=30)
                        response.raise_for_status() 
                        
                        print(f"🚀 (Percobaan {attempt + 1}) Pemicuan API berhasil!")
                        print(f"   Respons dari API lokal: {response.json()}")
                        break
                    
                    except requests.exceptions.RequestException as e:
                        print(f"❌ (Percobaan {attempt + 1}/{max_retries}) GAGAL MEMICU API LOKAL.")
                        print(f"   Pastikan api_server.py sedang berjalan dan responsif. Detail: {e}")
                        if attempt < max_retries - 1:
                            print(f"   Akan mencoba lagi dalam {retry_delay} detik...")
                            time.sleep(retry_delay)
                        else:
                            print("   Sudah mencapai batas maksimal percobaan. Pengiriman gagal.")
            else:
                print(f"❌ Deteksi gagal. Pesan: {message}. Pengiriman dibatalkan.")

if __name__ == "__main__":
    os.makedirs(WATCH_PATH, exist_ok=True)
    event_handler = OrthophotoHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_PATH, recursive=False)
    print(f"👀 Memantau folder: {WATCH_PATH}")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Pemantau dihentikan.")
    observer.join()
