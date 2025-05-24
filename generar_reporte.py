# generar_reporte.py
import os
import json
from collections import defaultdict
from datetime import datetime

LOG_PATH = './data/logs.txt'
REPORTE_PATH = './data/reporte.txt'
ESTADO_PATH = './data/estado_nodos.json'

envios = defaultdict(int)
fallos = defaultdict(int)
recuperaciones = defaultdict(int)
otros = []

if not os.path.exists(LOG_PATH):
    print("No se encontró el archivo logs.txt")
    exit()

with open(LOG_PATH, 'r', encoding='utf-8') as f:
    for linea in f:
        if "enviada a" in linea:
            nodo = linea.split("enviada a")[1].strip()
            envios[nodo] += 1
        elif "FALLO conexión con" in linea or "Fallo en nodo" in linea:
            for nodo in ["nodo_mx", "nodo_co", "nodo_pe", "nodo_cl", "nodo_ar"]:
                if nodo in linea:
                    fallos[nodo] += 1
        elif "NODO RECUPERADO" in linea:
            nodo = linea.split(":")[-1].strip()
            recuperaciones[nodo] += 1
        else:
            otros.append(linea.strip())

with open(REPORTE_PATH, 'w', encoding='utf-8') as f:
    f.write("REPORTE DEL SISTEMA DISTRIBUIDO\n")
    f.write(f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    f.write("📦 IMÁGENES ENVIADAS POR NODO:\n")
    for nodo, count in envios.items():
        f.write(f" - {nodo}: {count} imágenes\n")

    f.write("\n❌ FALLOS DETECTADOS POR NODO:\n")
    for nodo, count in fallos.items():
        f.write(f" - {nodo}: {count} fallos\n")

    f.write("\n🔁 NODOS RECUPERADOS:\n")
    for nodo, count in recuperaciones.items():
        f.write(f" - {nodo}: {count} veces volvió a estar activo\n")

    f.write("\n📚 OTROS EVENTOS (últimos 10):\n")
    for linea in otros[-10:]:
        f.write(f" - {linea}\n")

    if os.path.exists(ESTADO_PATH):
        f.write("\n ESTADO ACTUAL DE LOS NODOS (estado_nodos.json):\n")
        with open(ESTADO_PATH, 'r', encoding='utf-8') as estado_file:
            estados = json.load(estado_file)
            for nodo, info in estados.items():
                activo = "ACTIVO" if info["activo"] else "INACTIVO"
                f.write(f" - {nodo}: {activo} (última actualización: {info['ultima_actualizacion']})\n")
    else:
        f.write("\n estado_nodos.json no encontrado.\n")

print(f"Reporte generado: {REPORTE_PATH}")
