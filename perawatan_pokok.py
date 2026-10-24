from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
import os
from datetime import date

app = Flask(__name__)
DB = r"D:\DATA_TANAMAN\tanaman.db"

HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Perawatan Pokok Tanaman</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f3f6f4;color:#1f2937;font-family:Arial,sans-serif}
header{background:#14532d;color:white;padding:24px 5%}
header h1{margin:0 0 8px;font-size:25px}
header p{margin:0;color:#dcfce7}
nav{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
nav a{background:#166534;color:white;text-decoration:none;padding:10px 14px;border-radius:8px}
main{max-width:1400px;margin:24px auto;padding:0 18px}
.panel{background:white;border:1px solid #e5e7eb;border-radius:12px;padding:22px;margin-bottom:20px}
h2{font-size:19px;margin:0 0 18px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
label{display:block;font-size:13px;font-weight:bold;margin-bottom:7px}
input,select,textarea{width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:8px;font:14px Arial;background:white}
textarea{min-height:85px;resize:vertical}
.full{grid-column:1/-1}
button{background:#166534;color:white;border:0;border-radius:8px;padding:12px 18px;font-weight:bold;cursor:pointer}
.msg{padding:13px;border-radius:8px;margin-bottom:16px;background:#dcfce7;color:#166534}
.err{background:#fee2e2;color:#991b1b}
.table-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;min-width:1050px}
th,td{text-align:left;padding:12px;border-bottom:1px solid #e5e7eb;font-size:13px;vertical-align:top;line-height:1.5}
th{background:#f8fafc;color:#475569;white-space:nowrap}
.small{font-size:12px;color:#64748b;margin-top:14px}
@media(max-width:700px){.grid{grid-template-columns:1fr}.full{grid-column:auto}.panel{padding:14px}}
</style>
</head>
<body>
<header>
<h1>Perawatan Pokok Tanaman</h1>
<p>Catatan kegiatan perawatan, pemakaian bahan, biaya dan hasil per pokok.</p>
<nav>
<a href="http://127.0.0.1:5002">Dashboard</a>
<a href="http://127.0.0.1:5003">Pemeriksaan</a>
<a href="http://127.0.0.1:5004">Riwayat Pemeriksaan</a>
<a href="http://127.0.0.1:5005">Tindak Lanjut</a>
</nav>
</header>
<main>
{% if pesan %}<div class="msg">{{ pesan }}</div>{% endif %}
{% if error %}<div class="msg err">{{ error }}</div>{% endif %}

<section class="panel">
<h2>Input Kegiatan Perawatan</h2>
{% if tanaman %}
<form method="post" class="grid">
<div>
<label for="tanaman_id">Pokok Tanaman *</label>
<select id="tanaman_id" name="tanaman_id" required>
<option value="">-- Pilih pokok --</option>
{% for t in tanaman %}
<option value="{{ t['id'] }}">
{{ t['nomor'] or ('ID ' ~ t['id']) }} - {{ t['nama'] or 'Tanpa nama' }}{% if t['lokasi'] %} ({{ t['lokasi'] }}){% endif %}
</option>
{% endfor %}
</select>
</div>
<div>
<label for="tanggal_perawatan">Tanggal Perawatan *</label>
<input type="date" id="tanggal_perawatan" name="tanggal_perawatan"
value="{{ hari_ini }}" required>
</div>
<div>
<label for="jenis_perawatan">Jenis Perawatan *</label>
<select id="jenis_perawatan" name="jenis_perawatan" required>
<option value="">-- Pilih kegiatan --</option>
<option>Pemupukan</option>
<option>Penyiraman</option>
<option>Penyiangan</option>
<option>Pengendalian Hama</option>
<option>Pengendalian Penyakit</option>
<option>Pemangkasan</option>
<option>Perbaikan Drainase</option>
<option>Penggantian Tanaman</option>
<option>Lainnya</option>
</select>
</div>
<div>
<label for="petugas">Petugas Pelaksana *</label>
<input id="petugas" name="petugas" required placeholder="Nama petugas">
</div>
<div>
<label for="bahan">Bahan / Produk yang Digunakan</label>
<input id="bahan" name="bahan" placeholder="Nama bahan atau produk">
</div>
<div>
<label for="dosis">Dosis / Jumlah Penggunaan</label>
<input id="dosis" name="dosis" placeholder="Contoh: 200 gram per pokok">
</div>
<div>
<label for="biaya">Biaya (Rp)</label>
<input id="biaya" name="biaya" type="number" min="0" step="0.01" value="0">
</div>
<div>
<label for="hasil">Hasil Perawatan</label>
<select id="hasil" name="hasil">
<option value="">Belum dievaluasi</option>
<option>Berhasil</option>
<option>Perlu Pemantauan</option>
<option>Belum Berhasil</option>
</select>
</div>
<div class="full">
<label for="catatan">Catatan Perawatan</label>
<textarea id="catatan" name="catatan" placeholder="Keterangan tambahan, kondisi sebelum/sesudah, atau kebutuhan lanjutan"></textarea>
</div>
<div class="full">
<button type="submit">Simpan Perawatan</button>
<p class="small">Data disimpan ke tabel perawatan_pokok pada database tanaman.db.</p>
</div>
</form>
{% else %}
<p>Belum ada data tanaman untuk dipilih.</p>
{% endif %}
</section>

<section class="panel">
<h2>Riwayat Perawatan ({{ daftar|length }} catatan terbaru)</h2>
<div class="table-wrap">
<table>
<thead><tr>
<th>Tanggal</th><th>Nomor Pokok</th><th>Nama</th><th>Lokasi</th>
<th>Jenis Perawatan</th><th>Bahan</th><th>Dosis</th><th>Biaya (Rp)</th>
<th>Petugas</th><th>Hasil</th><th>Catatan</th>
</tr></thead>
<tbody>
{% for r in daftar %}
<tr>
<td>{{ r['tanggal_perawatan'] or '-' }}</td>
<td><strong>{{ r['nomor'] or ('ID ' ~ r['tanaman_id']) }}</strong></td>
<td>{{ r['nama'] or '-' }}</td>
<td>{{ r['lokasi'] or '-' }}</td>
<td>{{ r['jenis_perawatan'] or '-' }}</td>
<td>{{ r['bahan'] or '-' }}</td>
<td>{{ r['dosis'] or '-' }}</td>
<td>{{ "{:,.2f}".format(r['biaya'] or 0) }}</td>
<td>{{ r['petugas'] or '-' }}</td>
<td>{{ r['hasil'] or 'Belum dievaluasi' }}</td>
<td>{{ r['catatan'] or '-' }}</td>
</tr>
{% else %}
<tr><td colspan="11">Belum ada kegiatan perawatan yang dicatat.</td></tr>
{% endfor %}
</tbody>
</table>
</div>
<p class="small">Riwayat ditampilkan dari tanggal terbaru, maksimal 500 catatan.</p>
</section>
</main>
</body>
</html>
"""


def koneksi():
    if not os.path.isfile(DB):
        raise FileNotFoundError("Database tidak ditemukan: " + DB)
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    return con


@app.route("/", methods=["GET", "POST"])
def beranda():
    pesan = ""
    error = ""

    if request.method == "POST":
        tanaman_id = request.form.get("tanaman_id", "").strip()
        tanggal = request.form.get("tanggal_perawatan", "").strip()
        jenis = request.form.get("jenis_perawatan", "").strip()
        bahan = request.form.get("bahan", "").strip()
        dosis = request.form.get("dosis", "").strip()
        petugas = request.form.get("petugas", "").strip()
        hasil = request.form.get("hasil", "").strip()
        catatan = request.form.get("catatan", "").strip()
        biaya_text = request.form.get("biaya", "0").strip()

        jenis_valid = [
            "Pemupukan", "Penyiraman", "Penyiangan",
            "Pengendalian Hama", "Pengendalian Penyakit",
            "Pemangkasan", "Perbaikan Drainase",
            "Penggantian Tanaman", "Lainnya"
        ]
        hasil_valid = ["", "Berhasil", "Perlu Pemantauan", "Belum Berhasil"]

        if not tanaman_id.isdigit():
            error = "Silakan pilih pokok tanaman yang valid."
        elif not tanggal or not jenis or not petugas:
            error = "Tanggal, jenis perawatan dan petugas wajib diisi."
        elif jenis not in jenis_valid or hasil not in hasil_valid:
            error = "Pilihan jenis perawatan atau hasil tidak valid."
        else:
            try:
                biaya = float(biaya_text or "0")
                if biaya < 0:
                    raise ValueError()
            except ValueError:
                biaya = None
                error = "Biaya harus berupa angka nol atau lebih."

            if not error:
                try:
                    with koneksi() as con:
                        ada = con.execute(
                            "SELECT id FROM tanaman WHERE id = ?",
                            (int(tanaman_id),)
                        ).fetchone()

                        if not ada:
                            error = "Pokok tanaman tidak ditemukan."
                        else:
                            con.execute("""
                                INSERT INTO perawatan_pokok
                                (tanaman_id, tanggal_perawatan, jenis_perawatan,
                                 bahan, dosis, biaya, petugas, hasil, catatan,
                                 dibuat_pada)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                int(tanaman_id), tanggal, jenis,
                                bahan, dosis, biaya, petugas, hasil, catatan,
                                date.today().isoformat()
                            ))
                            con.commit()
                            return redirect(url_for("beranda", sukses="1"))

                except Exception as e:
                    error = "Gagal menyimpan perawatan: " + str(e)

    if request.args.get("sukses") == "1":
        pesan = "Catatan perawatan berhasil disimpan."

    try:
        with koneksi() as con:
            tanaman = con.execute("""
                SELECT id, nomor, nama, lokasi
                FROM tanaman
                ORDER BY nomor, id
            """).fetchall()

            daftar = con.execute("""
                SELECT p.id, p.tanaman_id, p.tanggal_perawatan,
                       p.jenis_perawatan, p.bahan, p.dosis, p.biaya,
                       p.petugas, p.hasil, p.catatan,
                       t.nomor, t.nama, t.lokasi
                FROM perawatan_pokok p
                LEFT JOIN tanaman t ON t.id = p.tanaman_id
                ORDER BY p.tanggal_perawatan DESC, p.id DESC
                LIMIT 500
            """).fetchall()

        return render_template_string(
            HTML,
            tanaman=tanaman,
            daftar=daftar,
            pesan=pesan,
            error=error,
            hari_ini=date.today().isoformat()
        )

    except Exception as e:
        return (
            "<h2>Gagal membuka modul perawatan</h2><pre>"
            + str(e).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;") + "</pre>",
            500
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=False)
