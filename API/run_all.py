import subprocess
import time

print("[🚀] Menjalankan FastAPI server...")
fastapi = subprocess.Popen(["uvicorn", "main:app", "--reload"])

time.sleep(3)

print("[👀] Menjalankan watcher untuk folder tree_input/")
watcher = subprocess.Popen(["python", "watch_and_detect.py"])

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[🛑] Menghentikan semua proses...")
    fastapi.terminate()
    watcher.terminate()
