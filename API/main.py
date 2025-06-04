from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from models.yolo_model import detect_trees
import shutil

app = FastAPI()

# Aktifkan CORS biar frontend bisa akses
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ganti dengan domain frontend kamu jika perlu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API aktif!"}

@app.post("/predict-tree")
async def predict_tree(image: UploadFile = File(...)):
    # Simpan file upload sementara
    temp_path = f"temp_{image.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # Lakukan prediksi
    detections = detect_trees(temp_path)

    return {"filename": image.filename, "detections": detections}
