import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import os
import shutil
import glob
import requests
import traceback
import time

# Impor fungsi logika dari folder src
from src.deteksi_tanah import analyze_soil_data
from src.deteksi_pohon import detect_trees_and_health 

# --- KONFIGURASI PENTING ---
# Alamat server teman Anda
DESTINATION_URL = "http://172.20.10.2:3001/api/receiver/terima-hasil-pohon"
# API Key yang ditentukan oleh server teman Anda
DESTINATION_API_KEY = "HALO"
# ----------------------------------------

# Tentukan path dasar proyek
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_SOIL_DIR = os.path.join(BASE_DIR, 'data_input', 'soil')
INPUT_ORTHO_DIR = os.path.join(BASE_DIR, 'data_input', 'orthophoto')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data_output')

os.makedirs(INPUT_SOIL_DIR, exist_ok=True)
os.makedirs(INPUT_ORTHO_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="API Deteksi Perkebunan Sawit")

# --- FUNGSI BARU UNTUK DIJALANKAN DI LATAR BELAKANG ---
def send_results_in_background():
    """
    Fungsi ini berisi logika pengiriman file yang berat dan akan dijalankan
    sebagai background task agar tidak menyebabkan timeout.
    """
    try:
        # Beri jeda singkat untuk memastikan file CSV selesai ditulis
        time.sleep(2)
        print("[BG-Task] Memulai tugas pengiriman bundle...")

        # 1. Cari semua file hasil yang diperlukan
        list_of_tifs = glob.glob(os.path.join(INPUT_ORTHO_DIR, '*.tif'))
        if not list_of_tifs:
            print("[BG-Task] Error: Tidak ada file mapping (.tif) ditemukan.")
            return

        latest_tif_file = max(list_of_tifs, key=os.path.getmtime)
        tree_csv_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')
        
        if not os.path.exists(tree_csv_path):
            print("[BG-Task] Error: File hasil_analisis_pohon.csv tidak ditemukan.")
            return

        print(f"[BG-Task] Mempersiapkan pengiriman ke {DESTINATION_URL}:")
        print(f" - Mapping: {os.path.basename(latest_tif_file)}")
        print(f" - CSV Pohon: {os.path.basename(tree_csv_path)}")

        # 2. Siapkan dan kirim file
        with open(latest_tif_file, 'rb') as tif_f, open(tree_csv_path, 'rb') as tree_csv_f:
            files_to_send = {
                'mapping_file': (os.path.basename(latest_tif_file), tif_f, 'image/tiff'),
                'csv_file': (os.path.basename(tree_csv_path), tree_csv_f, 'text/csv')
            }
            headers = {'x-api-key': DESTINATION_API_KEY}
            # Timeout panjang untuk proses pengiriman itu sendiri
            response = requests.post(DESTINATION_URL, headers=headers, files=files_to_send, timeout=300) 
            response.raise_for_status()

        print(f"[BG-Task] ✅ Bundle lengkap berhasil dikirim. Respons dari server tujuan: {response.json()}")

    except Exception:
        print(f"[BG-Task] ❌ Gagal menjalankan tugas pengiriman bundle.")
        # Mencetak detail error lengkap untuk debugging di log server
        print(traceback.format_exc())

# --- ENDPOINTS API ---

@app.get("/", summary="Endpoint Cek Status", tags=["Status"])
def read_root():
    return {"status": "API berjalan dengan baik!"}

@app.post("/api/upload-soil", summary="Unggah & Proses Data Tanah", tags=["Analisis Tanah"])
async def upload_and_process_soil_data(file: UploadFile = File(...)):
    input_filepath = os.path.join(INPUT_SOIL_DIR, "data_tanah_terbaru.csv")
    try:
        with open(input_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
    success, message = analyze_soil_data(input_filepath)
    if not success:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis data: {message}")
    return JSONResponse(status_code=200, content={"message": "File berhasil diunggah dan analisis dimulai."})

@app.get("/api/soil-results", summary="Ambil Hasil Analisis Tanah", tags=["Hasil Analisis"])
def get_soil_analysis_results():
    result_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_tanah.csv')
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="File hasil analisis tanah tidak ditemukan.")
    return FileResponse(path=result_path, media_type='text/csv', filename='hasil_analisis_tanah.csv')

@app.get("/api/tree-results", summary="Ambil Hasil Deteksi Pohon", tags=["Hasil Analisis"])
def get_tree_detection_results():
    result_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="File hasil deteksi pohon tidak ditemukan.")
    return FileResponse(path=result_path, media_type='text/csv', filename='hasil_analisis_pohon.csv')

# --- ENDPOINT DIPERBARUI UNTUK MENGGUNAKAN BACKGROUND TASK ---
@app.post("/api/send-tree-results", summary="Kirim Bundle Hasil Deteksi (Latar Belakang)", tags=["Kirim Hasil"])
def trigger_send_results_bundle(background_tasks: BackgroundTasks):
    """
    Memicu pengiriman bundle hasil di latar belakang. Endpoint ini merespons SEGERA.
    """
    print("[API] Menerima pemicu untuk pengiriman. Menjadwalkan tugas di latar belakang...")
    # Menambahkan fungsi pengiriman ke antrian background task
    background_tasks.add_task(send_results_in_background)
    
    # Langsung kembalikan respons ke watcher.py agar tidak timeout
    return JSONResponse(status_code=202, content={"message": "Tugas pengiriman telah diterima dan akan dijalankan di latar belakang."})
