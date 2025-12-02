import psutil
import paho.mqtt.client as mqtt
import time
import json
import os
import re
import subprocess

MQTT_BROKER = "public-mqtt-broker.bevywise.com"
MQTT_PORT = 1883
MQTT_TOPIC = "idwby/linux/cpu"  

def get_cpu_temperature_linux():
    methods = [
        lambda: get_temp_from_sys(),
        lambda: get_temp_from_sensors(),
        lambda: get_temp_from_thermal_zone(),
        lambda: estimate_temp_from_usage()
    ]
    
    for method in methods:
        try:
            temp = method()
            if temp is not None and 20 <= temp <= 120:  
                return temp
        except:
            continue
    
    return estimate_temp_from_usage()

def get_temp_from_sys():
    # Читаем температуру из /sys/class/thermal
    try:
        thermal_zones = [f for f in os.listdir('/sys/class/thermal/') 
                        if f.startswith('thermal_zone')]
        
        for zone in thermal_zones:
            type_path = f'/sys/class/thermal/{zone}/type'
            temp_path = f'/sys/class/thermal/{zone}/temp'
            
            if os.path.exists(type_path) and os.path.exists(temp_path):
                with open(type_path, 'r') as f:
                    zone_type = f.read().strip()
                
                if 'cpu' in zone_type.lower() or 'core' in zone_type.lower():
                    with open(temp_path, 'r') as f:
                        temp = int(f.read().strip())
                    return temp / 1000.0  
    except:
        pass
    return None

def get_temp_from_sensors():
    # Используем команду sensors (требует lm-sensors)
    try:
        result = subprocess.run(['sensors'], 
                              capture_output=True, text=True, timeout=2)
        
        lines = result.stdout.split('\n')
        for line in lines:
            if 'core' in line.lower() or 'cpu' in line.lower():
                matches = re.findall(r'([+-]?\d+\.\d+)°C', line)
                if matches:
                    return float(matches[0])
    except:
        pass
    return None

def get_temp_from_thermal_zone():
    # Альтернативный метод через thermal_zone
    try:
        for i in range(0, 10):
            temp_file = f'/sys/class/thermal/thermal_zone{i}/temp'
            if os.path.exists(temp_file):
                with open(temp_file, 'r') as f:
                    temp = int(f.read().strip())
                return temp / 1000.0
    except:
        pass
    return None

def estimate_temp_from_usage():
    # Оценочная температура на основе загрузки CPU
    cpu_usage = psutil.cpu_percent(interval=1)
    base_temp = 35.0  
    additional_heat = cpu_usage * 0.25 
    return base_temp + additional_heat

def get_cpu_frequency():
    # Получаем текущую частоту CPU
    try:
        freq = psutil.cpu_freq()
        if freq and freq.current:
            return freq.current
    except:
        pass
    return None

def get_cpu_cores_usage():
    # Получаем загрузку по каждому ядру
    try:
        return psutil.cpu_percent(interval=0.5, percpu=True)
    except:
        return []

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Успешно подключились к MQTT брокеру")
        print(f"Топик: {MQTT_TOPIC}")
    else:
        print(f"Ошибка подключения: {rc}")

client.on_connect = on_connect

try:
    print(f"Подключаемся к MQTT брокеру {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    print("Отправка данных с Linux системы")
    print("Нажмите Ctrl+C для остановки\n")
    print("=" * 50)

    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_temp = get_cpu_temperature_linux()
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        cpu_freq = get_cpu_frequency()
        cores_usage = get_cpu_cores_usage()
        
        message = {
            "cpu_usage": cpu_usage,
            "cpu_temperature": round(cpu_temp, 1),
            "memory_usage": round(memory_info.percent, 1),
            "disk_usage": round((disk_info.used / disk_info.total) * 100, 1),
            "cpu_frequency": round(cpu_freq, 1) if cpu_freq else 0,
            "cpu_cores": len(cores_usage) if cores_usage else psutil.cpu_count(),
            "timestamp": time.time(),
            "system": "linux",
            "unit": "celsius"
        }
        
        if cores_usage:
            message["cores_usage"] = [round(c, 1) for c in cores_usage]
        
        client.publish(MQTT_TOPIC, json.dumps(message))
        
        print(f"CPU: {cpu_usage:5.1f}% | "
              f"Temp: {cpu_temp:5.1f}°C | "
              f"Memory: {memory_info.percent:5.1f}% | "
              f"Disk: {(disk_info.used/disk_info.total*100):5.1f}%")
        
        if cpu_freq:
            print(f"   Frequency: {cpu_freq:.0f} MHz | "
                  f"Cores: {psutil.cpu_count()}")
        
        time.sleep(5)

except KeyboardInterrupt:
    print("\n\nПрограмма остановлена пользователем")
    client.loop_stop()
    client.disconnect()
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()