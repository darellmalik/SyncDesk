# SyncDesk: IoT Media Controller

SyncDesk adalah sistem Internet of Things (IoT) yang memungkinkan pengguna mengontrol pemutaran media di laptop Windows menggunakan pergerakan (gestur) dari smartphone Android. Proyek ini membaca data akselerometer dan giroskop dari smartphone menggunakan Termux, lalu mengirimkannya ke laptop melalui protokol MQTT untuk dieksekusi sebagai tombol media (Play/Pause, Next, Previous).

## 🎛️ Fitur & Pemetaan Gestur

Kontrol media bersifat **global** di Windows (mempengaruhi aplikasi yang sedang memutar media, seperti Spotify, YouTube Music, Media Player, dll).

* **Miring ke Kanan:** Berpindah ke lagu berikutnya (*Next Track*).
* **Miring ke Kiri:** Kembali ke lagu sebelumnya (*Previous Track*).
* **Rotasi/Putar Smartphone:** Memutar atau menjeda media (*Play / Pause*).

Sistem dilengkapi dengan:

1. **Moving Average Filter:** Mengambil rata-rata dari 3 sampel data akselerometer terakhir untuk mencegah pembacaan data yang tidak stabil.
2. **Cooldown & Neutral Threshold:** Sistem akan menunggu gestur kembali ke titik netral (HP lurus) dan memberikan jeda 1 detik sebelum menerima perintah baru, sehingga mencegah pemicu perintah ganda.

## 🏗️ Arsitektur & Teknologi

* **Perangkat Sensor (Android):** Menggunakan sensor bawaan (*LSM6DSVTR Accelerometer* & *Gyroscope*) yang dibaca melalui Termux:API. Script Python membaca data melalui `subprocess` dan mengirimkannya via library `paho-mqtt`.
* **Perangkat Pemroses (Windows):** Menerima data JSON via MQTT, memprosesnya dengan *rule-based classification*, lalu mengeksekusi kontrol media menggunakan modul `ctypes` bawaan Windows (mensimulasikan `keybd_event`).
* **Komunikasi (MQTT):**
  * **Broker:** `broker.emqx.io` (Public Broker, Port 1883, tanpa TLS).
  * **Topik Sensor:** `syncdesk/<DEVICE_ID>/sensor` (Android ➔ Windows)
  * **Topik Status:** `syncdesk/<DEVICE_ID>/status` (Windows ➔ Android)

## ⚙️ Persyaratan Sistem

* **Android:** Aplikasi Termux dan Termux:API (disarankan diunduh dari F-Droid).
* **Windows:** Python 3.x terinstal.
* Koneksi internet pada kedua perangkat.

## 🚀 Cara Instalasi & Setup

### 1. Setup di Android (Termux)

1. Buka aplikasi **Termux:API** di HP Android Anda dan berikan izin akses ke sensor perangkat jika diminta.
2. Buka aplikasi **Termux**, lalu jalankan perintah berikut untuk menyiapkan *environment*:

   ```bash
   pkg update && pkg upgrade
   pkg install python termux-api nano
   pip install paho-mqtt
   ```

3. Buat file Python baru menggunakan editor `nano`:

   ```bash
   nano syncdesk_phone.py
   ```

4. *Paste* (tempelkan) kode script Android Anda ke dalam terminal.
5. Simpan file dengan menekan **CTRL + X**, lalu **Y**, kemudian **Enter**.

### 2. Setup di Laptop Windows

1. Buka Terminal / Command Prompt di folder proyek `SyncDesk-IoT`.
2. Instal dependensi library melalui `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

> **Catatan:** Modul `json`, `subprocess`, `time`, `collections`, dan `ctypes` adalah modul bawaan Python sehingga tidak perlu diinstal.

## 🏃‍♂️ Cara Penggunaan

1. **Jalankan Receiver di Windows**

   Buka terminal di laptop dan jalankan script:

   ```bash
   python syncdesk_laptop.py
   ```

   Tunggu hingga muncul pesan `Laptop terhubung ke MQTT!` dan `Menunggu gestur dari HP...`.

2. **Jalankan Transmitter di Android**

   Buka Termux di HP Anda dan jalankan script yang sudah dibuat tadi:

   ```bash
   python syncdesk_phone.py
   ```

   Terminal akan menampilkan nilai sensor `ax` dan `gz` secara real-time.

3. Atur DEVICE_ID

   Buka `syncdesk_laptop.py` dan `syncdesk_phone.py`, lalu ganti `ganti-dengan-id-anda` dengan ID acak milik Anda sendiri (huruf/angka, tanpa spasi). ID di kedua file **harus sama**.

4. **Lakukan Gestur**

   Pegang HP Anda, lalu:

   * Miringkan HP ke kanan untuk **Next Track**.
   * Miringkan HP ke kiri untuk **Previous Track**.
   * Putar/Rotasi HP untuk **Play / Pause**.

   Di terminal laptop akan muncul tulisan `Gestur terdeteksi: [NAMA_GESTUR]`, dan di HP akan muncul balasan dari laptop berupa `Balasan laptop: OK:[NAMA_GESTUR]`.

## ⚠️ Catatan Keamanan

Proyek ini menggunakan broker MQTT publik (`broker.emqx.io`), jadi semua pesan bisa dilihat siapa saja. Keamanan hanya bergantung pada `DEVICE_ID` yang sulit ditebak. Sebelum menjalankan, ganti `DEVICE_ID` di `syncdesk_laptop.py` dan `syncdesk_phone.py` dengan ID acak milik Anda sendiri (harus sama di kedua file), dan jangan commit ID asli ke repository publik. Jangan gunakan sistem ini untuk data pribadi atau rahasia.
