import cv2
import json
import numpy as np
import mysql.connector
import os
from tkinter import Tk, filedialog

# --- Funciones auxiliares ---
def select_file(title, filetypes):
    Tk().withdraw()  # Ocultar ventana principal
    return filedialog.askopenfilename(title=title, filetypes=filetypes)

def move_file(src, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    dest_path = os.path.join(dest_folder, os.path.basename(src))
    os.replace(src, dest_path)
    return dest_path

# --- Conectar a MySQL ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345678",
        database="tracking"
    )

# --- Pedir datos del nuevo parking ---
name_parking = input("Nombre del parking: ")

# Selección de video
video_path = select_file("Seleccionar video del parking", [("Video Files", "*.mp4 *.avi *.mov")])
video_path_dest = move_file(video_path, "./videos")

# Captura del primer frame como imagen
cap = cv2.VideoCapture(video_path_dest)
ret, frame = cap.read()
if not ret:
    raise Exception("No se pudo leer el video")
image_path_dest = "./images"
os.makedirs(image_path_dest, exist_ok=True)
image_filename = os.path.join(image_path_dest, os.path.splitext(os.path.basename(video_path_dest))[0] + ".png")
cv2.imwrite(image_filename, frame)
cap.release()
print(f"Imagen generada: {image_filename}")

# --- Definir zonas ---
zonas = []
clone = frame.copy()
zona_actual = []

def click_event(event, x, y, flags, param):
    global zona_actual, clone
    if event == cv2.EVENT_LBUTTONDOWN:
        zona_actual.append([x, y])
        cv2.circle(clone, (x, y), 5, (0, 0, 255), -1)
        if len(zona_actual) > 1:
            cv2.line(clone, tuple(zona_actual[-2]), tuple(zona_actual[-1]), (0, 255, 0), 2)

cv2.namedWindow("Definir Zonas", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Definir Zonas", click_event)

while True:
    cv2.imshow("Definir Zonas", clone)
    key = cv2.waitKey(1) & 0xFF
    if key == 13:  # Enter -> guardar zona
        if len(zona_actual) >= 3:
            nombre_zona = input("Nombre de la zona: ")
            zonas.append({
                "nombre": nombre_zona,
                "puntos": zona_actual.copy()
            })
            print(f"Zona guardada: {nombre_zona} -> {zona_actual}")
        zona_actual.clear()
        clone = frame.copy()
        for z in zonas:
            cv2.polylines(clone, [np.array(z["puntos"], np.int32)], True, (255, 0, 0), 2)
    elif key == 27:  # ESC -> salir
        break

cv2.destroyAllWindows()

# Guardar JSON
json_folder = "./json"
os.makedirs(json_folder, exist_ok=True)
json_filename = os.path.join(json_folder, os.path.splitext(os.path.basename(video_path_dest))[0] + ".json")
with open(json_filename, "w") as f:
    json.dump(zonas, f, indent=2)
print(f"JSON guardado: {json_filename}")

# --- Insertar en DB ---
latitud = input("Latitud: ")
longitud = input("Longitud: ")

db = get_db_connection()
cursor = db.cursor()
cursor.execute("""
    INSERT INTO parking_lot (name_parking, file_video, file_json, file_image, latitud, longitud)
    VALUES (%s, %s, %s, %s, %s, %s)
""", (name_parking, os.path.basename(video_path_dest), os.path.basename(json_filename), os.path.basename(image_filename), latitud, longitud))
db.commit()
cursor.close()
db.close()

print("✅ Parking agregado correctamente!")