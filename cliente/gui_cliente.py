import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import requests
import os
import json
import subprocess
import platform

BALANCEADOR_URL = "http://<IP_SERVIDOR>:8000/subir"

class AppCliente:
    def __init__(self, root):
        self.root = root
        self.root.title("Cliente - Subida de Imágenes")
        self.root.geometry("820x600")

        self.ruta_descarga = "./cliente/descargas"
        os.makedirs(self.ruta_descarga, exist_ok=True)

        self.archivo_historial = "./cliente/historial_envios.txt"
        os.makedirs("./cliente", exist_ok=True)

        self.label = tk.Label(root, text="Selecciona una imagen (.png o .jpg)")
        self.label.pack(pady=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack()
        self.btn_cargar = tk.Button(btn_frame, text="Cargar imagen", command=self.cargar_imagen)
        self.btn_cargar.grid(row=0, column=0, padx=10)
        self.btn_subir = tk.Button(btn_frame, text="Subir imagen", command=self.subir_imagen, state=tk.DISABLED)
        self.btn_subir.grid(row=0, column=1, padx=10)
        self.btn_ver_nodo = tk.Button(btn_frame, text="Ver imágenes por nodo", command=self.abrir_ventana_nodos)
        self.btn_ver_nodo.grid(row=0, column=2, padx=10)
        self.btn_abrir_descargas = tk.Button(btn_frame, text="Abrir descargas", command=self.abrir_carpeta_descargas)
        self.btn_abrir_descargas.grid(row=0, column=3, padx=10)
        self.btn_generar_reporte = tk.Button(btn_frame, text="Generar reporte", command=self.generar_reporte)
        self.btn_generar_reporte.grid(row=0, column=4, padx=10)
        # Menú para seleccionar el modo de balanceo
        self.modo_var = tk.StringVar(value="round_robin")
        self.modo_menu = ttk.Combobox(btn_frame, textvariable=self.modo_var, values=["round_robin", "mas_cercano"], state="readonly", width=14)
        self.modo_menu.grid(row=0, column=5, padx=5)

        self.btn_guardar_modo = tk.Button(btn_frame, text="Guardar modo", command=self.guardar_modo_balanceo)
        self.btn_guardar_modo.grid(row=0, column=6, padx=5)


        self.mensaje = tk.Label(root, text="", fg="green")
        self.mensaje.pack(pady=10)

        self.tree = ttk.Treeview(root, columns=("nombre", "nodo", "estado"), show="headings")
        self.tree.heading("nombre", text="Imagen")
        self.tree.heading("nodo", text="Nodo destino")
        self.tree.heading("estado", text="Estado")
        self.tree.column("nombre", width=200)
        self.tree.column("nodo", width=150)
        self.tree.column("estado", width=100)
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        self.img_label = tk.Label(root)
        self.img_label.pack(pady=10)

        self.ruta_imagen = None
        self.imagen_tk = None

        self.cargar_historial()
        self.refrescar_historial()


    def cargar_imagen(self):
        archivo = filedialog.askopenfilename(
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg")]
        )
        if archivo:
            self.ruta_imagen = archivo
            self.mensaje.config(text=f"Imagen seleccionada: {os.path.basename(archivo)}", fg="blue")
            self.btn_subir.config(state=tk.NORMAL)
            self.mostrar_previsualizacion()

    def mostrar_previsualizacion(self):
        imagen = Image.open(self.ruta_imagen)
        imagen.thumbnail((200, 200))
        self.imagen_tk = ImageTk.PhotoImage(imagen)
        self.img_label.config(image=self.imagen_tk)

    def subir_imagen(self):
        if not self.ruta_imagen:
            return

        filename = os.path.basename(self.ruta_imagen)

        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            messagebox.showerror("Error", "Formato no válido. Solo se permiten .png, .jpg, .jpeg")
            return


        try:
            files = {'imagen': open(self.ruta_imagen, 'rb')}
            response = requests.post(BALANCEADOR_URL, files=files)
            files['imagen'].close()

            if response.status_code == 200:
                msg = response.json().get("mensaje", "")
                nodo = msg.split("nodo")[-1].strip()
                self.tree.insert("", tk.END, values=(filename, nodo, "✔ OK"))
                self.mensaje.config(text=msg, fg="green")
                self.guardar_en_historial(filename, nodo, "OK")
            else:
                error = response.json().get("error", "Error")
                self.tree.insert("", tk.END, values=(filename, "-", "❌ ERROR"))
                self.mensaje.config(text=error, fg="red")
                self.guardar_en_historial(filename, "-", "ERROR")
        except Exception as e:
            self.tree.insert("", tk.END, values=(filename, "-", "❌ CONEXIÓN"))
            self.mensaje.config(text=f"Error de conexión: {str(e)}", fg="red")
            self.guardar_en_historial(filename, "-", "CONEXIÓN")


    def guardar_en_historial(self, nombre, nodo, estado):
        with open(self.archivo_historial, 'a', encoding='utf-8') as f:
            f.write(f"{nombre} | {nodo} | {estado}\n")

    def cargar_historial(self):
        if not os.path.exists(self.archivo_historial):
            return

        # Para evitar duplicados en la tabla visual
        existentes = set()
        for fila in self.tree.get_children():
            existentes.add(self.tree.item(fila)["values"][0])  # nombre del archivo

        with open(self.archivo_historial, 'r', encoding='utf-8') as f:
            for linea in f:
                partes = [p.strip() for p in linea.strip().split("|")]
                if len(partes) == 3 and partes[0] not in existentes:
                    self.tree.insert("", tk.END, values=(partes[0], partes[1], partes[2]))

    def abrir_ventana_nodos(self):
        top = tk.Toplevel(self.root)
        top.title("Imágenes por Nodo")
        top.geometry("500x350")

        self.lista = tk.Listbox(top, width=60)
        self.lista.pack(pady=10, fill=tk.BOTH, expand=True)
        self.lista.bind('<Double-1>', self.descargar_seleccionada)

        self.archivo_historial = "./cliente/historial_envios.txt"
        self.ruta_descarga = "./cliente/descargas"
        os.makedirs("./cliente", exist_ok=True)
        os.makedirs(self.ruta_descarga, exist_ok=True)


        self.origenes = {}

        nodos = {
            "México": "http://localhost:5001",
            "Colombia": "http://localhost:5002",
            "Perú": "http://localhost:5003",
            "Chile": "http://localhost:5004",
            "Argentina": "http://localhost:5005"
        }

        for nombre, url in nodos.items():
            try:
                res = requests.get(f"{url}/imagenes", timeout=1)
                if res.status_code == 200:
                    archivos = res.json().get("imagenes", [])
                    if archivos:
                        self.lista.insert(tk.END, f"--- {nombre} ---")
                        for archivo in archivos:
                            entrada = f"{archivo} ({nombre})"
                            self.lista.insert(tk.END, entrada)
                            self.origenes[entrada] = (url, archivo)
                    else:
                        self.lista.insert(tk.END, f"{nombre}: (sin imágenes)")
                else:
                    self.lista.insert(tk.END, f"{nombre}: ❌ error al listar")
            except:
                self.lista.insert(tk.END, f"{nombre}: ❌ no disponible")

    def descargar_seleccionada(self, event):
        seleccion = self.lista.get(self.lista.curselection())
        if seleccion.startswith("---") or "❌" in seleccion or "(sin imágenes)" in seleccion:
            return

        url, filename = self.origenes.get(seleccion, (None, None))
        if not url:
            messagebox.showerror("Error", "No se pudo encontrar el nodo para descargar.")
            return

        try:
            res = requests.get(f"{url}/descargar/{filename}", stream=True)
            if res.status_code == 200:
                ruta_local = os.path.join(self.ruta_descarga, filename)
                with open(ruta_local, 'wb') as f:
                    for chunk in res.iter_content(1024):
                        f.write(chunk)
                messagebox.showinfo("Descarga completa", f"Imagen guardada en:\n{ruta_local}")
                self.mostrar_imagen_descargada(ruta_local)
            else:
                messagebox.showerror("Error", "No se pudo descargar la imagen.")
        except Exception:
            messagebox.showerror("Error", "Error de conexión al descargar la imagen.")

    def mostrar_imagen_descargada(self, ruta_local):
        try:
            top = tk.Toplevel(self.root)
            top.title(f"Vista previa - {os.path.basename(ruta_local)}")

            img = Image.open(ruta_local)
            img.thumbnail((300, 300))
            img_tk = ImageTk.PhotoImage(img)

            lbl = tk.Label(top, image=img_tk)
            lbl.image = img_tk
            lbl.pack(pady=10)
        except Exception:
            messagebox.showerror("Error", "No se pudo mostrar la imagen.")

    def abrir_carpeta_descargas(self):
        ruta = os.path.abspath(self.ruta_descarga)
        try:
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(ruta)
            elif sistema == "Darwin":
                subprocess.Popen(["open", ruta])
            else:
                subprocess.Popen(["xdg-open", ruta])
        except Exception:
            messagebox.showerror("Error", "No se pudo abrir la carpeta de descargas.")

    def generar_reporte(self):
        try:
            resultado = subprocess.run(["python", "generar_reporte.py"], capture_output=True, text=True)
            if resultado.returncode == 0:
                reporte_path = os.path.abspath("./data/reporte.txt")
                if os.path.exists(reporte_path):
                    self.mostrar_resumen_estado_nodos("./data/estado_nodos.json")
                    if platform.system() == "Windows":
                        os.startfile(reporte_path)
                    elif platform.system() == "Darwin":
                        subprocess.Popen(["open", reporte_path])
                    else:
                        subprocess.Popen(["xdg-open", reporte_path])
            else:
                messagebox.showerror("Error", f"No se pudo generar el reporte:\n{resultado.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al ejecutar el script:\n{str(e)}")

    def mostrar_resumen_estado_nodos(self, json_path):
        if not os.path.exists(json_path):
            messagebox.showinfo("Estado de Nodos", "No se encontró el archivo estado_nodos.json")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            estado = json.load(f)

        resumen = " Estado actual de los nodos:\n\n"
        for nodo, info in estado.items():
            status = "ACTIVO" if info["activo"] else " INACTIVO"
            resumen += f"{nodo}: {status}\nÚltima actualización: {info['ultima_actualizacion']}\n\n"

        messagebox.showinfo("Resumen del sistema", resumen)
        
    def guardar_modo_balanceo(self):
        modo = self.modo_var.get()
        try:
            os.makedirs("./config", exist_ok=True)
            with open("./config/modo_balanceo.json", "w", encoding="utf-8") as f:
                json.dump({"modo": modo}, f, indent=4)
            messagebox.showinfo("Modo de balanceo", f"Modo '{modo}' guardado exitosamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el modo: {str(e)}")

    def refrescar_historial(self):
        self.cargar_historial()
        self.root.after(5000, self.refrescar_historial)  # 5000 ms = 5 segundos
      
if __name__ == "__main__":
    root = tk.Tk()
    app = AppCliente(root)
    root.mainloop()
