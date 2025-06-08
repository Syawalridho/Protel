# api_server.py
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
# GANTI DENGAN URL DARI WEB TUJUAN ANDA
DESTINATION_URL = "http://192.168.186.41:8000/api/receiver/terima-hasil-pohon"
# GANTI DENGAN API KEY DARI WEB TUJUAN ANDA (JIKA DIBUTUHKAN)
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

# ... (Endpoint lain seperti @app.get("/") dan untuk soil tetap sama) ...

@app.get("/", summary="Endpoint Cek Status", tags=["Status"])
def read_root():
    """Endpoint untuk memeriksa apakah API berjalan."""
    return {"status": "API berjalan dengan baik!"}

@app.post("/api/upload-soil", summary="Unggah & Proses Data Tanah", tags=["Analisis Tanah"])
async def upload_and_process_soil_data(file: UploadFile = File(...)):
    """
    Menerima file CSV data tanah, menyimpannya, dan memicu analisis.
    """
    input_filepath = os.path.join(INPUT_SOIL_DIR, "data_tanah_terbaru.csv")
    
    try:
        with open(input_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan file: {e}")
    finally:
        file.file.close()
        
    success, message = analyze_soil_data(input_filepath)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis data: {message}")
        
    return JSONResponse(
        status_code=200,
        content={"message": "File berhasil diunggah dan analisis dimulai."}
    )

@app.get("/api/soil-results", summary="Ambil Hasil Analisis Tanah", tags=["Analisis Tanah"])
def get_soil_analysis_results():
    """
    Menyediakan file CSV hasil analisis kondisi tanah.
    """
    result_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_tanah.csv')
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="File hasil analisis tanah tidak ditemukan.")
    
    return FileResponse(path=result_path, media_type='text/csv', filename='hasil_analisis_tanah.csv')

@app.get("/api/tree-results", summary="Ambil Hasil Deteksi Pohon", tags=["Deteksi Pohon"])
def get_tree_detection_results():
    """
    Menyediakan file CSV hasil deteksi koordinat dan kesehatan pohon.
    """
    result_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="File hasil deteksi pohon tidak ditemukan.")
        
    return FileResponse(path=result_path, media_type='text/csv', filename='hasil_analisis_pohon.csv')


# --- ENDPOINT BARU UNTUK MENGIRIM BUNDLE HASIL POHON ---
@app.post("/api/send-tree-results", summary="Kirim Bundle Hasil Deteksi Pohon", tags=["Kirim Hasil"])
def send_tree_results_bundle():
    """
    Mencari file mapping .tif terbaru DAN file hasil_analisis_pohon.csv, 
    lalu mengirimkan keduanya ke endpoint web eksternal.
    """
    try:
        # 1. Cari file mapping .tif terbaru
        list_of_tifs = glob.glob(os.path.join(INPUT_ORTHO_DIR, '*.tif'))
        if not list_of_tifs:
            raise HTTPException(status_code=404, detail="Tidak ada file mapping (.tif) yang ditemukan.")
        latest_tif_file = max(list_of_tifs, key=os.path.getmtime)
        tif_filename = os.path.basename(latest_tif_file)

        # 2. Cari file CSV hasil analisis pohon
        csv_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="File hasil_analisis_pohon.csv tidak ditemukan.")
        csv_filename = os.path.basename(csv_path)

        print(f"Mempersiapkan untuk mengirim bundle:")
        print(f" - Mapping: {tif_filename}")
        print(f" - CSV: {csv_filename}")
        
        # 3. Siapkan kedua file untuk dikirim
        with open(latest_tif_file, 'rb') as tif_f, open(csv_path, 'rb') as csv_f:
            # Kunci 'mapping_file' dan 'csv_file' harus sesuai dengan yang diharapkan server tujuan
            files_to_send = {
                'mapping_file': (tif_filename, tif_f, 'image/tiff'),
                'csv_file': (csv_filename, csv_f, 'text/csv')
            }
            headers = {'x-api-key': DESTINATION_API_KEY}

            # Lakukan request POST untuk mengirim kedua file
            response = requests.post(DESTINATION_URL, headers=headers, files=files_to_send, timeout=60)
            response.raise_for_status()

        print(f"Bundle berhasil dikirim. Respons dari server tujuan: {response.json()}")
        return JSONResponse(
            status_code=200,
            content={
                "message": "Bundle hasil deteksi pohon berhasil dikirim.",
                "files_sent": [tif_filename, csv_filename],
                "destination_response": response.json()
            }
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Gagal menghubungi server tujuan: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi error tak terduga: {e}")
