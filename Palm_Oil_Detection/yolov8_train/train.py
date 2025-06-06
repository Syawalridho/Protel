from ultralytics import YOLO
import torch

if __name__ == "__main__":
    # Deteksi perangkat (GPU atau CPU)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)
    if torch.cuda.is_available():
        print("GPU Name:", torch.cuda.get_device_name(0))

    # Aktifkan CUDNN optimization untuk percepatan training
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.enabled = True

    # Load model YOLOv8 (Pilih model optimal)
    model = YOLO("yolov8l.pt").to(device)  # Bisa ganti ke "yolov8s.pt" jika butuh lebih cepat

    # Training model dengan optimasi
    model.train(
        data="D:/Semester 6/Protel/Palm_Oil_Detection/DATASET/data.yaml",  # Path dataset
        epochs=150,  # Gunakan epochs lebih banyak, tetapi ada Early Stopping
        imgsz=640,  # Ukuran gambar lebih besar untuk detail lebih baik
        batch=12,  # Gunakan batch size optimal (sesuai VRAM)
        device=device,  # Gunakan GPU jika tersedia
        optimizer="AdamW",  # Gunakan AdamW yang lebih stabil dari SGD
        lr0=0.002,  # Learning rate awal sedikit lebih tinggi
        cos_lr=True,  # Gunakan Cosine Annealing LR Scheduler
        warmup_epochs=3,  # Tambahkan warmup selama 3 epoch pertama
        patience=15,  # Early stopping jika loss stagnan 15 epoch
        workers=8,  # Bisa coba 6, jika error coba turunkan ke 2
        project="runs",  # Folder penyimpanan hasil training
        name="Palm_Tree_Training",  # Nama eksperimen
        amp=True,  # Gunakan Mixed Precision untuk mempercepat training
        cache= "true",  # Cache di disk karena RAM tidak cukup
        verbose=True,  # Tampilkan info training lebih lengkap
        label_smoothing=0.1,  # Hindari model terlalu yakin (overfitting)
        dropout=0.1,  # Tambahkan dropout agar lebih robust
        #hsv_h=0.015,  # Augmentasi Hue
        #hsv_s=0.7,  # Augmentasi Saturasi
        #hsv_v=0.4,  # Augmentasi Kecerahan
        #mosaic=1.0,  # Gunakan Mosaic augmentation (bagus untuk dataset kecil)
        #mixup=0.2,  # Gunakan MixUp augmentation
        #degrees=10,  # Augmentasi Rotasi
        #scale=0.5,  # Augmentasi Scaling
        #shear=10,  # Augmentasi Shearing
        #perspective=0.001,  # Augmentasi Perspektif
        #translate=0.2,  # Augmentasi Translasi
    )
