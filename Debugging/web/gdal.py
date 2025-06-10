import os
import subprocess
import shutil
import time

# --- PENGATURAN (SILAKAN UBAH BAGIAN INI) ---

# 1. Masukkan path lengkap ke file orthophoto TIF Anda
INPUT_ORTHO_PATH = r"D:/Semester 6/Protel/Debugging/web/odm_orthophoto.tif"

# 2. Tentukan di mana folder tiles akan disimpan
OUTPUT_TILES_DIR = r"D:/Semester 6/Protel/Debugging/web/map_tiles"

# 3. Tentukan rentang level zoom yang ingin dibuat (Contoh: level detail)
ZOOM_LEVELS = "18-22"

# ----------------------------------------------------

def create_map_tiles():
    """
    Menjalankan gdal2tiles.py untuk membuat map tiles dari file orthophoto.
    PENTING: Jalankan skrip ini dari dalam OSGeo4W Shell.
    """
    print("--- Proses Pembuatan Map Tiles Dimulai ---")

    # Validasi path input
    if not os.path.exists(INPUT_ORTHO_PATH):
        print(f"❌ ERROR: File input tidak ditemukan di: {INPUT_ORTHO_PATH}")
        return

    # Hapus folder output lama jika ada, untuk memastikan hasil yang bersih
    if os.path.exists(OUTPUT_TILES_DIR):
        print(f"📁 Menghapus folder output lama: {OUTPUT_TILES_DIR}")
        shutil.rmtree(OUTPUT_TILES_DIR)
        
    print(f"📁 Membuat folder output baru di: {OUTPUT_TILES_DIR}")
    os.makedirs(OUTPUT_TILES_DIR, exist_ok=True)

    # Siapkan perintah gdal2tiles.py
    # --tiledriver=WEBP akan membuat tiles dalam format .webp yang lebih kecil & modern
    command = [
        'gdal2tiles.py',
        '--profile=raster',
        f'--zoom={ZOOM_LEVELS}',
        '--tiledriver=WEBP',
        '--webviewer=leaflet', # Membuat file preview leaflet.html
        INPUT_ORTHO_PATH,
        OUTPUT_TILES_DIR
    ]
    
    print("\n▶️  Menjalankan perintah gdal2tiles...")
    # Mencetak perintah lengkap untuk debugging
    print(f"   Perintah: {' '.join(command)}")

    start_time = time.time()
    try:
        # Jalankan perintah
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
