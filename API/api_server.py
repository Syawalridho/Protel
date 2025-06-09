# api_server.py
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import os
import shutil
import glob
import requests
import traceback
import time
# import zipfile # Tidak lagi diperlukan karena tidak ada ZIP

# Impor fungsi logika dari folder src
from src.deteksi_tanah import analyze_soil_data
from src.deteksi_pohon import detect_trees_and_health 

# --- KONFIGURASI PENTING ---
# Alamat IP dan port server teman Anda
DESTINATION_URL = "http://192.168.1.11:9000/api/receiver/terima-hasil-lengkap"
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

# --- FUNGSI UNTUK KIRIM FILE TUNGGAL DI LATAR BELAKANG ---
def send_single_file_in_background(filepath: str, destination_url: str, api_key: str, form_field_name: str, media_type: str):
    """
    Tugas latar belakang untuk mengirim satu file ke server tujuan.
    """
    try:
        if not os.path.exists(filepath):
            print(f"[BG-Task-Single] Error: File '{os.path.basename(filepath)}' tidak ditemukan untuk pengiriman.")
            return

        print(f"[BG-Task-Single] Mempersiapkan pengiriman file '{os.path.basename(filepath)}' ke {destination_url}")
        with open(filepath, 'rb') as f:
            files_to_send = {form_field_name: (os.path.basename(filepath), f, media_type)}
            headers = {'x-api-key': api_key}
            response = requests.post(destination_url, headers=headers, files=files_to_send, timeout=300)
            response.raise_for_status()

        print(f"[BG-Task-Single] ✅ File '{os.path.basename(filepath)}' berhasil dikirim. Respons dari server tujuan: {response.json()}")

    except Exception:
        print(f"[BG-Task-Single] ❌ Gagal menjalankan tugas pengiriman file '{os.path.basename(filepath)}'.")
        print(traceback.format_exc())
    finally:
        # Untuk hasil analisis, biarkan tetap ada
        pass 

# --- ENDPOINTS API ---

@app.get("/", summary="Endpoint Cek Status", tags=["Status"])
def read_root():
    return {"status": "API berjalan dengan baik!"}

@app.post("/api/upload-soil", summary="Unggah & Proses Data Tanah", tags=["Analisis Tanah"])
async def upload_and_process_soil_data(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    input_filepath = os.path.join(INPUT_SOIL_DIR, "data_tanah_terbaru.csv")
    output_soil_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_tanah.csv') 
    try:
        with open(input_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
    
    success, message = analyze_soil_data(input_filepath)
    if not success:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis data: {message}")
    
    print(f"[API] Analisis tanah berhasil. Menjadwalkan pengiriman '{os.path.basename(output_soil_path)}' di latar belakang...")
    # Mengirim hasil analisis tanah (CSV) sebagai file tunggal
    background_tasks.add_task(
        send_single_file_in_background,
        filepath=output_soil_path,
        destination_url=DESTINATION_URL,
        api_key=DESTINATION_API_KEY,
        form_field_name='soil_result_file', # Nama field yang diharapkan server teman untuk CSV tanah
        media_type='text/csv'
    )
    
    return JSONResponse(status_code=200, content={"message": "File tanah berhasil diunggah, analisis selesai, dan hasil akan dikirim ke server tujuan."})

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

# --- ENDPOINT PEMICU PENGIRIMAN HASIL ORTHOPHOTO DAN POHON ---
@app.post("/api/receive-orthophoto-from-watcher", summary="Terima Orthophoto dari Watcher", tags=["Internal"])
async def receive_orthophoto_from_watcher(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...) # Menerima file langsung
):
    # Simpan file yang diterima dari watcher
    ortho_filepath = os.path.join(INPUT_ORTHO_DIR, file.filename)
    try:
        with open(ortho_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    print(f"[API] Orthophoto '{file.filename}' diterima dari watcher.")
    
    # Kemudian, panggil logika deteksi pohon dengan file yang baru disimpan
    success, message = detect_trees_and_health(ortho_filepath)
    if not success:
        raise HTTPException(status_code=500, detail=f"Gagal mendeteksi pohon: {message}")

    # Jadwalkan pengiriman hasil (orthophoto asli dan CSV hasil deteksi pohon)
    tree_csv_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')

    print(f"[API] Menjadwalkan pengiriman orthophoto asli '{os.path.basename(ortho_filepath)}' di latar belakang...")
    background_tasks.add_task(
        send_single_file_in_background,
        filepath=ortho_filepath,
        destination_url=DESTINATION_URL,
        api_key=DESTINATION_API_KEY,
        form_field_name='ortho_photo_file',
        media_type='image/tiff'
    )

    if os.path.exists(tree_csv_path):
        print(f"[API] Menjadwalkan pengiriman hasil deteksi pohon '{os.path.basename(tree_csv_path)}' di latar belakang...")
        background_tasks.add_task(
            send_single_file_in_background,
            filepath=tree_csv_path,
            destination_url=DESTINATION_URL,
            api_key=DESTINATION_API_KEY,
            form_field_name='tree_result_file',
            media_type='text/csv'
        )
    else:
        print(f"[API] Peringatan: File hasil_analisis_pohon.csv tidak ditemukan. Hanya orthophoto yang akan dikirim.")
    
    return JSONResponse(
        status_code=200, 
        content={"message": f"Orthophoto '{file.filename}' diterima, deteksi dimulai, dan hasil akan dikirim."}
    )