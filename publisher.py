import psutil
import paho.mqtt.client as mqtt
import time
import json

MQTT_BROKER = "public-mqtt-broker.bevywise.com"
MQTT_PORT = 1883
MQTT_TOPIC = "idwby/mac/cpu"

def get_cpu_temperature():
    cpu_usage = psutil.cpu_percent(interval=1)
    base_temperature = 35  
    additional_heat = cpu_usage * 0.3 
    estimated_temperature = base_temperature + additional_heat
    return round(estimated_temperature, 1)

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Успешно подключились к MQTT брокеру")
    else:
        print(f"Ошибка подключения: {rc}")

client.on_connect = on_connect

try:
    print(f"Подключаемся к {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    print("Отправка данных на MQTT брокер...")
    print("Нажмите Ctrl+C для остановки\n")

    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_temperature = get_cpu_temperature()
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        message = {
            "cpu_usage": cpu_usage,
            "cpu_temperature": cpu_temperature,
            "memory_usage": memory_info.percent,
            "disk_usage": round((disk_info.used / disk_info.total) * 100, 1),
            "timestamp": time.time(),
            "unit": "celsius"
        }
        
        client.publish(MQTT_TOPIC, json.dumps(message))
        
        print(f"Отправлено: Температура: {cpu_temperature}°C | CPU: {cpu_usage}% | Память: {memory_info.percent}%")

        time.sleep(5)

except KeyboardInterrupt:
    print("\n\nПрограмма остановлена пользователем")
    client.loop_stop()
    client.disconnect()
except Exception as e:
    print(f"Ошибка: {e}")