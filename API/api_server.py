import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import shutil
import glob
import requests
import traceback
import time

# Impor fungsi logika dari folder src
from src.deteksi_tanah import analyze_soil_data
# deteksi_pohon tidak perlu diimpor di sini karena dipicu oleh watcher

# --- KONFIGURASI PENTING ---
# Ganti dengan IP dan Port server teman Anda
DESTINATION_URL = "http://172.20.10.2:5000/api/receiver/terima-hasil-lengkap"
# API Key ini harus sama dengan yang ada di server teman Anda
# PERBAIKAN: Nama variabel disesuaikan agar konsisten
DESTINATION_API_KEY = "HALO"
# ----------------------------------------

# Tentukan path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_SOIL_DIR = os.path.join(BASE_DIR, 'data_input', 'soil')
INPUT_ORTHO_DIR = os.path.join(BASE_DIR, 'data_input', 'orthophoto')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data_output')

os.makedirs(INPUT_SOIL_DIR, exist_ok=True)
os.makedirs(INPUT_ORTHO_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="API Deteksi Perkebunan Sawit")

# --- FUNGSI UNTUK KIRIM 3 FILE DI LATAR BELAKANG ---
def send_full_bundle_task():
    """
    Tugas latar belakang untuk mencari semua 3 file hasil dan mengirimkannya.
    """
    try:
        # Beri jeda untuk memastikan file CSV dari proses deteksi selesai ditulis
        time.sleep(2)
        print("[BG-Task] Memulai tugas pengiriman bundle lengkap...")

        # Cari ketiga file yang diperlukan
        list_of_tifs = glob.glob(os.path.join(INPUT_ORTHO_DIR, '*.tif'))
        tree_csv_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')
        soil_csv_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_tanah.csv')
        
        # Validasi: Pastikan ketiga file ada sebelum melanjutkan
        if not list_of_tifs or not os.path.exists(tree_csv_path) or not os.path.exists(soil_csv_path):
            print("[BG-Task] Error: Satu atau lebih dari 3 file hasil tidak ditemukan. Pengiriman dibatalkan.")
            return

        latest_tif_file = max(list_of_tifs, key=os.path.getmtime)

        print(f"[BG-Task] Mempersiapkan pengiriman ke {DESTINATION_URL}:")  
        print(f"  - CSV Pohon: {os.path.basename(tree_csv_path)}")
        print(f"  - CSV Tanah: {os.path.basename(soil_csv_path)}")
        print(f"  - Mapping: {os.path.basename(latest_tif_file)}")
        
        # Kirim ketiga file dalam satu request
        with open(latest_tif_file, 'rb') as tif_f, \
             open(tree_csv_path, 'rb') as tree_csv_f, \
             open(soil_csv_path, 'rb') as soil_csv_f:
            
            # Kunci file (misal: 'mapping_file') harus sesuai dengan yang diharapkan server tujuan
            files_to_send = {
                'tree_csv_file': (os.path.basename(tree_csv_path), tree_csv_f, 'text/csv'),
                'soil_csv_file': (os.path.basename(soil_csv_path), soil_csv_f, 'text/csv'),
                'mapping_file': (os.path.basename(latest_tif_file), tif_f, 'image/tiff')
            }
            # PERBAIKAN: Menggunakan nama variabel yang konsisten
            headers = {'x-api-key': DESTINATION_API_KEY}
            # Timeout panjang untuk mengakomodasi pengiriman file besar
            response = requests.post(DESTINATION_URL, headers=headers, files=files_to_send, timeout=300)
            response.raise_for_status()

        print(f"[BG-Task] ✅ Bundle lengkap berhasil dikirim. Respons: {response.json()}")
    except Exception:
        print(f"[BG-Task] ❌ Gagal menjalankan tugas pengiriman.")
        print(traceback.format_exc())

# --- ENDPOINTS API ---

@app.post("/api/upload-soil", summary="Terima & Proses Data Tanah", tags=["Proses Utama"])
async def upload_and_process_soil_data(file: UploadFile = File(...)):
    """
    Endpoint ini HANYA menerima dan menganalisis data tanah.
    Tidak ada pengiriman otomatis dari sini.
    """
    input_filepath = os.path.join(INPUT_SOIL_DIR, "data_tanah_terbaru.csv")
    try:
        with open(input_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
        
    success, message = analyze_soil_data(input_filepath)
    if not success:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis data tanah: {message}")
    
    return JSONResponse(status_code=200, content={"message": "File tanah berhasil diunggah dan analisis selesai."})

@app.post("/api/send-full-results", summary="Kirim Semua Hasil Analisis", tags=["Proses Utama"])
def trigger_send_full_results(background_tasks: BackgroundTasks):
    """
    Endpoint ini HANYA untuk dipicu oleh watcher.
    Memicu pengiriman semua hasil (3 file) di latar belakang.
    """
    print("[API] Menerima pemicu dari watcher. Menjadwalkan pengiriman di latar belakang...")
    background_tasks.add_task(send_full_bundle_task)
    return JSONResponse(status_code=202, content={"message": "Perintah pengiriman diterima."})
