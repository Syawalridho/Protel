from super_gradients.training import models
from super_gradients.training.dataloaders.dataloaders import (
    yolo_detection_train_dataloader,
    yolo_detection_val_dataloader,
)
from super_gradients.training.models.detection_models.yolo_nas import YoloNASDetectionTrainer
from super_gradients.training.training_hyperparams import DEFAULT_YOLO_NAS_TRAIN_PARAMS

# Path ke dataset YAML SuperGradients (format YOLO) 
DATASET_YAML = "Palm Oil Detection and Counting.v5i.yolov8/data.yaml"  # Ubah sesuai path kamu

# Load model YOLO-NAS-L (bukan S atau M)
model = models.get(
    "yolo_nas_l",                # Versi L
    num_classes=1,               # Jumlah kelas objek (ubah sesuai dataset)
    pretrained_weights="coco"    # Atau None jika tidak mau pretrain
)

# Load data loader
train_data = yolo_detection_train_dataloader(
    dataset_params=DATASET_YAML,
    batch_size=8,
    num_workers=2
)

val_data = yolo_detection_val_dataloader(
    dataset_params=DATASET_YAML,
    batch_size=8,
    num_workers=2
)

# Trainer khusus YOLO-NAS
trainer = YoloNASDetectionTrainer(model=model)

# Mulai training
trainer.train(
    train_loader=train_data,
    valid_loader=val_data,
    train_params={
        **DEFAULT_YOLO_NAS_TRAIN_PARAMS,
        "max_epochs": 50,
        "initial_lr": 5e-4,
        "lr_mode": "cosine",
        "warmup_mode": "linear_epoch_step",
        "batch_accumulate": 2,
        "mixed_precision": True,
        "warmup_initial_lr": 1e-6,
        "lr_warmup_epochs": 3,
        "average_best_models": True,
        "save_checkpoints": True,
        "metric_to_watch": "mAP@0.50",
        "early_stop_patience": 10
    }
)
