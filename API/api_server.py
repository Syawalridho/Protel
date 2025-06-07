# api_server.py
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import shutil

# Impor fungsi logika dari folder src
from src.deteksi_tanah import analyze_soil_data
from src.deteksi_pohon import detect_trees_and_health # Meskipun tidak dipanggil lgsg oleh API, baik untuk diimpor

# Tentukan path dasar proyek
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_SOIL_DIR = os.path.join(BASE_DIR, 'data_input', 'soil')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data_output')

# Pastikan semua direktori ada
os.makedirs(INPUT_SOIL_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="API Deteksi Perkebunan Sawit")

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
    
    # Simpan file yang diunggah
    try:
        with open(input_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan file: {e}")
    finally:
        file.file.close()
        
    # Panggil fungsi analisis
    success, message = analyze_soil_data(input_filepath)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis data: {message}")
        
    return JSONResponse(
        status_code=200,
        content={"message": "File berhasil diunggah dan analisis dimulai.", "input_path": input_filepath}
    )

@app.get("/api/soil-results", summary="Ambil Hasil Analisis Tanah", tags=["Analisis Tanah"])
def get_soil_analysis_results():
    """
    Menyediakan file CSV hasil analisis kondisi tanah.
    """
    result_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_tanah.csv')
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="File hasil analisis tanah tidak ditemukan. Harap unggah data terlebih dahulu.")
    
    return FileResponse(path=result_path, media_type='text/csv', filename='hasil_analisis_tanah.csv')

@app.get("/api/tree-results", summary="Ambil Hasil Deteksi Pohon", tags=["Deteksi Pohon"])
def get_tree_detection_results():
    """
    Menyediakan file CSV hasil deteksi koordinat dan kesehatan pohon.
    """
    result_path = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="File hasil deteksi pohon tidak ditemukan. Harap letakkan file orthophoto terlebih dahulu.")
        
    return FileResponse(path=result_path, media_type='text/csv', filename='hasil_analisis_pohon.csv')

# Perintah untuk menjalankan server: uvicorn api_server:app --reload