from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
import os
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "tanaman.db")

app = Flask(__name__)
app.secret_key = os.environ.get("TANAMAN_SECRET_KEY", "ganti-kunci-monitoring")

HTML = """
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monitoring Pokok | DATA TANAMAN</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f3f6f4;color:#203329;font-family:Arial,sans-serif}
header{background:#174d35;color:white;padding:22px 5%}
header h1{margin:0 0 7px;font-size:24px}
header p{margin:0;color:#dcebe1}
main{max-width:1100px;margin:25px auto;padding:0 18px}
.panel{background:white;border:1px solid #e0e8e2;border-radius:12px;padding:22px;margin-bottom:20px}
h2{font-size:19px;margin:0 0 18px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}
label{font-size:13px;font-weight:bold;display:block;margin-bottom:7px}
input,select,textarea{width:100%;padding:11px;border:1px solid #ccd8cf;border-radius:7px;font:inherit;background:white}
textarea{min-height:90px;resize:vertical}
.full{grid-column:1/-1}
button{background:#17623f;color:white;border:0;border-radius:7px;padding:12px 18px;font-weight:bold;cursor:pointer}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;border-bottom:1px solid #e5ebe6;padding:12px;font-size:13px}
th{background:#f2f6f3}
.table-wrap{overflow-x:auto}
.notice{padding:12px;background:#edf6ee;border-radius:8px;margin-bottom:16px}
@media(max-width:650px){.grid{grid-template-columns:1fr}.full{grid-column:auto}.panel{padding:15px}}
</style>
</head>
<body>
<header>
<h1>Monitoring Pokok Tanaman</h1>
<p>DATA TANAMAN · Pencatatan kondisi lapangan</p>
</header>
<main>
{% if pesan %}<div class="notice">{{ pesan }}</div>{% endif %}
<section class="panel">
<h2>Form Pemeriksaan Pokok</h2>
<form method="post">
<div class="grid">
<div>
<label>ID Pokok / ID Tanaman *</label>
<input name="tanaman_id" type="number" min="1" required>
</div>
<div>
<label>Tanggal Pemeriksaan *</label>
<input name="tanggal" type="date" value="{{ hari_ini }}" required>
</div>
<div>
<label>Kondisi Tanaman *</label>
<select name="kondisi" required>
<option value="Sehat">Sehat</option>
<option value="Kurang Sehat">Kurang sehat</option>
<option value="Sakit">Sakit</option>
<option value="Mati">Mati</option>
<option value="Perlu Pemeriksaan">Perlu pemeriksaan</option>
</select>
</div>
<div>
<label>Kondisi Daun</label>
<select name="daun">
<option value="">Belum dinilai</option>
<option>Normal</option><option>Menguning</option>
<option>Layu</option><option>Rusak</option>
</select>
</div>
<div>
<label>Kondisi Batang</label>
<select name="batang">
<option value="">Belum dinilai</option>
<option>Normal</option><option>Rusak</option>
<option>Busuk</option><option>Patah</option>
</select>
</div>
<div>
<label>Hama / Penyakit</label>
<input name="hama" maxlength="300" placeholder="Isi jika ditemukan">
</div>
<div>
<label>Nama Petugas *</label>
<input name="petugas" maxlength="100" required>
</div>
<div>
<label>Tindak Lanjut</label>
<select name="tindak">
<option value="Tidak ada">Tidak ada</option>
<option value="Perlu pemeriksaan ulang">Pemeriksaan ulang</option>
<option value="Perlu perawatan">Perlu perawatan</option>
<option value="Perlu penggantian">Perlu penggantian</option>
</select>
</div>
<div class="full">
<label>Catatan Pemeriksaan</label>
<textarea name="catatan" maxlength="3000" placeholder="Temuan dan kondisi aktual tanaman"></textarea>
</div>
<div class="full">
<button type="submit">Simpan Pemeriksaan</button>
</div>
</div>
</form>
</section>
<section class="panel">
<h2>Riwayat Pemeriksaan Terbaru</h2>
<div class="table-wrap">
<table>
<thead><tr><th>Tanggal</th><th>ID Pokok</th><th>Kondisi</th><th>Hama/Penyakit</th><th>Petugas</th></tr></thead>
<tbody>
{% for r in rows %}
<tr><td>{{ r[1] }}</td><td>{{ r[0] }}</td><td>{{ r[2] }}</td><td>{{ r[3] or '-' }}</td><td>{{ r[4] }}</td></tr>
{% else %}
<tr><td colspan="5">Belum ada pemeriksaan yang tercatat.</td></tr>
{% endfor %}
</tbody>
</table>
</div>
</section>
</main>
</body>
</html>
"""

def koneksi():
    con = sqlite3.connect(DB, timeout=15)
    con.execute("""
        CREATE TABLE IF NOT EXISTS monitoring_pokok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanaman_id INTEGER NOT NULL,
            tanggal_pemeriksaan TEXT NOT NULL,
            kondisi TEXT NOT NULL,
            kondisi_daun TEXT,
            kondisi_batang TEXT,
            hama_penyakit TEXT,
            catatan TEXT,
            foto TEXT,
            petugas TEXT,
            tindak_lanjut TEXT,
            dibuat_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return con

@app.route("/", methods=["GET", "POST"])
def monitoring():
    pesan = ""
    if request.method == "POST":
        try:
            tanaman_id = int(request.form["tanaman_id"])
            tanggal = request.form["tanggal"]
            kondisi = request.form["kondisi"]
            petugas = request.form["petugas"].strip()

            if tanaman_id < 1 or not tanggal or not petugas:
                raise ValueError("ID pokok, tanggal, dan petugas wajib diisi.")

            with koneksi() as con:
                con.execute("""
                    INSERT INTO monitoring_pokok
                    (tanaman_id, tanggal_pemeriksaan, kondisi,
                     kondisi_daun, kondisi_batang, hama_penyakit,
                     catatan, petugas, tindak_lanjut)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tanaman_id, tanggal, kondisi,
                    request.form.get("daun", ""),
                    request.form.get("batang", ""),
                    request.form.get("hama", "").strip(),
                    request.form.get("catatan", "").strip(),
                    petugas,
                    request.form.get("tindak", "Tidak ada")
                ))

            return redirect(url_for("monitoring", tersimpan="1"))
        except (ValueError, KeyError) as e:
            pesan = str(e) or "Periksa kembali isian formulir."
        except sqlite3.Error:
            pesan = "Database gagal menyimpan data. Periksa database dan backup."

    if request.args.get("tersimpan") == "1":
        pesan = "Pemeriksaan berhasil disimpan."

    try:
        with koneksi() as con:
            rows = con.execute("""
                SELECT tanaman_id, tanggal_pemeriksaan, kondisi,
                       hama_penyakit, petugas
                FROM monitoring_pokok
                ORDER BY id DESC LIMIT 100
            """).fetchall()
    except sqlite3.Error:
        rows = []
        pesan = "Gagal membaca riwayat pemeriksaan."

    return render_template_string(
        HTML, rows=rows, pesan=pesan, hari_ini=date.today().isoformat()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
