import subprocess
import time
import sys

# Perintah untuk menjalankan server FastAPI di port 8000
uvicorn_command = [
    sys.executable,
    "-m", "uvicorn", 
    "api_server:app", 
<<<<<<< HEAD
    "--host", "192.168.1.11", 
=======
    "--host", "0.0.0.0", 
>>>>>>> 009f32d066f527191143c5d8a29ea3ff8310d6eb
    "--port", "9000"
]

# Perintah untuk menjalankan watcher
watcher_command = [sys.executable, "watcher.py"]

api_process = None
watcher_process = None
try:
    print("=============================================")
    print("🚀 Menjalankan server FastAPI di http://0.0.0.0:9000")
    print("=============================================")
    api_process = subprocess.Popen(uvicorn_command)
    time.sleep(4) 

    print("\n=============================================")
    print("👀 Menjalankan watcher untuk folder 'data_input/orthophoto/'")
    print("=============================================")
    watcher_process = subprocess.Popen(watcher_command)

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n=============================================")
    print("🛑 Menangkap sinyal (Ctrl+C). Menghentikan semua proses...")
    if api_process: api_process.terminate()
    if watcher_process: watcher_process.terminate()
    if api_process: api_process.wait()
    if watcher_process: watcher_process.wait()
    print("✅ Semua proses telah dihentikan.")
    print("=============================================")
except Exception as e:
    print(f"\nTerjadi error tak terduga: {e}")
    if api_process: api_process.terminate()
    if watcher_process: watcher_process.terminate()
