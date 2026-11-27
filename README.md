# Dreamkeeper (versi pribadi, 12 tabel)

Aplikasi web sederhana untuk mencatat screen time dan jam tidur harian.
Database: SQLite, dibuat otomatis dari `schema.sql` saat pertama kali dijalankan.

## Cara menjalankan

```bash
pip install -r requirements.txt
python app.py
```

Lalu buka http://127.0.0.1:5000

## Tabel (12)

1. pengguna
2. profil_tidur
3. kategori_aplikasi
4. aplikasi
5. kategori_screen_time
6. catatan_harian
7. penggunaan_aplikasi
8. mood_harian
9. aktivitas_offline
10. catatan_aktivitas
11. sumber_referensi
12. tips

## Catatan

- Versi ini untuk satu pengguna, tanpa login.
- Kategori screen time (Ringan, Sedang, Berlebihan) dihitung dari tabel `kategori_screen_time`.
- Setiap tips di halaman Tips terhubung ke satu baris `sumber_referensi`.
