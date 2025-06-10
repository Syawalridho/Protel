import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-geotiff';

const Map = ({ 
  useGps, 
  geoTiffUrl, 
  // 1. Tambahkan props baru dengan nilai default (peta Indonesia)
  initialCenter = [-2.5489, 118.0149], 
  initialZoom = 5 
}) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const geoTiffLayerRef = useRef(null);

  useEffect(() => {
    // Inisialisasi peta hanya jika belum ada instans
    if (mapRef.current && !mapInstanceRef.current) {
      mapInstanceRef.current = L.map(mapRef.current, {
        // 2. Gunakan props untuk inisialisasi peta
        center: initialCenter,
        zoom: initialZoom,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(mapInstanceRef.current);
    }

    // Hapus layer GeoTIFF lama jika ada sebelum membuat yang baru
    if (geoTiffLayerRef.current) {
        mapInstanceRef.current.removeLayer(geoTiffLayerRef.current);
        geoTiffLayerRef.current = null;
    }

    // Logika untuk menampilkan layer GeoTIFF (tidak berubah)
    if (geoTiffUrl && mapInstanceRef.current) {
      console.log(Mencoba memuat GeoTIFF dari: ${geoTiffUrl});
      
      const options = {};
      const geoTiffLayer = L.leafletGeotiff(geoTiffUrl, options);
      geoTiffLayer.addTo(mapInstanceRef.current);
      geoTiffLayerRef.current = geoTiffLayer;

      geoTiffLayer.on('load', () => {
        console.log("GeoTIFF event 'load' terpicu.");
        const bounds = geoTiffLayer.getBounds();
        console.log("[DEBUG] Bounds dari GeoTIFF:", bounds);

        if (bounds && bounds.isValid()) {
          console.log("[DEBUG] Bounds valid, melakukan fitBounds...");
          mapInstanceRef.current.fitBounds(bounds);
        } else {
          console.warn("PERINGATAN: GeoTIFF dimuat, tetapi tidak memiliki informasi batas (bounds) yang valid.");
          alert("Peta berhasil dimuat, tetapi tidak ada informasi lokasi di dalamnya. Peta tidak bisa di-zoom otomatis ke area tersebut.");
        }
      });

      geoTiffLayer.on('error', (e) => {
        console.error("Terjadi error pada layer GeoTIFF. Detail Event:", e);
        if (e.error) {
            console.error("Penyebab utama (kemungkinan error jaringan atau parsing):", e.error);
        }
        alert("Gagal memuat file peta GeoTIFF. Cek console (F12) untuk detail error yang lebih spesifik.");
      });
    }

    // Logika untuk GPS (tidak diubah)
    if (useGps && mapInstanceRef.current) {
      // kode geolocation Anda ditempatkan di sini...
    }

  // 3. Tambahkan props ke dependency array agar peta merespons perubahan (jika diperlukan)
  }, [useGps, geoTiffUrl, initialCenter, initialZoom]); 

  return (
    <div ref={mapRef} className="w-full h-full bg-gray-200 rounded-lg shadow-inner"></div>
  );
};

export default Map;