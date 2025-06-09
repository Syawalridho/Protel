import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import glob
import requests
import traceback
import time

# Impor fungsi logika dari folder src
from src.deteksi_tanah import analyze_soil_data
from src.deteksi_pohon import detect_trees_and_health 

# --- KONFIGURASI PENTING ---
DESTINATION_URL = "http://192.168.1.15:8000/api/receiver/terima-hasil-lengkap"
DESTINATION_API_KEY = "HALO"
# ----------------------------------------

# Tentukan path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_ORTHO_DIR = os.path.join(BASE_DIR, 'data_input', 'orthophoto')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data_output')

os.makedirs(os.path.join(BASE_DIR, 'data_input', 'soil'), exist_ok=True)
os.makedirs(INPUT_ORTHO_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="API Deteksi Perkebunan Sawit")

# --- FUNGSI UNTUK KIRIM 3 FILE DI LATAR BELAKANG ---
def send_full_bundle_task():
    try:
        time.sleep(2)
        print("[BG-Task] Memulai tugas pengiriman bundle lengkap...")

        # Cari ketiga file yang diperlukan
        list_of_tifs = glob.glob(os.path.join(INPUT_ORTHO_DIR, '*.tif'))
        tree_csv_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')
        soil_csv_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_tanah.csv')
        
        if not list_of_tifs or not os.path.exists(tree_csv_path) or not os.path.exists(soil_csv_path):
            print("[BG-Task] Error: Satu atau lebih file hasil tidak ditemukan. Pengiriman dibatalkan.")
            return

        latest_tif_file = max(list_of_tifs, key=os.path.getmtime)

        print(f"[BG-Task] Mempersiapkan pengiriman ke {DESTINATION_URL}:")
        print(f"  - Mapping: {os.path.basename(latest_tif_file)}")
        print(f"  - CSV Pohon: {os.path.basename(tree_csv_path)}")
        print(f"  - CSV Tanah: {os.path.basename(soil_csv_path)}")
        
        with open(latest_tif_file, 'rb') as tif_f, \
             open(tree_csv_path, 'rb') as tree_csv_f, \
             open(soil_csv_path, 'rb') as soil_csv_f:
            
            files_to_send = {
                'mapping_file': (os.path.basename(latest_tif_file), tif_f, 'image/tiff'),
                'tree_csv_file': (os.path.basename(tree_csv_path), tree_csv_f, 'text/csv'),
                'soil_csv_file': (os.path.basename(soil_csv_path), soil_csv_f, 'text/csv')
            }
            headers = {'x-api-key': DESTINATION_API_KEY}
            response = requests.post(DESTINATION_URL, headers=headers, files=files_to_send, timeout=300)
            response.raise_for_status()

        print(f"[BG-Task] ✅ Bundle lengkap berhasil dikirim. Respons: {response.json()}")
    except Exception:
        print(f"[BG-Task] ❌ Gagal menjalankan tugas pengiriman.")
        print(traceback.format_exc())

# --- ENDPOINTS API ---

@app.post("/api/send-full-results", summary="Kirim Semua Hasil Analisis", tags=["Proses Utama"])
def trigger_send_full_results(background_tasks: BackgroundTasks):
    """
    Endpoint ini HANYA untuk dipicu oleh watcher.
    Memicu pengiriman semua hasil (3 file) di latar belakang.
    """
    print("[API] Menerima pemicu dari watcher. Menjadwalkan pengiriman di latar belakang...")
    background_tasks.add_task(send_full_bundle_task)
    return JSONResponse(status_code=202, content={"message": "Perintah pengiriman diterima."})
