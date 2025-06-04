import exifread
from PIL import Image
import os

# === Konversi koordinat DMS ke Desimal ===
def dms_to_decimal(dms, ref):
    degrees, minutes, seconds = dms
    decimal = degrees + minutes / 60 + seconds / 3600
    if ref in ['S', 'W']:
        decimal *= -1
    return decimal

# === Ambil data GPS dari EXIF foto ===
def extract_gps(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)

    def get_dms(tag):
        return tuple(float(x.num) / float(x.den) for x in tags[tag].values)

    lat = get_dms('GPS GPSLatitude')
    lon = get_dms('GPS GPSLongitude')
    lat_ref = str(tags['GPS GPSLatitudeRef'])
    lon_ref = str(tags['GPS GPSLongitudeRef'])
    altitude = float(tags['GPS GPSAltitude'].values[0].num) / float(tags['GPS GPSAltitude'].values[0].den)

    return dms_to_decimal(lat, lat_ref), dms_to_decimal(lon, lon_ref), altitude


# === Hitung koordinat GPS dari piksel deteksi ===
def estimate_object_coordinates(img_path, det_path):
    lat0, lon0, alt = extract_gps(img_path)
    img = Image.open(img_path)
    width, height = img.size

    # Anggap cakupan FOV kamera drone adalah 84° horizontal & 63° vertikal (DJI standard)
    HFOV = 84
    VFOV = 63

    # Perhitungan panjang area yang tercakup (berbasis FOV dan altitude)
    import math
    ground_width = 2 * alt * math.tan(math.radians(HFOV / 2))
    ground_height = 2 * alt * math.tan(math.radians(VFOV / 2))

    gps_per_px_x = ground_width / width
    gps_per_px_y = ground_height / height

    results = []

    with open(det_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            cls, x_center, y_center, w, h = map(float, line.strip().split())
            px_x = x_center * width
            px_y = y_center * height

            dx_m = (px_x - width / 2) * gps_per_px_x
            dy_m = (px_y - height / 2) * gps_per_px_y

            # Konversi offset meter ke derajat (kurang akurat tapi cukup untuk estimasi kasar)
            lat_offset = -(dy_m / 111320)  # 1 derajat lat = ~111.32 km
            lon_offset = dx_m / (111320 * math.cos(math.radians(lat0)))

            est_lat = lat0 + lat_offset
            est_lon = lon0 + lon_offset

            results.append({
                'class': int(cls),
                'center_x_px': px_x,
                'center_y_px': px_y,
                'latitude': est_lat,
                'longitude': est_lon
            })

    return results

# === MAIN ===
image_path = 'DJI_20250503170534_0024_D.JPG'
detection_path = 'detections/drone.txt'

detected_objects = estimate_object_coordinates(image_path, detection_path)

# Cetak hasil
for i, obj in enumerate(detected_objects):
    print(f"Objek {i+1}:")
    print(f"  Kelas         : {obj['class']}")
    print(f"  Posisi piksel : ({obj['center_x_px']:.1f}, {obj['center_y_px']:.1f})")
    print(f"  Koordinat GPS : ({obj['latitude']:.7f}, {obj['longitude']:.7f})")
    print()
