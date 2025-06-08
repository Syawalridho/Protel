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
# Pastikan ini adalah Alamat IP LOKAL dari PC teman Anda yang menjalankan web server
DESTINATION_URL = "http://192.168.186.41:3001/api/receiver/terima-hasil-pohon"
# Pastikan API Key ini sama dengan yang ada di server teman Anda
DESTINATION_API_KEY = "HALO"
# ----------------------------------------

# Tentukan path dasar proyek
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_SOIL_DIR = os.path.join(BASE_DIR, 'data_input', 'soil')
INPUT_ORTHO_DIR = os.path.join(BASE_DIR, 'data_input', 'orthophoto')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data_output')

# Pastikan semua direktori ada
os.makedirs(INPUT_SOIL_DIR, exist_ok=True)
os.makedirs(INPUT_ORTHO_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="API Deteksi Perkebunan Sawit")

# --- FUNGSI PENGIRIMAN HASIL (Untuk Background Task) ---
def send_results_task():
    """
    Tugas latar belakang untuk mencari file terbaru dan mengirimkannya.
    """
    try:
        # Beri jeda singkat untuk memastikan file selesai ditulis oleh proses lain
        time.sleep(2)
        print("[BG-Task] Memulai tugas pengiriman bundle...")
        
        # 1. Cari file mapping .tif terbaru
        list_of_tifs = glob.glob(os.path.join(INPUT_ORTHO_DIR, '*.tif'))
        if not list_of_tifs:
            print("[BG-Task] Error: Tidak ada file mapping (.tif) ditemukan.")
            return # Hentikan tugas jika file tidak ada

        latest_tif_file = max(list_of_tifs, key=os.path.getmtime)
        tif_filename = os.path.basename(latest_tif_file)

        # 2. Cari file CSV hasil analisis pohon
        csv_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')
        if not os.path.exists(csv_path):
            print("[BG-Task] Error: File hasil_analisis_pohon.csv tidak ditemukan.")
            return # Hentikan tugas jika file tidak ada

        csv_filename = os.path.basename(csv_path)

        print(f"[BG-Task] Mempersiapkan pengiriman ke {DESTINATION_URL}:")
        print(f"  - Mapping: {tif_filename}")
        print(f"  - CSV: {csv_filename}")
        
        # 3. Kirim kedua file
        with open(latest_tif_file, 'rb') as tif_f, open(csv_path, 'rb') as csv_f:
            files_to_send = {
                'mapping_file': (tif_filename, tif_f, 'image/tiff'),
                'csv_file': (csv_filename, csv_f, 'text/csv')
            }
            headers = {'x-api-key': DESTINATION_API_KEY}
            response = requests.post(DESTINATION_URL, headers=headers, files=files_to_send, timeout=60)
            response.raise_for_status()

        print(f"[BG-Task] ✅ Bundle berhasil dikirim. Respons: {response.json()}")

    except Exception as e:
        print(f"[BG-Task] ❌ Gagal menjalankan tugas pengiriman bundle.")
        # Mencetak detail error lengkap untuk debugging
        print(traceback.format_exc())

# --- ENDPOINTS API ---

@app.get("/", summary="Endpoint Cek Status", tags=["Status"])
def read_root():
    return {"status": "API berjalan dengan baik!"}

@app.post("/api/start-full-analysis", summary="Unggah & Mulai Analisis Lengkap", tags=["Proses Utama"])
async def start_full_analysis_and_send(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    """
    Menerima file CSV data tanah, memicu SEMUA proses (analisis tanah, 
    deteksi pohon), lalu mengirimkan hasil bundle secara otomatis di latar belakang.
    """
    print("\n--- Menerima Permintaan Analisis Lengkap ---")
    input_filepath = os.path.join(INPUT_SOIL_DIR, "data_tanah_terbaru.csv")
    
    # Simpan file CSV yang diunggah
    try:
        with open(input_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
        
    # 1. Jalankan analisis tanah
    print("[1/3] Memulai analisis data tanah...")
    success_soil, message_soil = analyze_soil_data(input_filepath)
    if not success_soil:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis data tanah: {message_soil}")
    print("[1/3] Analisis data tanah berhasil.")
    
    # 2. Jalankan fungsi deteksi pohon
    print("\n[2/3] Memulai deteksi pohon...")
    success_tree = False
    try:
        list_of_tifs = glob.glob(os.path.join(INPUT_ORTHO_DIR, '*.tif'))
        if not list_of_tifs:
            print("[2/3] Peringatan: Tidak ada file orthophoto (.tif) untuk diproses.")
        else:
            latest_ortho_file = max(list_of_tifs, key=os.path.getmtime)
            # Ini adalah PANGGILAN FUNGSI YANG SUDAH DIPERBAIKI (hanya 1 argumen)
            success_tree, _ = detect_trees_and_health(latest_ortho_file)
            if success_tree:
                print("[2/3] Deteksi pohon selesai.")
            else:
                 print("[2/3] Fungsi deteksi pohon melaporkan kegagalan.")
    except Exception as e:
        print(f"[2/3] Peringatan: Terjadi error saat deteksi pohon: {e}")

    # 3. Jadwalkan pengiriman HANYA JIKA deteksi pohon berhasil
    if success_tree:
        print("\n[3/3] Menjadwalkan pengiriman bundle hasil di latar belakang...")
        background_tasks.add_task(send_results_task)
    else:
        print("\n[3/3] Pengiriman dibatalkan karena deteksi pohon tidak berhasil atau tidak ada file ortho.")
            
    # Kembalikan respons SEGERA ke client
    return JSONResponse(
        status_code=202, # 202 Accepted berarti permintaan diterima & sedang diproses
        content={"message": "Permintaan diterima. Proses analisis dan pengiriman telah dimulai di latar belakang. Cek log server untuk detail."}
    )

# ... (Endpoint untuk GET hasil tetap ada seperti sebelumnya) ...
@app.get("/api/soil-results", summary="Ambil Hasil Analisis Tanah", tags=["Hasil Analisis"])
def get_soil_analysis_results():
    result_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_tanah.csv')
    if not os.path.exists(result_path): raise HTTPException(status_code=404, detail="File hasil analisis tanah tidak ditemukan.")
    return FileResponse(path=result_path, media_type='text/csv', filename='hasil_analisis_tanah.csv')

@app.get("/api/tree-results", summary="Ambil Hasil Deteksi Pohon", tags=["Hasil Analisis"])
def get_tree_detection_results():
    result_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')
    if not os.path.exists(result_path): raise HTTPException(status_code=404, detail="File hasil deteksi pohon tidak ditemukan.")
    return FileResponse(path=result_path, media_type='text/csv', filename='hasil_analisis_pohon.csv')
