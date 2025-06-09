import pandas as pd
from ultralytics import YOLO
import os
import rasterio
import pyproj
import cv2

# --- Tentukan path ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data_output')

# Path untuk DUA model
TREE_MODEL_PATH = os.path.join(MODELS_DIR, 'best_tree_detector.pt') # Model untuk deteksi lokasi pohon
GANODERMA_MODEL_PATH = os.path.join(MODELS_DIR, 'best_ganoderma_detector.pt') # Model untuk deteksi penyakit

CSV_OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'hasil_analisis_pohon.csv')

def detect_trees_and_health(input_image_path: str):
    """
    Mendeteksi lokasi pohon, lalu menganalisis gejala Ganoderma pada setiap pohon
    menggunakan dua model terpisah, dan menyimpan hasil gabungan ke CSV.
    """
    print(f"Memulai proses deteksi pohon & kesehatan pada: {os.path.basename(input_image_path)}")

    try:
        # 1. Muat kedua model
        print("Memuat model...")
        if not os.path.exists(TREE_MODEL_PATH) or not os.path.exists(GANODERMA_MODEL_PATH):
            raise FileNotFoundError(f"Satu atau kedua model tidak ditemukan. Pastikan keduanya ada di folder 'models'.")
        
        tree_model = YOLO(TREE_MODEL_PATH)
        health_model = YOLO(GANODERMA_MODEL_PATH)
        print("Semua model berhasil dimuat.")

        # 2. Baca orthophoto dan data geografisnya
        print("Membaca file GeoTIFF...")
        with rasterio.open(input_image_path) as src:
            image_rgb = src.read([1, 2, 3])
            transform = src.transform
            source_crs = src.crs
            if not source_crs: raise ValueError("File GeoTIFF tidak memiliki informasi CRS.")

        image_hwc = image_rgb.transpose((1, 2, 0))
        image_bgr = cv2.cvtColor(image_hwc, cv2.COLOR_RGB2BGR)

        # 3. TAHAP 1: Deteksi lokasi semua pohon
        print("TAHAP 1: Mendeteksi lokasi pohon...")
        tree_results = tree_model.predict(source=image_bgr, save=False, conf=0.5)[0]
        print(f"Deteksi lokasi selesai. Ditemukan {len(tree_results.boxes)} pohon.")

        # 4. Siapkan konverter koordinat ke WGS84
        transformer = pyproj.Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)
        
        detection_data = []
        print("\nTAHAP 2: Menganalisis gejala Ganoderma untuk setiap pohon...")
        # Iterasi melalui setiap pohon yang terdeteksi
        for i, box in enumerate(tree_results.boxes):
            x1, y1, x2, y2 = [int(coord) for coord in box.xyxy[0]]
            
            # Crop gambar pohon individu
            cropped_tree_image = image_bgr[y1:y2, x1:x2]

            # Lakukan inference dengan model KESEHATAN
            health_results = health_model.predict(source=cropped_tree_image, verbose=False)[0]

            # Tentukan status kesehatan: 0 jika terdeteksi, 1 jika tidak
            status_kesehatan = 1 # Default: Sehat
            if len(health_results.boxes) > 0:
                status_kesehatan = 0 # Terdeteksi gejala Ganoderma
            
            print(f"  - Pohon_{i+1}: Status = {'Sehat' if status_kesehatan == 1 else 'Sakit (Ganoderma)'}")

            # Konversi koordinat piksel tengah ke WGS84
            xc_pixel, yc_pixel = (x1 + x2) / 2, (y1 + y2) / 2
            proj_lon, proj_lat = transform * (xc_pixel, yc_pixel)
            lon_wgs84, lat_wgs84 = transformer.transform(proj_lon, proj_lat)

            detection_data.append({
                'id_pohon': f"pohon_{i+1}", 'gps_long': lon_wgs84,
                'gps_lat': lat_wgs84, 'status_kesehatan': status_kesehatan
            })

        pd.DataFrame(detection_data).to_csv(CSV_OUTPUT_PATH, index=False)
        print(f"\nProses selesai. Hasil deteksi pohon dan kesehatan disimpan di: {CSV_OUTPUT_PATH}")
        return True, "Deteksi pohon dan kesehatan berhasil."

    except Exception as e:
        error_msg = f"Terjadi error kritis saat deteksi pohon: {e}"
        print(error_msg)
        return False, error_msg
