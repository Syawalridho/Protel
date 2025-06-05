from ultralytics import YOLO
import rasterio
import cv2
from fastapi import UploadFile
from rasterio.transform import Affine
import numpy as np
import tempfile

# Load YOLO model sekali saja
model = YOLO("best.pt")

def detect_trees_from_geotiff(uploaded_file: UploadFile):
    # Simpan file sementara
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
        tmp.write(uploaded_file.file.read())
        tmp_path = tmp.name

    # Buka file geotiff
    with rasterio.open(tmp_path) as src:
        image = src.read([1, 2, 3])
        transform: Affine = src.transform

    # Preprocess image
    image = image.transpose((1, 2, 0))  # (H, W, 3)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Prediksi menggunakan YOLO
    results = model.predict(source=image, conf=0.5, save=False)[0]

    # Ambil koordinat
    detections = []
    for i, box in enumerate(results.boxes.xyxy.tolist()):
        x1, y1, x2, y2 = box
        xc = (x1 + x2) / 2
        yc = (y1 + y2) / 2
        lon, lat = transform * (xc, yc)

        detections.append({
            "Tree_ID": f"tree_{i+1}",
            "X_pixel": xc,
            "Y_pixel": yc,
            "Longitude": lon,
            "Latitude": lat
        })

    return detections
