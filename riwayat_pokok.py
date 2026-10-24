from flask import Flask, request, render_template_string
import sqlite3
import os

app = Flask(__name__)

DB = r"D:\DATA_TANAMAN\tanaman.db"

HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Riwayat Pemeriksaan Pokok</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f3f6f4;color:#1f2937;
font-family:Arial,Helvetica,sans-serif}
header{background:#14532d;color:white;padding:24px 5%}
header h1{margin:0 0 8px;font-size:25px}
header p{margin:0;color:#dcfce7}
nav{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
nav a{color:white;text-decoration:none;background:#166534;
padding:10px 14px;border-radius:8px}
main{max-width:1450px;margin:24px auto;padding:0 18px}
.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
gap:14px;margin-bottom:20px}
.card{background:white;padding:20px;border-radius:12px;
box-shadow:0 2px 10px #0000000a;border:1px solid #e5e7eb}
.card span{font-size:13px;color:#64748b}
.card strong{display:block;font-size:28px;margin-top:10px;color:#166534}
.panel{background:white;border:1px solid #e5e7eb;border-radius:12px;
padding:20px;margin-bottom:20px}
h2{font-size:18px;margin:0 0 16px}
.filters{display:grid;grid-template-columns:2fr 1fr auto auto;
gap:10px;align-items:end}
label{font-size:13px;font-weight:bold;display:block;margin-bottom:7px}
input,select{width:100%;padding:11px;border:1px solid #cbd5e1;
border-radius:8px;background:white;font-size:14px}
button,.btn{border:0;border-radius:8px;padding:11px 16px;
background:#166534;color:white;font-weight:bold;cursor:pointer;
text-decoration:none;display:inline-block}
.btn-reset{background:#e5e7eb;color:#1f2937}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:1050px}
th,td{text-align:left;padding:12px;border-bottom:1px solid #e5e7eb;
vertical-align:top;font-size:13px;line-height:1.5}
th{background:#f8fafc;color:#475569;white-space:nowrap}
.badge{display:inline-block;padding:5px 9px;border-radius:20px;
font-size:12px;font-weight:bold;white-space:nowrap}
.sehat{background:#dcfce7;color:#166534}
.perhatian{background:#fef3c7;color:#92400e}
.sakit{background:#fee2e2;color:#991b1b}
.kritis,.mati{background:#7f1d1d;color:white}
.lain{background:#e2e8f0;color:#334155}
.empty{text-align:center;padding:36px;color:#64748b}
.small{font-size:12px;color:#64748b;margin-top:14px}
@media(max-width:760px){
 .cards{grid-template-columns:1fr}
 .filters{grid-template-columns:1fr}
 header h1{font-size:21px}
 main{padding:0 10px}
 .panel{padding:14px}
}
</style>
</head>
<body>
<header>
  <h1>Riwayat Pemeriksaan Tanaman</h1>
  <p>Catatan pemeriksaan, kondisi pokok, petugas dan tindak lanjut.</p>
  <nav>
    <a href="http://127.0.0.1:5002">Dashboard Pokok</a>
    <a href="http://127.0.0.1:5003">Input Pemeriksaan</a>
  </nav>
</header>
<main>
  <section class="cards">
    <div class="card">
      <span>Total catatan pemeriksaan</span>
      <strong>{{ total }}</strong>
    </div>
    <div class="card">
      <span>Pokok yang pernah diperiksa</span>
      <strong>{{ jumlah_pokok }}</strong>
    </div>
    <div class="card">
      <span>Pokok dengan catatan kondisi kritis terbaru</span>
      <strong>{{ kritis }}</strong>
    </div>
  </section>

  <section class="panel">
    <h2>Filter Riwayat</h2>
    <form method="get" class="filters">
      <div>
        <label for="q">Cari nomor, nama pokok, lokasi, petugas atau hama</label>
        <input id="q" name="q" value="{{ q }}"
          placeholder="Contoh: P001 atau nama petugas">
      </div>
      <div>
        <label for="kondisi">Kondisi pemeriksaan</label>
        <select id="kondisi" name="kondisi">
          <option value="">Semua kondisi</option>
          {% for item in pilihan %}
          <option value="{{ item }}" {% if kondisi == item %}selected{% endif %}>
            {{ item }}
          </option>
          {% endfor %}
        </select>
      </div>
      <button type="submit">Cari</button>
      <a class="btn btn-reset" href="/">Reset</a>
    </form>
    <p class="small">
      Ringkasan di atas memakai seluruh riwayat. Daftar di bawah mengikuti filter.
    </p>
  </section>

  <section class="panel">
    <h2>Daftar Riwayat ({{ hasil|length }} catatan)</h2>
    {% if hasil %}
    <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Tanggal</th>
          <th>Nomor Pokok</th>
          <th>Nama</th>
          <th>Lokasi</th>
          <th>Kondisi</th>
          <th>Kondisi Daun</th>
          <th>Kondisi Batang</th>
          <th>Hama / Penyakit</th>
          <th>Petugas</th>
          <th>Tindak Lanjut</th>
          <th>Catatan</th>
        </tr>
      </thead>
      <tbody>
      {% for r in hasil %}
        <tr>
          <td>{{ r['tanggal_pemeriksaan'] or '-' }}</td>
          <td><strong>{{ r['nomor'] or '-' }}</strong></td>
          <td>{{ r['nama'] or '-' }}</td>
          <td>{{ r['lokasi'] or '-' }}</td>
          <td>
            {% set k = (r['kondisi'] or '').lower() %}
            {% if k == 'sehat' %}
              <span class="badge sehat">{{ r['kondisi'] }}</span>
            {% elif k in ['perlu perhatian', 'perhatian'] %}
              <span class="badge perhatian">{{ r['kondisi'] }}</span>
            {% elif k == 'sakit' %}
              <span class="badge sakit">{{ r['kondisi'] }}</span>
            {% elif k in ['kritis', 'mati'] %}
              <span class="badge kritis">{{ r['kondisi'] }}</span>
            {% else %}
              <span class="badge lain">{{ r['kondisi'] or 'Belum diisi' }}</span>
            {% endif %}
          </td>
          <td>{{ r['kondisi_daun'] or '-' }}</td>
          <td>{{ r['kondisi_batang'] or '-' }}</td>
          <td>{{ r['hama_penyakit'] or '-' }}</td>
          <td>{{ r['petugas'] or '-' }}</td>
          <td>{{ r['tindak_lanjut'] or '-' }}</td>
          <td>{{ r['catatan'] or '-' }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
    {% else %}
      <div class="empty">
        <h3>Belum ada riwayat yang cocok</h3>
        <p>Jika belum pernah melakukan pemeriksaan, buka menu Input Pemeriksaan.</p>
        <a class="btn" href="http://127.0.0.1:5003">Input Pemeriksaan</a>
      </div>
    {% endif %}
  </section>
</main>
</body>
</html>
"""

PILIHAN = ["Sehat", "Perlu Perhatian", "Sakit", "Kritis", "Mati"]


def koneksi():
    if not os.path.isfile(DB):
        raise FileNotFoundError("Database tidak ditemukan: " + DB)
    return sqlite3.connect("file:D:/DATA_TANAMAN/tanaman.db?mode=ro",
                           uri=True, timeout=10)


@app.route("/")
def beranda():
    q = request.args.get("q", "").strip()
    kondisi = request.args.get("kondisi", "").strip()

    try:
        with koneksi() as con:
            con.row_factory = sqlite3.Row

            total = con.execute(
                "SELECT COUNT(*) FROM monitoring_pokok"
            ).fetchone()[0]

            jumlah_pokok = con.execute(
                "SELECT COUNT(DISTINCT tanaman_id) FROM monitoring_pokok"
            ).fetchone()[0]

            # Hitung kondisi dari pemeriksaan terakhir setiap pokok.
            kritis = con.execute("""
                SELECT COUNT(*) FROM (
                    SELECT m.tanaman_id, m.kondisi
                    FROM monitoring_pokok m
                    WHERE m.id = (
                        SELECT m2.id
                        FROM monitoring_pokok m2
                        WHERE m2.tanaman_id = m.tanaman_id
                        ORDER BY m2.tanggal_pemeriksaan DESC, m2.id DESC
                        LIMIT 1
                    )
                )
                WHERE LOWER(COALESCE(kondisi, '')) = 'kritis'
            """).fetchone()[0]

            sql = """
                SELECT
                    m.id,
                    m.tanggal_pemeriksaan,
                    m.kondisi,
                    m.kondisi_daun,
                    m.kondisi_batang,
                    m.hama_penyakit,
                    m.catatan,
                    m.petugas,
                    m.tindak_lanjut,
                    t.nomor,
                    t.nama,
                    t.lokasi
                FROM monitoring_pokok m
                JOIN tanaman t ON t.id = m.tanaman_id
                WHERE 1=1
            """
            params = []

            if q:
                sql += """
                    AND (
                        COALESCE(t.nomor, '') LIKE ?
                        OR COALESCE(t.nama, '') LIKE ?
                        OR COALESCE(t.lokasi, '') LIKE ?
                        OR COALESCE(m.petugas, '') LIKE ?
                        OR COALESCE(m.hama_penyakit, '') LIKE ?
                    )
                """
                term = "%" + q + "%"
                params.extend([term, term, term, term, term])

            if kondisi:
                sql += " AND LOWER(COALESCE(m.kondisi, '')) = LOWER(?)"
                params.append(kondisi)

            sql += """
                ORDER BY m.tanggal_pemeriksaan DESC, m.id DESC
                LIMIT 1000
            """
            hasil = con.execute(sql, params).fetchall()

        return render_template_string(
            HTML,
            total=total,
            jumlah_pokok=jumlah_pokok,
            kritis=kritis,
            hasil=hasil,
            q=q,
            kondisi=kondisi,
            pilihan=PILIHAN
        )

    except Exception as e:
        return (
            "<h2>Gagal membuka riwayat pemeriksaan</h2>"
            "<p>Periksa database dan struktur tabel.</p>"
            "<pre>" + str(e).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;") + "</pre>",
            500
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=False)
