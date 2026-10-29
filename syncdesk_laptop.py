
import json
import time
import ctypes
import paho.mqtt.client as mqtt

# Konfigurasi MQTT
DEVICE_ID = "ganti-dengan-id-anda"  # Masukkan ID device Anda (harus sama di laptop dan HP)
if DEVICE_ID.strip() in ("", "ganti-dengan-id-anda"):
    raise SystemExit("Isi DEVICE_ID dulu di bagian atas script.")
BROKER = "broker.emqx.io"
PORT = 1883

SENSOR_TOPIC = f"syncdesk/{DEVICE_ID}/sensor"
STATUS_TOPIC = f"syncdesk/{DEVICE_ID}/status"

# Tombol media Windows
VK_NEXT = 0xB0
VK_PREVIOUS = 0xB1
VK_PLAY_PAUSE = 0xB3
KEYUP = 0x0002

# Ambang awal sensor
TILT_THRESHOLD = 5.0
ROTATION_THRESHOLD = 1.8
NEUTRAL_THRESHOLD = 3.0
GYRO_NEUTRAL = 0.7
COOLDOWN = 1.0

armed = True
last_command = 0.0
ax_history = []


def media_key(key):
    user32 = ctypes.windll.user32
    user32.keybd_event(key, 0, 0, 0)
    user32.keybd_event(key, 0, KEYUP, 0)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print("Koneksi MQTT gagal:", reason_code)
        return

    client.subscribe(SENSOR_TOPIC)
    print("Laptop terhubung ke MQTT!")
    print("Menunggu gestur dari HP...")


def on_message(client, userdata, msg):
    global armed, last_command, ax_history

    try:
        data = json.loads(msg.payload.decode("utf-8"))
        ax = float(data["ax"])
        gz = float(data["gz"])
    except (ValueError, KeyError, TypeError):
        print("Data sensor tidak valid.")
        return

    # Pemrosesan 1: moving average 3 sampel.
    ax_history.append(ax)
    if len(ax_history) > 3:
        ax_history.pop(0)

    filtered_ax = sum(ax_history) / len(ax_history)
    now = time.monotonic()

    # Gestur baru hanya boleh setelah kembali netral.
    if (
        abs(filtered_ax) < NEUTRAL_THRESHOLD
        and abs(gz) < GYRO_NEUTRAL
    ):
        armed = True

    if not armed or now - last_command < COOLDOWN:
        return

    # Pemrosesan 2: klasifikasi gestur berbasis aturan.
    if abs(gz) > ROTATION_THRESHOLD:
        command = VK_PLAY_PAUSE
        label = "PLAY_PAUSE"
    elif filtered_ax > TILT_THRESHOLD:
        command = VK_NEXT
        label = "NEXT_TRACK"
    elif filtered_ax < -TILT_THRESHOLD:
        command = VK_PREVIOUS
        label = "PREVIOUS_TRACK"
    else:
        return

    try:
        media_key(command)
        status = f"OK:{label}"
        client.publish(STATUS_TOPIC, status)
        print(f"Gestur terdeteksi: {label}")
    except Exception as error:
        print("Gagal mengirim tombol media:", error)

    armed = False
    last_command = now


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id=f"syncdesk-laptop-{DEVICE_ID}"
)
client.on_connect = on_connect
client.on_message = on_message

print("Menghubungkan laptop ke broker...")
client.connect(BROKER, PORT, 60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nSyncDesk dihentikan.")
finally:
    client.disconnect()
