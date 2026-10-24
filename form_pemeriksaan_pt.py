import os
import sqlite3
from datetime import date
from flask import Flask, request, redirect, url_for, render_template_string

BASE = r"D:\DATA_TANAMAN"
DB = os.path.join(BASE, "tanaman.db")

app = Flask(__name__)

def connect():
    con = sqlite3.connect(DB, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def has_table(con, name):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,)
    ).fetchone() is not None

def init_table():
    with connect() as con:
        if not has_table(con, "tanaman"):
            raise RuntimeError("Tabel tanaman tidak ditemukan.")
        if not has_table(con, "monitoring_pokok"):
            con.execute("""
                CREATE TABLE monitoring_pokok (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tanaman_id INTEGER NOT NULL,
                    tanggal_pemeriksaan TEXT NOT NULL,
                    kondisi TEXT,
                    kondisi_daun TEXT,
                    kondisi_batang TEXT,
                    hama_penyakit TEXT,
                    catatan TEXT,
                    foto TEXT,
                    petugas TEXT,
                    tindak_lanjut TEXT,
                    dibuat_pada TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tanaman_id) REFERENCES tanaman(id)
                )
            """)

PAGE = """
<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pemeriksaan Pokok | DATA TANAMAN</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f1f5f3;color:#1d3027;font:15px Arial,sans-serif}
header{background:#174b35;color:white;padding:24px 5%}header h1{margin:0 0 8px}
main{max-width:1100px;margin:25px auto;padding:0 16px}
.panel{background:white;padding:22px;border-radius:14px;margin-bottom:18px;border:1px solid #dce7e0}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}
label{display:block;font-weight:600;margin-bottom:7px}
input,select,textarea{width:100%;padding:11px;border:1px solid #cbd5ce;border-radius:8px;font:inherit;background:white}
textarea{min-height:85px;resize:vertical}.full{grid-column:1/-1}
button,.link{display:inline-block;background:#176444;color:white;border:0;border-radius:8px;padding:12px 17px;text-decoration:none;cursor:pointer}
table{width:100%;border-collapse:collapse;min-width:720px}th,td{padding:11px;text-align:left;border-bottom:1px solid #e3e9e5}
th{background:#e8f2ec}.scroll{overflow:auto}.muted{color:#627168}
@media(max-width:650px){.grid{grid-template-columns:1fr}.full{grid-column:auto}}
</style></head><body>
<header><h1>Pemeriksaan Tanaman per Pokok</h1>
<div>DATA TANAMAN · Catat kondisi aktual di lapangan</div></header>
<main>
{% if pesan %}<div class="panel">{{ pesan }}</div>{% endif %}
<section class="panel"><h2>Form pemeriksaan</h2>
<form method="post" action="/simpan">
<div class="grid">
<div><label>Nomor pokok *</label><select name="tanaman_id" required>
<option value="">Pilih pokok</option>
{% for p in plants %}<option value="{{ p['id'] }}">{{ p['nomor'] }} — {{ p['lokasi'] or 'Lokasi belum diisi' }}</option>{% endfor %}
</select></div>
<div><label>Tanggal pemeriksaan *</label><input type="date" name="tanggal" value="{{ today }}" required></div>
<div><label>Kondisi keseluruhan *</label><select name="kondisi" required>
<option value="">Pilih kondisi</option><option>Sehat</option><option>Perlu perhatian</option><option>Sakit</option><option>Mati</option><option>Belum dapat dinilai</option>
</select></div>
<div><label>Kondisi daun</label><select name="daun">
<option value="">Pilih kondisi daun</option><option>Normal</option><option>Menguning</option><option>Layu</option><option>Rusak</option><option>Rontok</option><option>Tidak dapat dinilai</option>
</select></div>
<div><label>Kondisi batang</label><select name="batang">
<option value="">Pilih kondisi batang</option><option>Normal</option><option>Luka</option><option>Busuk</option><option>Patah</option><option>Tidak dapat dinilai</option>
</select></div>
<div><label>Nama petugas *</label><input name="petugas" maxlength="100" required></div>
<div class="full"><label>Hama atau penyakit yang ditemukan</label><input name="hama" maxlength="500" placeholder="Tuliskan temuan, atau kosongkan jika tidak ada"></div>
<div class="full"><label>Catatan pemeriksaan</label><textarea name="catatan" maxlength="3000"></textarea></div>
<div class="full"><label>Tindakan yang disarankan</label><textarea name="tindakan" maxlength="2000"></textarea></div>
</div><p><button type="submit">Simpan pemeriksaan</button></p>
</form></section>
<section class="panel"><h2>Riwayat pemeriksaan terbaru</h2>
<div class="scroll"><table><thead><tr><th>Tanggal</th><th>Nomor pokok</th><th>Kondisi</th><th>Daun</th><th>Batang</th><th>Hama/penyakit</th><th>Petugas</th></tr></thead>
<tbody>{% for r in records %}<tr><td>{{ r['tanggal_pemeriksaan'] or '-' }}</td><td>{{ r['nomor'] }}</td><td>{{ r['kondisi'] or '-' }}</td><td>{{ r['kondisi_daun'] or '-' }}</td><td>{{ r['kondisi_batang'] or '-' }}</td><td>{{ r['hama_penyakit'] or '-' }}</td><td>{{ r['petugas'] or '-' }}</td></tr>{% else %}<tr><td colspan="7">Belum ada catatan pemeriksaan.</td></tr>{% endfor %}</tbody>
</table></div></section>
<p class="muted">Modul terpisah. Belum terintegrasi dengan login admin aplikasi utama.</p>
</main></body></html>
"""

@app.route("/", methods=["GET"])
def index():
    pesan = request.args.get("pesan", "")
    with connect() as con:
        plants = con.execute("SELECT * FROM tanaman ORDER BY nomor").fetchall()
        if not has_table(con, "monitoring_pokok"):
            records = []
        else:
            cols = {r["name"] for r in con.execute("PRAGMA table_info(monitoring_pokok)")}
            if "tanaman_id" not in cols:
                records = []
            else:
                records = con.execute("""
                    SELECT m.*, t.nomor
                    FROM monitoring_pokok m
                    LEFT JOIN tanaman t ON t.id = m.tanaman_id
                    ORDER BY m.id DESC LIMIT 100
                """).fetchall()
    return render_template_string(PAGE, plants=plants, records=records,
                                  today=date.today().isoformat(), pesan=pesan)

@app.route("/simpan", methods=["POST"])
def simpan():
    init_table()
    tanaman_id = request.form.get("tanaman_id", type=int)
    tanggal = request.form.get("tanggal", "").strip()
    kondisi = request.form.get("kondisi", "").strip()
    petugas = request.form.get("petugas", "").strip()

    if not tanaman_id or not tanggal or not kondisi or not petugas:
        return redirect(url_for("index", pesan="Isi semua kolom wajib."))

    values = (
        tanaman_id, tanggal, kondisi,
        request.form.get("daun", "").strip(),
        request.form.get("batang", "").strip(),
        request.form.get("hama", "").strip(),
        request.form.get("catatan", "").strip(),
        petugas,
        request.form.get("tindakan", "").strip()
    )

    with connect() as con:
        if not con.execute("SELECT 1 FROM tanaman WHERE id=?", (tanaman_id,)).fetchone():
            return redirect(url_for("index", pesan="Nomor pokok tidak ditemukan."))

        cols = {r["name"] for r in con.execute("PRAGMA table_info(monitoring_pokok)")}
        required = {"tanaman_id", "tanggal_pemeriksaan", "kondisi"}
        if not required.issubset(cols):
            return redirect(url_for("index", pesan="Struktur tabel monitoring berbeda. Data tidak disimpan."))

        data = {
            "tanaman_id": values[0],
            "tanggal_pemeriksaan": values[1],
            "kondisi": values[2],
            "kondisi_daun": values[3],
            "kondisi_batang": values[4],
            "hama_penyakit": values[5],
            "catatan": values[6],
            "petugas": values[7],
            "tindak_lanjut": values[8]
        }
        usable = {k: v for k, v in data.items() if k in cols}
        keys = list(usable.keys())
        sql = "INSERT INTO monitoring_pokok (" + ",".join(keys) + ") VALUES (" + ",".join("?" for _ in keys) + ")"
        con.execute(sql, tuple(usable[k] for k in keys))

    return redirect(url_for("index", pesan="Pemeriksaan berhasil disimpan."))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5013, debug=False)
