from ultralytics import YOLO
import cv2
import os

# === SETTING ===
model_path = "D:/Semester 6/Protel/Palm_Oil_Detection/yolov8_train/runs/Optimized_Training4/weights/best.pt"           # Ganti ke lokasi model hasil training
image_path = "D:/Semester 6/Protel/GPS/DJI_20250503170534_0024_D.JPG"    # Ganti ke gambar yang ingin diuji
output_dir = "results/"                  # Folder untuk menyimpan hasil deteksi

# Buat folder output jika belum ada
os.makedirs(output_dir, exist_ok=True)

# === LOAD MODEL ===
model = YOLO(model_path)

# === PREDIKSI ===
results = model(image_path)

# === AMBIL HASIL DETEKSI DAN SIMPAN GAMBAR ===
for r in results:
    # Gambar asli
    img = r.plot()  # Otomatis menggambar bounding box
    filename = os.path.basename(image_path)
    output_path = os.path.join(output_dir, f"detected_{filename}")

    # Simpan hasil
    cv2.imwrite(output_path, img)
    print(f"Hasil deteksi disimpan di: {output_path}")
