from ultralytics import YOLO
import cv2
import rasterio
from rasterio.transform import Affine
import csv

# Load model YOLO
model = YOLO("D:/Semester 6/Protel/Palm_Oil_Detection/yolov8_train/runs/Optimized_Training4/weights/best.pt")

# Baca orthophoto.tif dan transformasi GeoTIFF
with rasterio.open("D:/Semester 6/Protel/GPS/map_test/odm_orthophoto/odm_orthophoto.tif") as src:
    image = src.read([1, 2, 3])  # RGB
    transform: Affine = src.transform

# Convert (1, H, W) to (H, W, 3)
image = image.transpose((1, 2, 0))
image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

# Inference ke YOLO
results = model.predict(source=image, save=False, conf=0.5)[0]

# Simpan koordinat deteksi ke CSV
with open("tree_coordinates.csv", "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Tree_ID", "X_pixel", "Y_pixel", "Longitude", "Latitude"])

    for i, box in enumerate(results.boxes.xyxy.tolist()):
        x1, y1, x2, y2 = box
        xc = (x1 + x2) / 2
        yc = (y1 + y2) / 2

        # Konversi piksel ke koordinat dunia (lon, lat)
        lon, lat = transform * (xc, yc)

        writer.writerow([f"tree_{i+1}", xc, yc, lon, lat])
