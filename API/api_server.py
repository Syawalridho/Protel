import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import shutil
import glob
import requests

# Impor fungsi logika dari folder src
from src.deteksi_tanah import analyze_soil_data
from src.deteksi_pohon import detect_trees_and_health 

# --- KONFIGURASI PENTING ---
# Ini adalah alamat server teman Anda yang akan menerima file.
DESTINATION_URL = "http://192.168.1.15:8000/api/receiver/terima-hasil-pohon"
# API Key ini harus sama dengan yang ditentukan oleh server teman Anda.
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

@app.post("/api/send-tree-results", summary="Kirim Bundle Hasil Deteksi Pohon", tags=["Kirim Hasil"])
def send_tree_results_bundle():
    try:
        list_of_tifs = glob.glob(os.path.join(INPUT_ORTHO_DIR, '*.tif'))
        if not list_of_tifs:
            raise HTTPException(status_code=404, detail="Tidak ada file mapping (.tif) yang ditemukan.")
        latest_tif_file = max(list_of_tifs, key=os.path.getmtime)
        
        csv_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="File hasil_analisis_pohon.csv tidak ditemukan.")
        
        print(f"Mempersiapkan untuk mengirim bundle ke {DESTINATION_URL}:")
        print(f" - Mapping: {os.path.basename(latest_tif_file)}")
        print(f" - CSV: {os.path.basename(csv_path)}")
        
        with open(latest_tif_file, 'rb') as tif_f, open(csv_path, 'rb') as csv_f:
            files_to_send = {
                'mapping_file': (os.path.basename(latest_tif_file), tif_f, 'image/tiff'),
                'csv_file': (os.path.basename(csv_path), csv_f, 'text/csv')
            }
            headers = {'x-api-key': DESTINATION_API_KEY}
            response = requests.post(DESTINATION_URL, headers=headers, files=files_to_send, timeout=60)
            response.raise_for_status()

        print(f"Bundle berhasil dikirim. Respons dari server tujuan: {response.json()}")
        return JSONResponse(status_code=200, content={"message": "Bundle hasil deteksi pohon berhasil dikirim.", "files_sent": [os.path.basename(latest_tif_file), os.path.basename(csv_path)], "destination_response": response.json()})
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Gagal menghubungi server tujuan: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi error tak terduga: {e}")
