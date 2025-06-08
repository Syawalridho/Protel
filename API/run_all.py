import subprocess
import time
import sys

# Perintah untuk menjalankan server FastAPI
# Menggunakan nama file baru: api_server:app
# Menambahkan --host dan --port agar konsisten
uvicorn_command = [
    sys.executable,  # Menggunakan interpreter python yang sedang berjalan
    "-m", "uvicorn", 
    "api_server:app", 
    "--host", "0.0.0.0", 
    "--port", "8000"
    # Dihilangkan --reload agar lebih stabil saat dijalankan via skrip,
    # tapi bisa ditambahkan jika masih dalam tahap development aktif
]

# Perintah untuk menjalankan watcher
# Menggunakan nama file baru: watcher.py
watcher_command = [sys.executable, "watcher.py"]

# --- Mulai Menjalankan Proses ---
try:
    print("=============================================")
    print("🚀 [1/2] Menjalankan server FastAPI di http://0.0.0.0:8000")
    print("=============================================")
    # Menjalankan server API di background
    api_process = subprocess.Popen(uvicorn_command)

    # Beri jeda beberapa detik agar server siap sepenuhnya
    time.sleep(4) 

    print("\n=============================================")
    print("👀 [2/2] Menjalankan watcher untuk folder 'data_input/orthophoto/'")
    print("=============================================")
    # Menjalankan watcher di background
    watcher_process = subprocess.Popen(watcher_command)

    # Biarkan skrip utama berjalan agar bisa menangkap Ctrl+C
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n=============================================")
    print("🛑 Menangkap sinyal (Ctrl+C). Menghentikan semua proses...")
    
    # Hentikan proses secara aman
    api_process.terminate()
    watcher_process.terminate()
    
    # Tunggu proses benar-benar berhenti
    api_process.wait()
    watcher_process.wait()
    
    print("✅ Semua proses telah dihentikan.")
    print("=============================================")

except Exception as e:
    print(f"\nTerjadi error: {e}")
    # Pastikan proses dihentikan jika terjadi error lain
    api_process.terminate()
    watcher_process.terminate()