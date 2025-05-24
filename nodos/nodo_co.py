from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__)

NOMBRE_NODO = "Colombia"
CARPETA_IMAGENES = os.path.abspath("./imagenes_co")
os.makedirs(CARPETA_IMAGENES, exist_ok=True)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"estado": "activo", "nodo": NOMBRE_NODO}), 200

@app.route('/subir', methods=['POST'])
def subir_imagen():
    if 'imagen' not in request.files:
        return jsonify({"error": "No se recibió archivo"}), 400
    imagen = request.files['imagen']
    if imagen.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400
    ruta = os.path.join(CARPETA_IMAGENES, imagen.filename)
    imagen.save(ruta)
    return jsonify({"mensaje": f"Imagen almacenada en nodo {NOMBRE_NODO}"}), 200

@app.route('/imagenes', methods=['GET'])
def listar_imagenes():
    if not os.path.exists(CARPETA_IMAGENES):
        return jsonify({"imagenes": [], "mensaje": "Carpeta no existe"}), 200
    archivos = os.listdir(CARPETA_IMAGENES)
    return jsonify({"imagenes": archivos}), 200

@app.route('/descargar/<filename>', methods=['GET'])
def descargar_imagen(filename):
    try:
        return send_from_directory(CARPETA_IMAGENES, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "Archivo no encontrado"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
