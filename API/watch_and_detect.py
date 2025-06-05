import os
import time
import logging
from utils.detect_and_send import detect_trees_georeferenced

WATCH_FOLDER = "tree_input"
API_URL = "http://localhost:8000/upload-tree-detection"
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Setup logger
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "deteksi.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("deteksi")

log.info("👀 Memulai pemantauan folder: tree_input")

sudah_diproses = set()

while True:
    for file in os.listdir(WATCH_FOLDER):
        if file.endswith(".tif") and file not in sudah_diproses:
            full_path = os.path.join(WATCH_FOLDER, file)
            output_csv = os.path.join("tree_results", f"{os.path.splitext(file)[0]}_trees.csv")

            try:
                detect_trees_georeferenced(full_path, output_csv, API_URL)
                sudah_diproses.add(file)
            except Exception as e:
                log.error(f"[❌] Gagal deteksi {file}: {e}")
    time.sleep(5)
