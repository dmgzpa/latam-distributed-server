import json
import os

RR_INDEX_FILE = './data/rr_index.json'

def obtener_nodo_round_robin(activos):
    nodos = sorted(list(activos.keys()))
    if not nodos:
        return None

    # Asegura archivo
    if not os.path.exists(RR_INDEX_FILE):
        with open(RR_INDEX_FILE, 'w') as f:
            json.dump({"ultimo_usado": -1}, f)

    with open(RR_INDEX_FILE, 'r') as f:
        data = json.load(f)

    i = data.get("ultimo_usado", -1)
    siguiente = (i + 1) % len(nodos)
    seleccionado = nodos[siguiente]

    # Actualiza el índice
    with open(RR_INDEX_FILE, 'w') as f:
        json.dump({"ultimo_usado": siguiente}, f)

    return seleccionado

def obtener_nodo_mas_cercano(activos):
    from .monitor import NODOS
    import heapq
    import json

    with open('./config/rutas_nodos.json', 'r') as f:
        grafo = json.load(f)

    distancias = {nodo: float('inf') for nodo in grafo}
    distancias['cliente'] = 0
    cola = [(0, 'cliente')]

    while cola:
        distancia_actual, nodo_actual = heapq.heappop(cola)
        for vecino, peso in grafo.get(nodo_actual, {}).items():
            nueva_distancia = distancia_actual + peso
            if nueva_distancia < distancias[vecino]:
                distancias[vecino] = nueva_distancia
                heapq.heappush(cola, (nueva_distancia, vecino))

    disponibles = {nodo: distancias[nodo] for nodo in activos if nodo in distancias}
    if not disponibles:
        return None
    return min(disponibles, key=disponibles.get)

