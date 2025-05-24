# utils/monitor.py
import threading
import time
import requests
from datetime import datetime
import json
import os

NODOS = {
    "nodo_mx": "http://localhost:5001",
    "nodo_co": "http://localhost:5002",
    "nodo_pe": "http://localhost:5003",
    "nodo_cl": "http://localhost:5004",
    "nodo_ar": "http://localhost:5005"
}

estado_actual = {}
json_path = './data/estado_nodos.json'
log_path = './data/logs.txt'

def registrar_log(evento, tipo="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"[{tipo}] {timestamp} - {evento}\n")

def actualizar_json_estado():
    estado_resumen = {}
    for nodo, activo in estado_actual.items():
        estado_resumen[nodo] = {
            "activo": activo,
            "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(estado_resumen, f, indent=4)

def ping_nodos():
    while True:
        for nombre, url in NODOS.items():
            try:
                res = requests.get(f"{url}/status", timeout=2)
                if res.status_code == 200:
                    if estado_actual.get(nombre) is False:
                        registrar_log(f"NODO RECUPERADO: {nombre}", "INFO")
                    estado_actual[nombre] = True
                else:
                    if estado_actual.get(nombre) is not False:
                        registrar_log(f"NODO INACTIVO (status error): {nombre}", "ERROR")
                    estado_actual[nombre] = False
            except:
                if estado_actual.get(nombre) is not False:
                    registrar_log(f"NODO INACTIVO (sin respuesta): {nombre}", "ERROR")
                estado_actual[nombre] = False
        actualizar_json_estado()
        time.sleep(4)

def iniciar_heartbeat():
    os.makedirs('./data', exist_ok=True)
    hilo = threading.Thread(target=ping_nodos, daemon=True)
    hilo.start()

def nodos_activos():
    return {n: url for n, url in NODOS.items() if estado_actual.get(n)}
