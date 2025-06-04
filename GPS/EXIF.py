from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def get_exif_data(image_path):
    image = Image.open(image_path)
    exif_data = {}
    
    if image._getexif():
        for tag, value in image._getexif().items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == "GPSInfo":
                gps_data = {}
                for gps_tag in value:
                    gps_tag_name = GPSTAGS.get(gps_tag, gps_tag)
                    gps_data[gps_tag_name] = value[gps_tag]
                exif_data["GPSInfo"] = gps_data
            else:
                exif_data[tag_name] = value
    return exif_data

def save_exif_to_file(exif_data, filename="output.exif"):
    with open(filename, "w") as f:
        for key, value in exif_data.items():
            f.write(f"{key}: {value}\n")

# Ganti dengan path gambar drone kamu
image_path = "DJI_20250503170534_0024_D.JPG"

# Ekstrak dan simpan EXIF
exif_data = get_exif_data(image_path)
save_exif_to_file(exif_data, "gambar_DJI_0012.exif")

print("File EXIF berhasil disimpan sebagai 'gambar_DJI_0012.exif'")
