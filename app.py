"""Dreamkeeper versi pribadi (12 tabel).
Jalankan: python app.py  lalu buka http://127.0.0.1:5000
"""
import os
import sqlite3
from datetime import date, datetime

from flask import Flask, g, redirect, render_template, request, url_for, flash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dreamkeeper.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
PENGGUNA_ID = 1  # versi pribadi: satu pengguna

app = Flask(__name__)
app.secret_key = "dreamkeeper-pribadi"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Buat database dari schema.sql jika belum ada."""
    if not os.path.exists(DB_PATH):
        con = sqlite3.connect(DB_PATH)
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            con.executescript(f.read())
        con.commit()
        con.close()


def hitung_menit(jam_mulai, jam_selesai):
    """Durasi tidur dalam menit, bisa melewati tengah malam."""
    if not jam_mulai or not jam_selesai:
        return None
    t1 = datetime.strptime(jam_mulai, "%H:%M")
    t2 = datetime.strptime(jam_selesai, "%H:%M")
    selisih = (t2 - t1).total_seconds() / 60
    if selisih < 0:
        selisih += 24 * 60
    return int(selisih)


def format_durasi(menit):
    if menit is None:
        return "-"
    return f"{menit // 60}j {menit % 60:02d}m"


def kategori_screen_time(db, menit):
    """Cari kategori dari tabel kategori_screen_time berdasarkan total menit."""
    row = db.execute(
        "SELECT nama FROM kategori_screen_time WHERE ? BETWEEN batas_min_menit AND batas_maks_menit",
        (menit,),
    ).fetchone()
    return row["nama"] if row else "-"


def ambil_harian(db, batas_baris=None):
    """Gabungkan catatan harian, total screen time, dan mood lewat JOIN."""
    sql = """
        SELECT c.id_catatan, c.tanggal, c.jam_tidur, c.jam_bangun,
               m.skor AS mood,
               COALESCE(SUM(p.durasi_menit), 0) AS screen_time_menit
        FROM catatan_harian c
        LEFT JOIN penggunaan_aplikasi p ON p.id_catatan = c.id_catatan
        LEFT JOIN mood_harian m ON m.id_catatan = c.id_catatan
        WHERE c.id_pengguna = ?
        GROUP BY c.id_catatan
        ORDER BY c.tanggal DESC
    """
    params = [PENGGUNA_ID]
    if batas_baris:
        sql += " LIMIT ?"
        params.append(batas_baris)
    hasil = []
    for r in db.execute(sql, params).fetchall():
        menit_layar = r["screen_time_menit"]
        kat = kategori_screen_time(db, menit_layar)
        tidur = hitung_menit(r["jam_tidur"], r["jam_bangun"])
        hasil.append({
            "tanggal": r["tanggal"],
            "screen_time": menit_layar,
            "kategori": kat,
            "tidur": tidur,
            "mood": r["mood"],
            "berlebihan": kat == "Berlebihan",
        })
    return hasil


def target_tidur(db):
    row = db.execute(
        "SELECT target_tidur_menit FROM profil_tidur WHERE id_pengguna = ?", (PENGGUNA_ID,)
    ).fetchone()
    return row["target_tidur_menit"] if row else 450


@app.route("/")
def dashboard():
    db = get_db()
    harian = ambil_harian(db, batas_baris=7)
    target = target_tidur(db)
    n = len(harian)

    rata_screen = sum(h["screen_time"] for h in harian) // n if n else None
    tidur_list = [h["tidur"] for h in harian if h["tidur"] is not None]
    rata_tidur = sum(tidur_list) // len(tidur_list) if tidur_list else None
    mood_list = [h["mood"] for h in harian if h["mood"] is not None]
    rata_mood = round(sum(mood_list) / len(mood_list), 1) if mood_list else "-"
    hari_berlebihan = sum(1 for h in harian if h["berlebihan"])

    tidur_berlebihan = [h["tidur"] for h in harian if h["berlebihan"] and h["tidur"] is not None]
    tidur_lainnya = [h["tidur"] for h in harian if not h["berlebihan"] and h["tidur"] is not None]
    pola = None
    if tidur_berlebihan and tidur_lainnya:
        pola = {
            "berlebihan": format_durasi(sum(tidur_berlebihan) // len(tidur_berlebihan)),
            "lainnya": format_durasi(sum(tidur_lainnya) // len(tidur_lainnya)),
        }

    return render_template(
        "dashboard.html",
        harian=harian,
        n=n,
        rata_screen=format_durasi(rata_screen),
        rata_tidur=format_durasi(rata_tidur),
        target=format_durasi(target),
        target_menit=target,
        hari_berlebihan=hari_berlebihan,
        rata_mood=rata_mood,
        pola=pola,
        format_durasi=format_durasi,
    )


@app.route("/catat", methods=["GET", "POST"])
def catat():
    db = get_db()
    aplikasi = db.execute("SELECT id_aplikasi, nama FROM aplikasi ORDER BY nama").fetchall()
    aktivitas = db.execute("SELECT id_aktivitas, nama FROM aktivitas_offline ORDER BY nama").fetchall()

    if request.method == "POST":
        tanggal = request.form.get("tanggal") or date.today().isoformat()
        jam_tidur = request.form.get("jam_tidur") or None
        jam_bangun = request.form.get("jam_bangun") or None
        skor = request.form.get("skor_mood", type=int)
        catatan_mood = (request.form.get("catatan_mood") or "").strip() or None

        if tanggal > date.today().isoformat():
            flash("Tanggal tidak boleh di masa depan.", "error")
            return redirect(url_for("catat"))

        try:
            # 1. Catatan harian: satu baris per pengguna per tanggal
            db.execute(
                """
                INSERT INTO catatan_harian (id_pengguna, tanggal, jam_tidur, jam_bangun)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id_pengguna, tanggal) DO UPDATE SET
                    jam_tidur = excluded.jam_tidur,
                    jam_bangun = excluded.jam_bangun
                """,
                (PENGGUNA_ID, tanggal, jam_tidur, jam_bangun),
            )
            id_catatan = db.execute(
                "SELECT id_catatan FROM catatan_harian WHERE id_pengguna = ? AND tanggal = ?",
                (PENGGUNA_ID, tanggal),
            ).fetchone()["id_catatan"]

            # 2. Penggunaan aplikasi: ganti isian lama dengan isian baru
            db.execute("DELETE FROM penggunaan_aplikasi WHERE id_catatan = ?", (id_catatan,))
            for a in aplikasi:
                menit = request.form.get(f"app_{a['id_aplikasi']}", type=int)
                if menit and menit > 0:
                    db.execute(
                        "INSERT INTO penggunaan_aplikasi (id_catatan, id_aplikasi, durasi_menit) VALUES (?, ?, ?)",
                        (id_catatan, a["id_aplikasi"], menit),
                    )

            # 3. Mood: simpan jika diisi, hapus jika dikosongkan
            if skor:
                db.execute(
                    """
                    INSERT INTO mood_harian (id_catatan, skor, catatan) VALUES (?, ?, ?)
                    ON CONFLICT(id_catatan) DO UPDATE SET skor = excluded.skor, catatan = excluded.catatan
                    """,
                    (id_catatan, skor, catatan_mood),
                )
            else:
                db.execute("DELETE FROM mood_harian WHERE id_catatan = ?", (id_catatan,))

            # 4. Aktivitas offline
            db.execute("DELETE FROM catatan_aktivitas WHERE id_catatan = ?", (id_catatan,))
            for akt in request.form.getlist("aktivitas"):
                db.execute(
                    "INSERT INTO catatan_aktivitas (id_catatan, id_aktivitas) VALUES (?, ?)",
                    (id_catatan, int(akt)),
                )

            db.commit()
            flash("Catatan tersimpan.", "ok")
        except sqlite3.IntegrityError as e:
            db.rollback()
            flash(f"Data tidak valid: {e}", "error")
        return redirect(url_for("catat", tanggal=tanggal))

    # GET: tampilkan form, bisa membuka catatan tanggal tertentu untuk diedit
    tanggal = request.args.get("tanggal", date.today().isoformat())
    catatan = db.execute(
        "SELECT * FROM catatan_harian WHERE id_pengguna = ? AND tanggal = ?",
        (PENGGUNA_ID, tanggal),
    ).fetchone()
    durasi, terpilih, mood = {}, set(), None
    if catatan:
        for row in db.execute(
            "SELECT id_aplikasi, durasi_menit FROM penggunaan_aplikasi WHERE id_catatan = ?",
            (catatan["id_catatan"],),
        ):
            durasi[row["id_aplikasi"]] = row["durasi_menit"]
        for row in db.execute(
            "SELECT id_aktivitas FROM catatan_aktivitas WHERE id_catatan = ?",
            (catatan["id_catatan"],),
        ):
            terpilih.add(row["id_aktivitas"])
        mood = db.execute(
            "SELECT skor, catatan FROM mood_harian WHERE id_catatan = ?", (catatan["id_catatan"],)
        ).fetchone()

    return render_template(
        "catat.html",
        tanggal=tanggal,
        catatan=catatan,
        mood=mood,
        aplikasi=aplikasi,
        aktivitas=aktivitas,
        durasi=durasi,
        terpilih=terpilih,
        hari_ini=date.today().isoformat(),
    )


@app.route("/riwayat")
def riwayat():
    db = get_db()
    return render_template("riwayat.html", data=ambil_harian(db), format_durasi=format_durasi,
                           target_menit=target_tidur(db))


@app.route("/tips")
def tips():
    db = get_db()
    # JOIN tips ke sumber_referensi agar setiap saran bisa ditelusuri ke jurnalnya
    daftar = db.execute(
        """
        SELECT t.isi, s.judul, s.penulis, s.tahun, s.doi, s.url
        FROM tips t
        JOIN sumber_referensi s ON s.id_sumber = t.id_sumber
        ORDER BY t.id_tips
        """
    ).fetchall()
    return render_template("tips.html", daftar=daftar)


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
