import paho.mqtt.client as mqtt
import json
import time

MQTT_BROKER = "public-mqtt-broker.bevywise.com"
MQTT_PORT = 1883
MQTT_TOPIC = "idwby/mac/cpu"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Подключение к брокеру успешно")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Ошибка подключения {rc}")

def on_message(client, userdata, message):

    try:
        data = json.loads(message.payload.decode())
        print("Данные получены")
        print(f"Данные CPU: {data.get('cpu_usage')}%")
        print(f"Температура: {data.get('cpu_temperature', 'N/A')}°C")
        print(f"Время: {time.ctime(data.get('timestamp'))}")

    except Exception as e:
        print(f"Ошибка обработки сообщения: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Топик: {MQTT_TOPIC}")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
