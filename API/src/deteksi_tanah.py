import pandas as pd
import joblib
import os

# Tentukan path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'random_forest_classifier.pkl')
OUTPUT_PATH = os.path.join(BASE_DIR, 'data_output', 'hasil_analisis_tanah.csv')

def analyze_soil_data(input_csv_path: str):
    """
    Menganalisis data tanah untuk mengklasifikasikan sebagai 'Sehat' atau 'Tidak Sehat'.
    """
    print(f"Mulai menganalisis file tanah: {input_csv_path}")
    
    try:
        print(f"Memuat model dari: {MODEL_PATH}")
        model = joblib.load(MODEL_PATH)
        
        print(f"Membaca data dari: {input_csv_path}")
        df = pd.read_csv(input_csv_path)
        
        # PERBAIKAN: Nama kolom disesuaikan dengan contoh CSV Anda
        feature_columns = ['pH', 'kelembaban', 'suhu']
        print(f"Menggunakan fitur: {feature_columns}")
        
        if not all(col in df.columns for col in feature_columns):
            raise ValueError(f"Kolom fitur {feature_columns} tidak ditemukan di file CSV.")

        features = df[feature_columns]
        
        print("Melakukan prediksi...")
        predictions = model.predict(features)
        
        status_map = {1: 'Sehat', 0: 'Tidak Sehat'}
        df['status_prediksi'] = [status_map.get(p, "Error") for p in predictions]
        print("Prediksi kondisi tanah selesai.")
        
        df.to_csv(OUTPUT_PATH, index=False)
        print(f"Hasil analisis tanah berhasil disimpan di: {OUTPUT_PATH}")
        return True, "Analisis berhasil"
        
    except FileNotFoundError:
        error_msg = f"Error: File model tidak ditemukan di {MODEL_PATH}. Pastikan model sudah ada."
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Terjadi error saat analisis tanah: {e}"
        print(error_msg)
        return False, error_msg
