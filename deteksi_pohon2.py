import pandas as pd
from ultralytics import YOLO
import os
import rasterio
from rasterio.transform import Affine
import pyproj
import cv2
import numpy as np

# Tentukan path absolut untuk konsistensi
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Path untuk DUA model ---
# Model untuk mendeteksi lokasi pohon
TREE_MODEL_PATH = os.path.join(BASE_DIR, 'models', 'best_tree_detector.pt') 
# Model untuk mendeteksi kondisi/penyakit pohon
HEALTH_MODEL_PATH = os.path.join(BASE_DIR, 'models', 'best_health_analyzer.pt') 

OUTPUT_PATH = os.path.join(BASE_DIR, 'data_output', 'hasil_analisis_pohon.csv')

def detect_trees_and_health(input_image_path: str):
    """
    Mendeteksi koordinat pohon, lalu menganalisis kesehatan setiap pohon
    menggunakan dua model terpisah, dan menyimpan hasil gabungan ke CSV.
    """
    print(f"Memulai proses deteksi dan analisis pada: {input_image_path}")

    try:
        # 1. Muat kedua model
        print("Memuat model...")
        if not os.path.exists(TREE_MODEL_PATH) or not os.path.exists(HEALTH_MODEL_PATH):
            raise FileNotFoundError(f"Satu atau kedua model tidak ditemukan. Pastikan 'best_tree_detector.pt' dan 'best_health_analyzer.pt' ada di folder 'models'.")
        
        tree_model = YOLO(TREE_MODEL_PATH)
        health_model = YOLO(HEALTH_MODEL_PATH)
        print("Semua model berhasil dimuat.")

        # 2. Baca orthophoto.tif dan informasi geospasialnya
        print("Membaca file GeoTIFF...")
        with rasterio.open(input_image_path) as src:
            image_rgb = src.read([1, 2, 3])
            transform: Affine = src.transform
            source_crs = src.crs
            if not source_crs:
                raise ValueError("File GeoTIFF tidak memiliki informasi CRS.")

        # Konversi gambar untuk diproses
        image_hwc = image_rgb.transpose((1, 2, 0))
        image_bgr = cv2.cvtColor(image_hwc, cv2.COLOR_RGB2BGR)

        # --- TAHAP 1: Deteksi Lokasi Pohon ---
        print("TAHAP 1: Mendeteksi lokasi semua pohon...")
        tree_results = tree_model.predict(source=image_bgr, save=False, conf=0.5)[0]
        print(f"Deteksi lokasi selesai. Ditemukan {len(tree_results.boxes)} pohon.")

        # Siapkan konverter koordinat
        target_crs = "EPSG:4326"
        transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)
        
        detection_data = []
        print("TAHAP 2: Menganalisis kesehatan untuk setiap pohon...")
        # Iterasi melalui setiap pohon yang terdeteksi
        for i, box in enumerate(tree_results.boxes):
            # Ambil koordinat bounding box pohon
            x1, y1, x2, y2 = [int(coord) for coord in box.xyxy[0]]
            
            # --- TAHAP 2: Analisis Kesehatan per Pohon ---
            # Crop gambar pohon individu dari gambar besar
            cropped_tree_image = image_bgr[y1:y2, x1:x2]

            # Lakukan inference dengan model KESEHATAN pada pohon yang di-crop
            health_results = health_model.predict(source=cropped_tree_image, verbose=False)[0]

            # Tentukan status berdasarkan hasil prediksi (CONTOH LOGIKA)
            # GANTI BAGIAN INI SESUAI DENGAN OUTPUT MODEL KESEHATAN ANDA
            status_kesehatan = "Sehat" # Default status
            if len(health_results.boxes) > 0:
                # Jika model kesehatan mendeteksi sesuatu (misal: penyakit)
                # Ambil nama kelas dari deteksi dengan confidence tertinggi
                top_detection_cls = int(health_results.boxes.cls[0])
                status_kesehatan = health_model.names[top_detection_cls] # Contoh: 'Daun Kuning', 'Ganoderma'
            # -----------------------------------------------------------

            # Konversi koordinat piksel tengah ke WGS84
            xc_pixel = (x1 + x2) / 2
            yc_pixel = (y1 + y2) / 2
            proj_lon, proj_lat = transform * (xc_pixel, yc_pixel)
            lon_wgs84, lat_wgs84 = transformer.transform(proj_lon, proj_lat)

            # Tambahkan semua data ke list
            detection_data.append({
                'id_pohon': f"pohon_{i+1}",
                'longitude_wgs84': lon_wgs84,
                'latitude_wgs84': lat_wgs84,
                'status_kesehatan': status_kesehatan,
                'x_pixel': xc_pixel,
                'y_pixel': yc_pixel,
            })
            print(f"  Pohon_{i+1}: Status = {status_kesehatan}")

        if not detection_data:
            print("Proses selesai, namun tidak ada pohon yang terdeteksi.")
            return True, "Tidak ada pohon yang terdeteksi."
        
        # Simpan hasil akhir ke file CSV
        df_hasil = pd.DataFrame(detection_data)
        df_hasil.to_csv(OUTPUT_PATH, index=False)
        
        print(f"\nProses selesai. Hasil analisis gabungan disimpan di: {OUTPUT_PATH}")
        return True, "Deteksi dan analisis kesehatan berhasil."

    except Exception as e:
        error_msg = f"Terjadi error kritis: {e}"
        print(error_msg)
        return False, error_msg