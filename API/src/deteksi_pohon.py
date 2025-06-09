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

# --- Path hanya untuk SATU model ---
# Model untuk mendeteksi lokasi pohon
TREE_MODEL_PATH = os.path.join(BASE_DIR, 'models', 'best_tree_detector.pt') 

OUTPUT_PATH = os.path.join(BASE_DIR, 'data_output', 'hasil_analisis_pohon.csv')

def detect_trees_and_health(input_image_path: str):
    """
    Mendeteksi koordinat pohon menggunakan satu model, mengonversinya ke WGS84,
    dan menyimpan hasilnya ke CSV dengan status kesehatan placeholder.
    """
    print(f"Memulai proses deteksi pohon pada: {input_image_path}")

    try:
        # 1. Muat model deteksi pohon
        print("Memuat model deteksi pohon...")
        if not os.path.exists(TREE_MODEL_PATH):
            raise FileNotFoundError(f"Model deteksi pohon tidak ditemukan. Pastikan 'best_tree_detector.pt' ada di folder 'models'.")
        
        tree_model = YOLO(TREE_MODEL_PATH)
        print("Model berhasil dimuat.")

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

        # 3. Lakukan inference dengan model deteksi pohon
        print("Mendeteksi lokasi semua pohon...")
        tree_results = tree_model.predict(source=image_bgr, save=False, conf=0.5)[0]
        print(f"Deteksi lokasi selesai. Ditemukan {len(tree_results.boxes)} pohon.")

        # 4. Siapkan konverter koordinat
        target_crs = "EPSG:4326"
        transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)
        
        detection_data = []
        # Iterasi melalui setiap pohon yang terdeteksi
        for i, box in enumerate(tree_results.boxes):
            # Ambil koordinat bounding box pohon
            x1, y1, x2, y2 = [int(coord) for coord in box.xyxy[0]]
            
            # --- Status kesehatan diatur ke placeholder ---
            status_kesehatan = "Belum dianalisis"
            
            # Konversi koordinat piksel tengah ke WGS84
            xc_pixel = (x1 + x2) / 2
            yc_pixel = (y1 + y2) / 2
            proj_lon, proj_lat = transform * (xc_pixel, yc_pixel)
            lon_wgs84, lat_wgs84 = transformer.transform(proj_lon, proj_lat)

            # Tambahkan semua data ke list
            detection_data.append({
                'id_pohon': f"pohon_{i+1}",
                'gps_long': lon_wgs84,
                'gps_lat': lat_wgs84,
                'status_kesehatan': status_kesehatan,
            })

        if not detection_data:
            print("Proses selesai, namun tidak ada pohon yang terdeteksi.")
            return True, "Tidak ada pohon yang terdeteksi."
        
        # 5. Simpan hasil akhir ke file CSV
        df_hasil = pd.DataFrame(detection_data)
        df_hasil.to_csv(OUTPUT_PATH, index=False)
        
        print(f"\nProses selesai. Hasil deteksi disimpan di: {OUTPUT_PATH}")
        return True, "Deteksi pohon berhasil."

    except Exception as e:
        error_msg = f"Terjadi error kritis: {e}"
        print(error_msg)
        return False, error_msg

