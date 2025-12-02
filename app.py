from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
import json
import threading
import time

app = Flask(__name__)

cpu_data = {
    'temperature': 35.0,
    'usage': 10.0,
    'memory': 50.0,
    'timestamp': time.time()
}

MQTT_BROKER = "public-mqtt-broker.bevywise.com"
MQTT_PORT = 1883
MQTT_TOPIC = "idwby/mac/cpu"
# MQTT_TOPIC = "idwby/linux/cpu" -- для linux

def on_connect(client, userdata, flags, rc, properties=None):  
    print(f"MQTT подключен: {rc}")
    client.subscribe(MQTT_TOPIC)
    print(f"Подписались на топик: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        
        cpu_data['temperature'] = data.get('cpu_temperature', 35.0)
        cpu_data['usage'] = data.get('cpu_usage', 10.0)
        cpu_data['memory'] = data.get('memory_usage', 50.0)
        cpu_data['timestamp'] = data.get('timestamp', time.time())
        
        print(f"Получены данные: CPU {cpu_data['usage']}% | Temp {cpu_data['temperature']}°C")
    except Exception as e:
        print(f"Ошибка обработки MQTT: {e}")

def start_mqtt():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_connect = on_connect
        client.on_message = on_message
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"Подключаемся к MQTT брокеру {MQTT_BROKER}:{MQTT_PORT}")
        client.loop_forever()
    except Exception as e:
        print(f"Ошибка MQTT: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    return jsonify(cpu_data)

if __name__ == '__main__':
    # Запускаем MQTT клиент в отдельном потоке
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()

    print("\n" + "="*50)
    print("Запускаем веб-сервер мониторинга CPU")
    print("="*50)
    print("\nОткройте в браузере:")
    print("   http://localhost:8080")
    print("   или http://127.0.0.1:8080")
    print("\nОжидаем данные от MQTT брокера")
    print("="*50 + "\n")
    
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8080)