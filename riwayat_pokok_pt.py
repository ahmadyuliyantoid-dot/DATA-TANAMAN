import os
import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)
DB = r"D:\DATA_TANAMAN\tanaman.db"

PAGE = """
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Riwayat per Pokok | DATA TANAMAN</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f3f6f4;color:#24352c;font:14px Arial,sans-serif}
header{background:#174b35;color:#fff;padding:25px 4%}
header h1{margin:0 0 8px;font-size:25px}
main{max-width:1250px;margin:24px auto;padding:0 16px}
.panel{background:#fff;padding:20px;border:1px solid #dfe8e2;border-radius:12px;margin-bottom:18px}
.filters{display:flex;gap:12px;flex-wrap:wrap;align-items:end}
label{display:block;font-weight:bold;margin-bottom:7px}
select,input{padding:11px;border:1px solid #cbd5ce;border-radius:8px;min-width:220px;max-width:100%}
button{padding:11px 16px;border:0;border-radius:8px;background:#176444;color:white;cursor:pointer}
.tablebox{overflow:auto}
table{width:100%;border-collapse:collapse;min-width:900px}
th,td{padding:11px;text-align:left;border-bottom:1px solid #e4e9e5;vertical-align:top}
th{background:#e8f1eb}
.muted{color:#627168}
@media print{header{background:white;color:black}button,.filters{display:none}body{background:white}}
</style>
</head>
<body>
<header>
<h1>Riwayat Tanaman per Pokok</h1>
<div>DATA TANAMAN · Rekam jejak pemeriksaan untuk kebutuhan operasional PT</div>
</header>
<main>
<section class="panel">
<h2>Pilih pokok tanaman</h2>
<form method="get" class="filters">
<div><label>Nomor pokok</label>
<select name="tanaman_id">
<option value="">Semua pokok</option>
{% for p in plants %}
<option value="{{ p['id'] }}" {% if selected == p['id']|string %}selected{% endif %}>
{{ p['nomor'] }} — {{ p['lokasi'] or 'Lokasi belum diisi' }}
</option>
{% endfor %}
</select></div>
<div><label>Cari petugas / temuan</label>
<input name="q" value="{{ q }}" placeholder="Nama petugas atau hama/penyakit"></div>
<div><button type="submit">Tampilkan</button></div>
<div><button type="button" onclick="window.print()">Cetak / PDF</button></div>
</form>
</section>
<section class="panel">
<h2>Catatan pemeriksaan</h2>
<p class="muted">Jumlah catatan yang ditampilkan: {{ records|length }}</p>
<div class="tablebox"><table>
<thead><tr><th>Tanggal</th><th>Nomor pokok</th><th>Kondisi</th><th>Daun</th><th>Batang</th><th>Hama / penyakit</th><th>Catatan</th><th>Petugas</th><th>Tindakan disarankan</th></tr></thead>
<tbody>
{% for r in records %}
<tr><td>{{ r['tanggal_pemeriksaan'] or '-' }}</td>
<td>{{ r['nomor'] or '-' }}</td><td>{{ r['kondisi'] or '-' }}</td>
<td>{{ r['kondisi_daun'] or '-' }}</td><td>{{ r['kondisi_batang'] or '-' }}</td>
<td>{{ r['hama_penyakit'] or '-' }}</td><td>{{ r['catatan'] or '-' }}</td>
<td>{{ r['petugas'] or '-' }}</td><td>{{ r['tindak_lanjut'] or '-' }}</td></tr>
{% else %}
<tr><td colspan="9">Belum ada catatan untuk filter ini.</td></tr>
{% endfor %}
</tbody></table></div>
</section>
<p class="muted">Halaman baca-saja. Untuk memasukkan catatan baru, gunakan modul pemeriksaan yang telah disiapkan.</p>
</main></body></html>
"""

def get_columns(con, table):
    return {r["name"] for r in con.execute(f"PRAGMA table_info({table})")}

@app.route("/")
def index():
    if not os.path.isfile(DB):
        return "Database tanaman.db tidak ditemukan.", 500

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        tables = {r["name"] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if "tanaman" not in tables:
            return "Tabel tanaman tidak ditemukan.", 500

        plants = con.execute(
            "SELECT id, nomor, lokasi FROM tanaman ORDER BY nomor"
        ).fetchall()

        selected = request.args.get("tanaman_id", "").strip()
        q = request.args.get("q", "").strip()
        records = []

        if "monitoring_pokok" in tables:
            cols = get_columns(con, "monitoring_pokok")
            if "tanaman_id" in cols:
                allowed = [
                    "tanggal_pemeriksaan", "kondisi", "kondisi_daun",
                    "kondisi_batang", "hama_penyakit", "catatan",
                    "petugas", "tindak_lanjut"
                ]
                selected_cols = [c for c in allowed if c in cols]
                select_sql = ", ".join("m." + c for c in selected_cols)
                if select_sql:
                    sql = (
                        "SELECT t.nomor, " + select_sql +
                        " FROM monitoring_pokok m "
                        "LEFT JOIN tanaman t ON t.id=m.tanaman_id WHERE 1=1"
                    )
                    params = []
                    if selected:
                        try:
                            int(selected)
                            sql += " AND m.tanaman_id=?"
                            params.append(int(selected))
                        except ValueError:
                            selected = ""
                    if q:
                        searchable = [
                            c for c in ("petugas", "hama_penyakit", "catatan")
                            if c in cols
                        ]
                        if searchable:
                            sql += " AND (" + " OR ".join(
                                "COALESCE(m." + c + ",'') LIKE ?" for c in searchable
                            ) + ")"
                            params.extend(["%" + q + "%"] * len(searchable))
                    order = "m.id DESC" if "id" in cols else "m.tanaman_id"
                    sql += " ORDER BY " + order + " LIMIT 1000"
                    records = con.execute(sql, params).fetchall()

        return render_template_string(
            PAGE, plants=plants, records=records,
            selected=selected, q=q
        )
    finally:
        con.close()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5014, debug=False)
