# watcher.py
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
# import json # Tidak lagi perlu jika tidak mengirim JSON

# Impor fungsi logika
from src.deteksi_pohon import detect_trees_and_health # detect_trees_and_health tetap dipanggil di api_server sekarang

# --- Konfigurasi ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCH_PATH = os.path.join(BASE_DIR, 'data_input', 'orthophoto')
<<<<<<< HEAD
# PENTING: URL ini menunjuk ke API server LOKAL Anda sendiri untuk Menerima file orthophoto.
API_ENDPOINT_URL_RECEIVE_ORTHO = "http://192.168.1.11:9000/api/receive-orthophoto-from-watcher" # URL baru
=======
# PENTING: URL ini menunjuk ke API server LOKAL Anda dengan endpoint BARU.
API_ENDPOINT_URL = "http://localhost:000/api/send-full-results"
>>>>>>> 009f32d066f527191143c5d8a29ea3ff8310d6eb

class OrthophotoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.tif', '.tiff')):
            print(f"✅ Gambar orthophoto baru terdeteksi: {os.path.basename(event.src_path)}")
            time.sleep(2) # Beri sedikit waktu untuk memastikan file selesai ditulis sepenuhnya
            
<<<<<<< HEAD
            # TAHAP 1: KIRIM ORTHOPHOTO KE API SERVER UNTUK DETEKSI
            print("🚀 Mengirim orthophoto ke API server untuk diproses...")
            
            max_retries = 3 
            retry_delay = 20 
            
            for attempt in range(max_retries):
                try:
                    with open(event.src_path, 'rb') as f:
                        # Kirim file sebagai multipart/form-data
                        files_to_send = {'file': (os.path.basename(event.src_path), f, 'image/tiff')}
                        # Tidak perlu headers Content-Type karena requests akan menanganinya untuk multipart/form-data
                        response = requests.post(API_ENDPOINT_URL_RECEIVE_ORTHO, files=files_to_send, timeout=300) # Timeout lebih besar
=======
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
>>>>>>> 009f32d066f527191143c5d8a29ea3ff8310d6eb
                        response.raise_for_status() 
                        
                        print(f"🚀 (Percobaan {attempt + 1}) Pengiriman orthophoto ke API server berhasil!")
                        print(f"   Respons dari API lokal: {response.json()}")
                        break 
                    
                except requests.exceptions.RequestException as e:
                    print(f"❌ (Percobaan {attempt + 1}/{max_retries}) GAGAL MENGIRIM ORTHOPHOTO KE API LOKAL.")
                    print(f"   Pastikan api_server.py sedang berjalan dan responsif. Detail: {e}")
                    if attempt < max_retries - 1:
                        print(f"   Akan mencoba lagi dalam {retry_delay} detik...")
                        time.sleep(retry_delay)
                    else:
                        print("   Sudah mencapai batas maksimal percobaan. Pengiriman orthophoto gagal.")
            
            # Di alur ini, deteksi pohon dan pengiriman hasil DILAKUKAN OLEH API SERVER,
            # bukan oleh watcher lagi. Jadi, watcher hanya mengirim file dan menunggu konfirmasi.

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