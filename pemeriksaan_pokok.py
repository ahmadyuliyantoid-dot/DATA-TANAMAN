from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
import os
from datetime import date

app = Flask(__name__)
DB = r"D:\DATA_TANAMAN\tanaman.db"

HTML = """
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pemeriksaan Pokok Tanaman</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f1f5f9;color:#172b4d;font-family:Arial,sans-serif}
header{background:#153b32;color:white;padding:24px}
header h1{margin:0 0 8px;font-size:24px}
header p{margin:0;color:#d5e8df}
main{max-width:900px;margin:25px auto;padding:0 16px}
.panel{background:white;border:1px solid #e2e8f0;border-radius:14px;padding:24px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
label{display:block;font-weight:bold;font-size:13px;margin-bottom:7px}
input,select,textarea{width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:8px;font:inherit}
textarea{min-height:90px;resize:vertical}
.field{margin-bottom:16px}
.full{grid-column:1/-1}
button{background:#17664f;color:white;border:0;border-radius:8px;padding:12px 18px;font-weight:bold;cursor:pointer}
.note{padding:12px;border-radius:8px;margin-bottom:16px;background:#ecfdf5;color:#166534}
.error{background:#fef2f2;color:#991b1b}
a{color:#17664f}
@media(max-width:600px){.grid{grid-template-columns:1fr}.full{grid-column:auto}}
</style>
</head>
<body>
<header>
<h1>Pemeriksaan Pokok Tanaman</h1>
<p>Pencatatan kondisi lapangan per tanaman</p>
</header>
<main>
<div class="panel">
{% if pesan %}<div class="note {{ 'error' if gagal else '' }}">{{ pesan }}</div>{% endif %}
<form method="post">
<div class="grid">
<div class="field full">
<label>Nomor / Nama Pokok *</label>
<select name="tanaman_id" required>
<option value="">-- Pilih pokok tanaman --</option>
{% for t in tanaman %}
<option value="{{ t.id }}" {% if pilihan == t.id|string %}selected{% endif %}>
{{ t.nomor or ('ID-' ~ t.id) }} — {{ t.nama or 'Tanpa nama' }} ({{ t.lokasi or 'Lokasi belum diisi' }})
</option>
{% endfor %}
</select>
</div>
<div class="field">
<label>Tanggal Pemeriksaan *</label>
<input type="date" name="tanggal" value="{{ hari_ini }}" required>
</div>
<div class="field">
<label>Kondisi Tanaman *</label>
<select name="kondisi" required>
<option value="">-- Pilih kondisi --</option>
<option>Sehat</option><option>Perlu Perhatian</option>
<option>Sakit</option><option>Kritis</option><option>Mati</option>
</select>
</div>
<div class="field">
<label>Kondisi Daun</label>
<select name="daun">
<option value="">-- Pilih --</option>
<option>Normal</option><option>Menguning</option>
<option>Layu</option><option>Bercak / Berlubang</option>
<option>Rontok</option><option>Rusak Berat</option>
</select>
</div>
<div class="field">
<label>Kondisi Batang</label>
<select name="batang">
<option value="">-- Pilih --</option>
<option>Normal</option><option>Luka</option>
<option>Busuk</option><option>Retak / Patah</option>
<option>Diserang Hama</option>
</select>
</div>
<div class="field full">
<label>Hama / Penyakit</label>
<input name="hama" maxlength="500" placeholder="Tuliskan jika ditemukan">
</div>
<div class="field">
<label>Nama Petugas *</label>
<input name="petugas" maxlength="150" required>
</div>
<div class="field">
<label>Tindak Lanjut</label>
<input name="tindak" maxlength="500" placeholder="Contoh: periksa ulang 3 hari lagi">
</div>
<div class="field full">
<label>Catatan Lapangan</label>
<textarea name="catatan" maxlength="3000" placeholder="Temuan pemeriksaan..."></textarea>
</div>
<div class="field full">
<button type="submit">Simpan Pemeriksaan</button>
</div>
</div>
</form>
<p><a href="http://127.0.0.1:5002/">Kembali ke Dashboard</a></p>
</div>
</main>
</body>
</html>
"""

def koneksi():
    if not os.path.isfile(DB):
        raise RuntimeError("Database tanaman.db tidak ditemukan.")
    con = sqlite3.connect(DB, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=20000")
    return con

def halaman(con, pesan="", gagal=False, pilihan=""):
    tanaman = con.execute(
        "SELECT id, nomor, nama, lokasi FROM tanaman ORDER BY nomor, id"
    ).fetchall()
    return render_template_string(
        HTML, tanaman=tanaman, pesan=pesan, gagal=gagal,
        pilihan=str(pilihan), hari_ini=date.today().isoformat()
    )

@app.route("/", methods=["GET", "POST"])
def index():
    con = koneksi()
    try:
        if request.method == "POST":
            tanaman_id = request.form.get("tanaman_id", "").strip()
            tanggal = request.form.get("tanggal", "").strip()
            kondisi = request.form.get("kondisi", "").strip()
            petugas = request.form.get("petugas", "").strip()

            if not tanaman_id.isdigit():
                return halaman(con, "Pilih pokok tanaman yang valid.", True)
            if not tanggal or not kondisi or not petugas:
                return halaman(con, "Tanggal, kondisi, dan petugas wajib diisi.", True, tanaman_id)

            valid = con.execute(
                "SELECT id FROM tanaman WHERE id = ?", (int(tanaman_id),)
            ).fetchone()
            if not valid:
                return halaman(con, "Tanaman tidak ditemukan di database.", True)

            con.execute("""
                INSERT INTO monitoring_pokok (
                    tanaman_id, tanggal_pemeriksaan, kondisi,
                    kondisi_daun, kondisi_batang, hama_penyakit,
                    catatan, petugas, tindak_lanjut, dibuat_pada
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
            """, (
                int(tanaman_id), tanggal, kondisi,
                request.form.get("daun", "").strip(),
                request.form.get("batang", "").strip(),
                request.form.get("hama", "").strip(),
                request.form.get("catatan", "").strip(),
                petugas, request.form.get("tindak", "").strip()
            ))
            con.commit()
            return halaman(con, "Pemeriksaan berhasil disimpan.")

        return halaman(con)
    except sqlite3.Error as e:
        con.rollback()
        return halaman(con, "Gagal menyimpan data: " + str(e), True)
    finally:
        con.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)
