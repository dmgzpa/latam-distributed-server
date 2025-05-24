# servidor/balanceador.py
from flask import Flask, request, jsonify
import requests
import os
import sys
import json
import datetime

# Asegura acceso a utils/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.monitor import nodos_activos, iniciar_heartbeat
from utils.algoritmo_distancia import obtener_nodo_round_robin, obtener_nodo_mas_cercano
from utils.monitor import nodos_activos, iniciar_heartbeat
iniciar_heartbeat()

app = Flask(__name__)
LOG_PATH = './data/logs.txt'

def registrar_log(evento, tipo="INFO"):
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        timestamp = datetime.datetime.now().isoformat()
        f.write(f"[{tipo}] {timestamp} - {evento}\n")

@app.route('/subir', methods=['POST'])
def subir():
    if 'imagen' not in request.files:
        registrar_log("Solicitud sin archivo 'imagen'", "WARN")
        return jsonify({"error": "No se recibió imagen"}), 400
    
    imagen = request.files['imagen']
    if imagen.filename == '':
        registrar_log("Nombre de archivo vacío recibido", "WARN")
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    intentos_fallidos = set()

    while True:
        activos = nodos_activos()
        disponibles = {n: url for n, url in activos.items() if n not in intentos_fallidos}

        print(f"Nodos activos detectados: {list(disponibles.keys())}")
        if not disponibles:
            registrar_log("No hay nodos disponibles tras intentos fallidos", "ERROR")
            return jsonify({"error": "No hay nodos disponibles"}), 503

        modo = obtener_modo_balanceo()
        if modo == "round_robin":
            nodo_seleccionado = obtener_nodo_round_robin(disponibles)
        else:
            nodo_seleccionado = obtener_nodo_mas_cercano(disponibles)

        if not nodo_seleccionado:
            registrar_log("No se pudo calcular nodo más cercano entre disponibles", "ERROR")
            return jsonify({"error": "Error al calcular nodo más cercano"}), 500

        url = disponibles[nodo_seleccionado]
        try:
            files = {'imagen': (imagen.filename, imagen.stream, imagen.mimetype)}
            respuesta = requests.post(f"{url}/subir", files=files, timeout=5)
            if respuesta.status_code == 200:
                registrar_log(f"Imagen '{imagen.filename}' enviada a {nodo_seleccionado}", "INFO")
                return respuesta.json(), 200
            else:
                registrar_log(f"Fallo en nodo {nodo_seleccionado} (status {respuesta.status_code})", "ERROR")
                intentos_fallidos.add(nodo_seleccionado)
        except requests.exceptions.RequestException as e:
            registrar_log(f"FALLO conexión con {nodo_seleccionado}: {str(e)}", "ERROR")
            intentos_fallidos.add(nodo_seleccionado)

def obtener_modo_balanceo():
        try:
            with open('./config/modo_balanceo.json', 'r') as f:
                config = json.load(f)
                return config.get("modo", "mas_cercano")
        except:
            return "mas_cercano"
        
if __name__ == '__main__':
    os.makedirs('./data', exist_ok=True)
    iniciar_heartbeat()
    app.run(host='0.0.0.0', port=8000)
