import os
import cv2
import csv
import requests
import rasterio
from ultralytics import YOLO
from rasterio.transform import Affine

# Load model YOLO hanya sekali
model = YOLO("models/best.pt")

def detect_trees_georeferenced(image_path, output_csv_path="tree_results/hasil_deteksi.csv", post_url=None):
    # Buka GeoTIFF
    with rasterio.open(image_path) as src:
        image = src.read([1, 2, 3])  # RGB
        transform: Affine = src.transform

    # Convert ke BGR (untuk OpenCV/YOLOv8)
    image = image.transpose((1, 2, 0))
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Deteksi pohon menggunakan YOLO
    results = model.predict(source=image, save=False, conf=0.5)[0]

    # Buat folder hasil jika belum ada
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    # Simpan ke CSV
    with open(output_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Tree_ID", "X_pixel", "Y_pixel", "Longitude", "Latitude"])

        for i, box in enumerate(results.boxes.xyxy.tolist()):
            x1, y1, x2, y2 = box
            xc = (x1 + x2) / 2
            yc = (y1 + y2) / 2

            # Transformasi ke GPS
            lon, lat = transform * (xc, yc)

            writer.writerow([f"tree_{i+1}", xc, yc, lon, lat])

    print(f"[✔] Deteksi selesai, disimpan ke: {output_csv_path}")

    # Kirim ke Web jika ada URL
    if post_url:
        status, response = send_csv_to_web(output_csv_path, post_url)
        print(f"[🌐] Kirim ke web status {status}:\n{response}")

    return output_csv_path


def send_csv_to_web(csv_path, api_url):
    with open(csv_path, 'rb') as f:
        files = {'file': (os.path.basename(csv_path), f, 'text/csv')}
        try:
            response = requests.post(api_url, files=files)
            return response.status_code, response.text
        except Exception as e:
            return 500, f"[❌] Error saat mengirim: {e}"
