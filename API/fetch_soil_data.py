import requests
import os

# --- GANTI BAGIAN INI DENGAN INFORMASI DARI WEB LAIN ---
API_ENDPOINT_URL = "https://website-sumber-data.com/api/v1/get-soil-csv"  # CONTOH URL
API_KEY = "abcde1234567890"  # CONTOH API KEY

# Tentukan di mana file akan disimpan
SAVE_DIR = "data_input/soil"
SAVE_PATH = os.path.join(SAVE_DIR, "data_tanah_dari_web.csv")
# ---------------------------------------------------------

def fetch_data_from_web():
    """
    Mengambil data CSV dari endpoint API eksternal dan menyimpannya secara lokal.
    """
    print(f"Mencoba mengambil data dari: {API_ENDPOINT_URL}")

    # Siapkan header untuk autentikasi (sesuaikan jika metodenya berbeda)
    headers = {
        "x-api-key": API_KEY  # Contoh header, mungkin namanya 'Authorization' atau lainnya
    }

    try:
        # Lakukan permintaan GET ke endpoint
        response = requests.get(API_ENDPOINT_URL, headers=headers, timeout=30)

        # Cek apakah permintaan berhasil (status code 200 OK)
        response.raise_for_status()  # Ini akan error jika status 4xx atau 5xx

        # Pastikan direktori penyimpanan ada
        os.makedirs(SAVE_DIR, exist_ok=True)

        # Simpan konten respons (yaitu data CSV) ke dalam file
        with open(SAVE_PATH, 'w', encoding='utf-8') as f:
            f.write(response.text)

        print(f"✅ Data berhasil diambil dan disimpan di: {SAVE_PATH}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Gagal mengambil data: {e}")

if __name__ == "__main__":
    fetch_data_from_web()