import os
import subprocess
import shutil
import time

# --- Konfigurasi ---
# Path ke file orthophoto TIF Anda
INPUT_ORTHO_PATH = r"D:/Semester 6/protel/debugging/Tiles/input/odm_orthophoto.tif" 

# Nama folder untuk menyimpan hasil tiles
OUTPUT_TILES_DIR = r"D:/Semester 6/Protel/debugging/Tiles/output/map_tiles"

# Level zoom yang ingin dibuat (Contoh: level detail)
ZOOM_LEVELS = "18-22"

def create_map_tiles():
    """
    Menjalankan gdal2tiles.py untuk membuat map tiles dari file orthophoto.
    PENTING: Jalankan skrip ini dari dalam OSGeo4W Shell.
    """
    print("--- Proses Pembuatan Map Tiles Dimulai ---")

    # 1. Validasi path input
    if not os.path.exists(INPUT_ORTHO_PATH):
        print(f"❌ ERROR: File input tidak ditemukan di: {INPUT_ORTHO_PATH}")
        return

    # 2. Hapus folder output lama jika ada, untuk memastikan hasil yang bersih
    if os.path.exists(OUTPUT_TILES_DIR):
        print(f"📁 Menghapus folder output lama: {OUTPUT_TILES_DIR}")
        shutil.rmtree(OUTPUT_TILES_DIR)
        
    print(f"📁 Membuat folder output baru di: {OUTPUT_TILES_DIR}")
    os.makedirs(OUTPUT_TILES_DIR)

    # 3. Siapkan perintah gdal2tiles
    command = [
        'gdal2tiles.py',
        '--profile=raster', # Profil untuk data non-geografis/lokal
        f'--zoom={ZOOM_LEVELS}',
        '--webviewer=leaflet', # Buat file preview leaflet
        INPUT_ORTHO_PATH,
        OUTPUT_TILES_DIR
    ]
    
    print("\n▶️  Menjalankan perintah gdal2tiles...")
    print(f"   Perintah: {' '.join(command)}")

    start_time = time.time()
    try:
        # 4. Jalankan perintah
        # shell=True direkomendasikan di Windows agar environment path dikenali
        subprocess.run(command, check=True, shell=True)
        end_time = time.time()
        
        print("\n✅--- Proses Selesai ---")
        print(f"   Waktu yang dibutuhkan: {end_time - start_time:.2f} detik.")
        print(f"   Map tiles berhasil dibuat di: {OUTPUT_TILES_DIR}")
        print(f"   Buka file 'leaflet.html' di dalam folder tersebut untuk melihat pratinjau.")

    except FileNotFoundError:
        print("\n❌ ERROR: Perintah 'gdal2tiles.py' tidak ditemukan.")
        print("   Pastikan Anda menjalankan skrip ini dari dalam OSGeo4W Shell.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: Terjadi kesalahan saat menjalankan gdal2tiles.py: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: Terjadi kesalahan tak terduga: {e}")

if __name__ == "__main__":
    create_map_tiles()
