
import json
import subprocess
import time
import paho.mqtt.client as mqtt

DEVICE_ID = "ganti-dengan-id-anda"  # Masukkan ID device Anda (harus sama di laptop dan HP)
if DEVICE_ID.strip() in ("", "ganti-dengan-id-anda"):
    raise SystemExit("Isi DEVICE_ID dulu di bagian atas script.")
BROKER = "broker.emqx.io"
PORT = 1883

SENSOR_TOPIC = f"syncdesk/{DEVICE_ID}/sensor"
STATUS_TOPIC = f"syncdesk/{DEVICE_ID}/status"

ACCEL = "LSM6DSVTR Accelerometer"
GYRO = "LSM6DSVTR Gyroscope"


def read_sensor(name):
    result = subprocess.run(
        ["termux-sensor", "-s", name, "-d", "250", "-n", "1"],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Sensor gagal dibaca")

    data = json.loads(result.stdout)
    sensor = data.get(name)

    if not isinstance(sensor, dict):
        raise ValueError(f"Sensor tidak ditemukan: {name}")

    values = sensor.get("values", [])
    if len(values) < 3:
        raise ValueError(f"Data tidak lengkap: {name}")

    return [float(value) for value in values[:3]]


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print("Koneksi MQTT gagal:", reason_code)
        return

    client.subscribe(STATUS_TOPIC)
    print("HP terhubung ke MQTT!")


def on_message(client, userdata, msg):
    print("Balasan laptop:", msg.payload.decode("utf-8"))


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id=f"syncdesk-phone-{DEVICE_ID}"
)
client.on_connect = on_connect
client.on_message = on_message

try:
    print("Menghubungkan HP ke MQTT...")
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    deadline = time.monotonic() + 10
    while not client.is_connected() and time.monotonic() < deadline:
        time.sleep(0.2)

    if not client.is_connected():
        raise RuntimeError("MQTT belum terhubung.")

    print("Mulai membaca kedua sensor...")

    while True:
        try:
            accel = read_sensor(ACCEL)
            gyro = read_sensor(GYRO)

            payload = {
                "ax": accel[0],
                "ay": accel[1],
                "az": accel[2],
                "gx": gyro[0],
                "gy": gyro[1],
                "gz": gyro[2]
            }

            client.publish(
                SENSOR_TOPIC,
                json.dumps(payload),
                qos=0
            )

            print(
                f"ax={payload['ax']:.2f}, "
                f"gz={payload['gz']:.2f}"
            )

        except (
            ValueError,
            RuntimeError,
            subprocess.TimeoutExpired,
            json.JSONDecodeError
        ) as error:
            print("Pembacaan sensor gagal:", error)

        time.sleep(0.3)

except KeyboardInterrupt:
    print("\nProgram HP dihentikan.")
except Exception as error:
    print("Error:", error)
finally:
    client.loop_stop()
    client.disconnect()
