from flask import Flask, request, Response
import sqlite3
import csv
import io
import os
from html import escape

app = Flask(__name__)
DB = r"D:\DATA_TANAMAN\tanaman.db"

def get_data(cari="", status=""):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    sql = """
    SELECT
        t.id,
        t.nomor,
        t.nama,
        t.jenis,
        t.lokasi,
        t.kondisi AS kondisi_master,
        m.tanggal_pemeriksaan,
        m.kondisi AS kondisi_periksa,
        m.kondisi_daun,
        m.kondisi_batang,
        m.hama_penyakit,
        m.petugas,
        m.tindak_lanjut,
        m.catatan
    FROM tanaman t
    LEFT JOIN monitoring_pokok m
      ON m.id = (
        SELECT m2.id
        FROM monitoring_pokok m2
        WHERE m2.tanaman_id = t.id
        ORDER BY m2.tanggal_pemeriksaan DESC, m2.id DESC
        LIMIT 1
      )
    WHERE (
        t.nomor LIKE ? OR t.nama LIKE ? OR
        t.lokasi LIKE ? OR t.jenis LIKE ?
    )
    """
    q = "%" + cari + "%"
    rows = con.execute(sql, (q, q, q, q)).fetchall()
    con.close()

    hasil = []
    for r in rows:
        d = dict(r)
        kondisi = (d.get("kondisi_periksa") or "").strip()
        d["status_monitoring"] = kondisi if kondisi else "Belum diperiksa"
        hasil.append(d)

    if status:
        hasil = [r for r in hasil if r["status_monitoring"].lower() == status.lower()]

    return hasil

def e(value):
    return escape(str(value if value is not None else ""))

@app.route("/")
def dashboard():
    cari = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    rows = get_data(cari, status)

    total = len(rows)
    belum = sum(r["status_monitoring"] == "Belum diperiksa" for r in rows)
    sehat = sum(r["status_monitoring"].lower() == "sehat" for r in rows)
    perhatian = sum(r["status_monitoring"].lower() in ("perlu perhatian", "sakit", "kritis", "mati") for r in rows)

    pilihan = [
        ("", "Semua status"),
        ("Belum diperiksa", "Belum diperiksa"),
        ("Sehat", "Sehat"),
        ("Perlu Perhatian", "Perlu Perhatian"),
        ("Sakit", "Sakit"),
        ("Kritis", "Kritis"),
        ("Mati", "Mati"),
    ]

    options = "".join(
        f'<option value="{e(v)}" {"selected" if status == v else ""}>{e(label)}</option>'
        for v, label in pilihan
    )

    trs = []
    for r in rows:
        st = r["status_monitoring"]
        badge = "normal" if st.lower() == "sehat" else "warning"
        if st == "Belum diperiksa":
            badge = "muted"

        trs.append(f"""
        <tr>
          <td><b>{e(r['nomor'])}</b></td>
          <td>{e(r['nama'])}</td>
          <td>{e(r['jenis'])}</td>
          <td>{e(r['lokasi'])}</td>
          <td><span class="badge {badge}">{e(st)}</span></td>
          <td>{e(r['tanggal_pemeriksaan'] or "—")}</td>
          <td>{e(r['kondisi_daun'] or "—")}</td>
          <td>{e(r['kondisi_batang'] or "—")}</td>
          <td>{e(r['hama_penyakit'] or "—")}</td>
          <td>{e(r['petugas'] or "—")}</td>
          <td>{e(r['tindak_lanjut'] or "—")}</td>
        </tr>
        """)

    table = "".join(trs) or '<tr><td colspan="11">Tidak ada data yang cocok.</td></tr>'

    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Monitoring Per Pokok | DATA TANAMAN</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f3f6f8;color:#172b3a;font:14px Arial,sans-serif}}
header{{background:#123d32;color:white;padding:24px 30px}}
header h1{{margin:0 0 7px;font-size:24px}}
header p{{margin:0;color:#d7e9df}}
main{{padding:24px;max-width:1600px;margin:auto}}
.cards{{display:grid;grid-template-columns:repeat(4,minmax(140px,1fr));gap:14px;margin-bottom:20px}}
.card{{background:white;padding:18px;border-radius:12px;border:1px solid #e0e8e5}}
.card span{{color:#62756d;font-size:13px}}
.card strong{{display:block;font-size:28px;margin-top:8px}}
.panel{{background:white;border:1px solid #e0e8e5;border-radius:12px;padding:18px;margin-bottom:18px}}
form{{display:flex;gap:10px;flex-wrap:wrap}}
input,select,button,.btn{{padding:11px 13px;border:1px solid #ccd8d3;border-radius:8px;font-size:14px}}
input{{flex:1;min-width:200px}}
button,.btn{{background:#17664e;color:white;border:0;text-decoration:none;cursor:pointer}}
.tablewrap{{overflow:auto}}
table{{border-collapse:collapse;width:100%;min-width:1200px}}
th,td{{padding:12px;text-align:left;border-bottom:1px solid #e7ece9;vertical-align:top}}
th{{background:#edf4f0;position:sticky;top:0;white-space:nowrap}}
.badge{{display:inline-block;padding:5px 9px;border-radius:20px;font-weight:bold;white-space:nowrap}}
.normal{{background:#d9f4e4;color:#17623a}}
.warning{{background:#fff0cf;color:#875400}}
.muted{{background:#e8edf1;color:#536473}}
.actions{{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}}
.small{{color:#64756f;font-size:12px;margin-top:12px}}
@media(max-width:760px){{main{{padding:12px}}header{{padding:20px}}.cards{{grid-template-columns:repeat(2,minmax(120px,1fr))}}}}
@media print{{form,.actions{{display:none}}body{{background:white}}main{{padding:0}}.panel,.card{{border:1px solid #bbb}}}}
</style>
</head>
<body>
<header>
<h1>Monitoring Tanaman per Pokok</h1>
<p>Dashboard pemeriksaan, kondisi terakhir, dan tindak lanjut lapangan</p>
</header>
<main>
<div class="cards">
<div class="card"><span>Total pokok pada hasil</span><strong>{total}</strong></div>
<div class="card"><span>Belum diperiksa</span><strong>{belum}</strong></div>
<div class="card"><span>Status sehat terakhir</span><strong>{sehat}</strong></div>
<div class="card"><span>Perlu perhatian / sakit / kritis / mati</span><strong>{perhatian}</strong></div>
</div>
<section class="panel">
<form method="get">
<input name="q" value="{e(cari)}" placeholder="Cari nomor pokok, nama, jenis, atau lokasi">
<select name="status">{options}</select>
<button type="submit">Cari / Filter</button>
<a class="btn" href="/export.csv?q={e(cari)}&status={e(status)}">Ekspor CSV</a>
</form>
<div class="small">Status ditampilkan dari pemeriksaan terbaru. “Belum diperiksa” berarti belum ada catatan inspeksi, bukan berarti tanaman sakit.</div>
</section>
<section class="panel">
<div class="tablewrap">
<table>
<thead><tr>
<th>Nomor Pokok</th><th>Nama</th><th>Jenis</th><th>Lokasi / Blok</th>
<th>Status Terakhir</th><th>Tanggal Periksa</th><th>Kondisi Daun</th>
<th>Kondisi Batang</th><th>Hama / Penyakit</th><th>Petugas</th><th>Tindak Lanjut</th>
</tr></thead>
<tbody>{table}</tbody>
</table>
</div>
<div class="actions"><button onclick="window.print()">Cetak Laporan</button></div>
</section>
</main>
</body>
</html>"""

@app.route("/export.csv")
def export_csv():
    cari = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    rows = get_data(cari, status)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Nomor Pokok", "Nama", "Jenis", "Lokasi / Blok",
        "Status Terakhir", "Tanggal Periksa", "Kondisi Daun",
        "Kondisi Batang", "Hama / Penyakit", "Petugas", "Tindak Lanjut"
    ])
    for r in rows:
        writer.writerow([
            r["nomor"], r["nama"], r["jenis"], r["lokasi"],
            r["status_monitoring"], r["tanggal_pemeriksaan"],
            r["kondisi_daun"], r["kondisi_batang"],
            r["hama_penyakit"], r["petugas"], r["tindak_lanjut"]
        ])

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=laporan_monitoring_pokok.csv"}
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=False)
