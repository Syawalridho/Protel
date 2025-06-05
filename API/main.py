from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import os
import shutil
import pandas as pd

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-tree-detection")
async def upload_tree_detection(file: UploadFile = File(...)):
    # Simpan file CSV ke foldeSr uploads
    file_location = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Optional: Baca isinya pakai pandas
    try:
        df = pd.read_csv(file_location)
        return {
            "status": "success",
            "filename": file.filename,
            "rows_received": len(df),
            "columns": df.columns.tolist()
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Gagal membaca CSV: {str(e)}"})
