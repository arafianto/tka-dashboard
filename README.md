# TKA Dashboard

Aplikasi internal untuk memantau Tenaga Kerja Asing (TKA) aktif dan mengelola dokumen legalnya (RPTKA, IMTA/Notifikasi, Visa, KITAS, SKTT, Paspor).

## Ringkasan Fitur
- Dashboard ringkasan: Total TKA, Dokumen aktif/kedaluwarsa, daftar dokumen akan habis ≤ 90 hari.
- CRUD: Perusahaan, Pekerja, Dokumen.
- Detail Pekerja: daftar semua dokumen milik pekerja.
- Perpanjangan Dokumen: form perpanjangan dengan penyimpanan riwayat (audit trail).
- Ekspor: CSV untuk Pekerja dan Dokumen.
- Admin: Django Admin untuk manajemen data tambahan.

## Arsitektur Singkat
- Framework: Django 5 + Django Templates + Bootstrap 5.
- App utama: `dashboard`.
- DB: PostgreSQL (via `.env`) dengan fallback SQLite.
- Struktur UI: `templates/base.html` dengan sidebar navigasi.

## Persiapan Lingkungan
1) Buat virtualenv dan install dependency
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Konfigurasi environment (.env) - opsional jika pakai SQLite
```
POSTGRES_DB=nama_db
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

3) Migrasi database dan jalankan server
```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

4) Buat superuser (untuk akses Admin)
```
python manage.py createsuperuser
```

5) Akses aplikasi
- Aplikasi: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Alur Kerja Harian
- Tambahkan Perusahaan, lalu Pekerja (relasi ke Perusahaan), kemudian Dokumen per Pekerja.
- Pantau Dashboard untuk dokumen yang akan habis (warna: ≤30 merah, ≤60 kuning, ≤90 biru).
- Klik "Perpanjang" pada dokumen untuk input nomor/tanggal baru dan simpan riwayat.
- Gunakan menu Ekspor di Dashboard untuk CSV Pekerja/Dokumen.

## Model Data
- Perusahaan (`Company`)
- Pekerja (`Worker`)
- Dokumen (`Document`) dengan jenis, nomor, tanggal terbit/berakhir, status, sisa hari.
- Riwayat Perpanjangan (`RenewalHistory`) untuk audit trail per dokumen.

## Penamaan & Bahasa
- Bahasa aplikasi: Indonesia (`LANGUAGE_CODE = 'id'`).
- Label model dan field sudah disesuaikan Bahasa Indonesia untuk konsistensi di Form/Admin.

## Standar Kode & Kontribusi
- Ikuti PEP8 dan konvensi Django.
- Tambah unit test jika menambah logika bisnis baru.
- Untuk perubahan model, buat migrasi: `python manage.py makemigrations && python manage.py migrate`.
- Gunakan view, form, dan template yang ada sebagai referensi gaya.

## Pengembangan & Penambahan Fitur
- Reminders terjadwal: disarankan menambah command management + cron/CI scheduler untuk notifikasi otomatis (email/Slack). Dasar query sudah ada di view dashboard.
- Ekspor Excel: library `openpyxl` sudah tersedia; tambahkan endpoint baru jika diperlukan.
- Pencarian/Filter lanjutan: tambah filter di `worker_list` dan `document_list` sesuai kebutuhan.

## Deployment (Ringkas)
- Set `DEBUG=False`, isi `ALLOWED_HOSTS`.
- Konfigurasi PostgreSQL di `.env` dan jalankan migrasi.
- Kumpulkan static files: `python manage.py collectstatic`.
- Jalankan via WSGI (gunicorn/uwsgi) di balik reverse proxy (nginx).

### Environment (.env contoh)
```
DEBUG=False
SECRET_KEY=ubah_ke_random_yang_sangat_panjang
ALLOWED_HOSTS=yourdomain.com,127.0.0.1

POSTGRES_DB=tka_db
POSTGRES_USER=tka_user
POSTGRES_PASSWORD=ubah_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
USE_PROXY_SSL_HEADER=True
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

### Gunicorn (systemd)
```
[Unit]
Description=TKA Dashboard Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/tka-dashboard
Environment="PATH=/srv/tka-dashboard/.venv/bin"
ExecStart=/srv/tka-dashboard/.venv/bin/gunicorn tka_dashboard.wsgi:application --bind 127.0.0.1:8001 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx (reverse proxy)
```
server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 10M;

    location /static/ {
        alias /srv/tka-dashboard/staticfiles/;
    }

    location /media/ {
        alias /srv/tka-dashboard/media/;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8001;
    }
}
```

### Reminder Dokumen (cron)
```
# contoh harian jam 07:00
0 7 * * * cd /srv/tka-dashboard && source .venv/bin/activate && python manage.py send_document_reminders >> /var/log/tka_reminders.log 2>&1
```

## Backup & Pemulihan
- Backup DB PostgreSQL rutin (pg_dump). Untuk SQLite, backup file `db.sqlite3`.
- Backup folder `media/` untuk file upload foto pekerja.

## Catatan Teknis
- Upload foto pekerja membutuhkan Pillow.
- Zona waktu: Asia/Jakarta.
- Folder utama: `dashboard/templates/core/*` untuk halaman, `templates/base.html` untuk layout.

## Panduan Perubahan ke Depan
- Perubahan skema model: perbarui model + migrasi + admin + form + template bila label berubah.
- Perubahan logika dokumen/masa berlaku: perbarui utilitas terkait pada `Document` (mis. `days_until_expiry`).
- UI/UX: konsisten gunakan komponen Bootstrap dan pola di `form.html`.

