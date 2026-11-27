-- Skema database Dreamkeeper (SQLite), 12 tabel sesuai desain kelompok.
-- Dijalankan ulang setiap kali database dibuat dari awal.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS tips;
DROP TABLE IF EXISTS sumber_referensi;
DROP TABLE IF EXISTS catatan_aktivitas;
DROP TABLE IF EXISTS aktivitas_offline;
DROP TABLE IF EXISTS mood_harian;
DROP TABLE IF EXISTS penggunaan_aplikasi;
DROP TABLE IF EXISTS catatan_harian;
DROP TABLE IF EXISTS kategori_screen_time;
DROP TABLE IF EXISTS aplikasi;
DROP TABLE IF EXISTS kategori_aplikasi;
DROP TABLE IF EXISTS profil_tidur;
DROP TABLE IF EXISTS pengguna;

-- 1. Data akun mahasiswa
CREATE TABLE pengguna (
    id_pengguna INTEGER PRIMARY KEY,
    nama        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    dibuat_pada TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 2. Target jam tidur tiap pengguna (1 pengguna = 1 profil)
CREATE TABLE profil_tidur (
    id_profil          INTEGER PRIMARY KEY,
    id_pengguna        INTEGER NOT NULL UNIQUE REFERENCES pengguna(id_pengguna) ON DELETE CASCADE,
    target_tidur_menit INTEGER NOT NULL CHECK (target_tidur_menit BETWEEN 60 AND 720)
);

-- 3. Master kategori aplikasi
CREATE TABLE kategori_aplikasi (
    id_kategori INTEGER PRIMARY KEY,
    nama        TEXT NOT NULL UNIQUE
);

-- 4. Master daftar aplikasi
CREATE TABLE aplikasi (
    id_aplikasi INTEGER PRIMARY KEY,
    nama        TEXT NOT NULL UNIQUE,
    id_kategori INTEGER NOT NULL REFERENCES kategori_aplikasi(id_kategori)
);

-- 5. Master kategori total screen time harian beserta batas menitnya
CREATE TABLE kategori_screen_time (
    id_kategori_st  INTEGER PRIMARY KEY,
    nama            TEXT NOT NULL UNIQUE,
    batas_min_menit INTEGER NOT NULL CHECK (batas_min_menit >= 0),
    batas_maks_menit INTEGER NOT NULL,
    CHECK (batas_maks_menit >= batas_min_menit)
);

-- 6. Satu catatan per pengguna per tanggal
CREATE TABLE catatan_harian (
    id_catatan  INTEGER PRIMARY KEY,
    id_pengguna INTEGER NOT NULL REFERENCES pengguna(id_pengguna) ON DELETE CASCADE,
    tanggal     TEXT NOT NULL,            -- format YYYY-MM-DD
    jam_tidur   TEXT,                     -- format HH:MM
    jam_bangun  TEXT,                     -- format HH:MM
    UNIQUE (id_pengguna, tanggal)
);

-- 7. Durasi tiap aplikasi dalam satu hari. Total screen time dihitung dari tabel ini.
CREATE TABLE penggunaan_aplikasi (
    id_penggunaan INTEGER PRIMARY KEY,
    id_catatan    INTEGER NOT NULL REFERENCES catatan_harian(id_catatan) ON DELETE CASCADE,
    id_aplikasi   INTEGER NOT NULL REFERENCES aplikasi(id_aplikasi),
    durasi_menit  INTEGER NOT NULL CHECK (durasi_menit >= 0),
    UNIQUE (id_catatan, id_aplikasi)
);

-- 8. Skor mood dan catatan singkat per hari (1 catatan harian = 1 mood)
CREATE TABLE mood_harian (
    id_mood    INTEGER PRIMARY KEY,
    id_catatan INTEGER NOT NULL UNIQUE REFERENCES catatan_harian(id_catatan) ON DELETE CASCADE,
    skor       INTEGER NOT NULL CHECK (skor BETWEEN 1 AND 5),
    catatan    TEXT
);

-- 9. Master aktivitas di luar layar
CREATE TABLE aktivitas_offline (
    id_aktivitas INTEGER PRIMARY KEY,
    nama         TEXT NOT NULL UNIQUE
);

-- 10. Aktivitas offline yang dilakukan pada hari tertentu (many-to-many)
CREATE TABLE catatan_aktivitas (
    id_catatan   INTEGER NOT NULL REFERENCES catatan_harian(id_catatan) ON DELETE CASCADE,
    id_aktivitas INTEGER NOT NULL REFERENCES aktivitas_offline(id_aktivitas),
    PRIMARY KEY (id_catatan, id_aktivitas)
);

-- 11. Daftar jurnal dan sumber resmi
CREATE TABLE sumber_referensi (
    id_sumber   INTEGER PRIMARY KEY,
    judul       TEXT NOT NULL,
    penulis     TEXT NOT NULL,
    tahun       INTEGER NOT NULL,
    doi         TEXT,
    url         TEXT NOT NULL,
    tanggal_cek TEXT NOT NULL              -- kapan sumber ini terakhir dicek
);

-- 12. Tips tidur, setiap tips wajib terhubung ke satu sumber
CREATE TABLE tips (
    id_tips   INTEGER PRIMARY KEY,
    isi       TEXT NOT NULL,
    id_sumber INTEGER NOT NULL REFERENCES sumber_referensi(id_sumber)
);

-- ===== DATA MASTER =====

INSERT INTO pengguna (id_pengguna, nama, email) VALUES (1, 'Pengguna Pribadi', 'pribadi@lokal');

INSERT INTO profil_tidur (id_profil, id_pengguna, target_tidur_menit) VALUES (1, 1, 450);

INSERT INTO kategori_aplikasi (id_kategori, nama) VALUES
    (1, 'Media sosial'),
    (2, 'Komunikasi'),
    (3, 'Belajar'),
    (4, 'Gim'),
    (5, 'Lainnya');

INSERT INTO aplikasi (id_aplikasi, nama, id_kategori) VALUES
    (1, 'Instagram', 1),
    (2, 'TikTok', 1),
    (3, 'YouTube', 1),
    (4, 'WhatsApp', 2),
    (5, 'Google Classroom', 3),
    (6, 'Mobile Legends', 4),
    (7, 'Lainnya', 5);

INSERT INTO kategori_screen_time (id_kategori_st, nama, batas_min_menit, batas_maks_menit) VALUES
    (1, 'Ringan', 0, 119),
    (2, 'Sedang', 120, 299),
    (3, 'Berlebihan', 300, 1440);

INSERT INTO aktivitas_offline (id_aktivitas, nama) VALUES
    (1, 'Jalan kaki'),
    (2, 'Olahraga'),
    (3, 'Membaca buku'),
    (4, 'Bertemu teman'),
    (5, 'Memasak');

INSERT INTO sumber_referensi (id_sumber, judul, penulis, tahun, doi, url, tanggal_cek) VALUES
    (1, 'Hubungan Durasi Screen Time Smartphone dengan Durasi Tidur pada Mahasiswa FK Unisba',
        'Noeradiana dkk.', 2024, '10.29313/jiks.v6i1.11498',
        'https://ejournal.unisba.ac.id/index.php/jiks/article/download/11498/pdf', '2026-11-20'),
    (2, 'Jurnal Pandu Husada, Vol. 7 No. 3',
        'Malau & Utami', 2026, NULL,
        'https://jurnal.umsu.ac.id/index.php/JPH/article/download/28773/15059', '2026-11-20'),
    (3, 'MAHESA Malahayati, Vol. 3 No. 7',
        'Putra & Ulia', 2023, '10.33024/mahesa.v3i7.10358',
        'https://ejurnalmalahayati.ac.id/index.php/MAHESA/article/download/10358/Download%20Artikel', '2026-11-20'),
    (4, 'Naskah Publikasi FK UMS',
        'Rozak & Hernawan', 2023, NULL,
        'https://eprints.ums.ac.id/122270/2/Naskah%20Publikasi.pdf', '2026-11-20'),
    (5, 'Journal of Qualitative Health Research & Case Studies Reports, Vol. 6 No. 3',
        'Ani, Suratini & Sudyasih', 2026, '10.56922/quilt.v6i3.2711',
        'https://e-jurnal.iphorr.com/index.php/qlt/article/download/2711/3405/19690', '2026-11-20');

INSERT INTO tips (id_tips, isi, id_sumber) VALUES
    (1, 'Perhatikan jika screen time harian melebihi 5 jam. Penelitian FK Unisba (2024) menemukan sebagian besar mahasiswa dengan kebiasaan ini tidurnya kurang dari 7 jam.', 1),
    (2, 'Perhatikan kebiasaan memakai HP secara berlebihan. Penelitian MAHESA (2023) mengaitkan kecanduan smartphone dengan kualitas tidur mahasiswa.', 3),
    (3, 'Saran umum: letakkan HP di luar jangkauan saat hendak tidur. Penelitian FK UMS (2023) mengaitkan durasi penggunaan smartphone dengan kualitas tidur.', 4),
    (4, 'Hubungan screen time dan tidur belum konsisten di semua kelompok. Jurnal Pandu Husada (2026) tidak menemukan hubungan yang signifikan pada mahasiswa Kedokteran yang diteliti.', 2),
    (5, 'Pada siswa SMA, penggunaan gadget berhubungan lemah dengan tidur (r = 0,156). Hasil ini menunjukkan hubungannya tidak selalu besar.', 5);
