import cv2
import json
import numpy as np
from ultralytics import YOLO
import mysql.connector
import sys
import requests

def changeAvailable(parking_id, available):
    try:
        url = f'http://127.0.0.1:5000/parkings/{parking_id}/available'
        myobj = {'available': available}
        x = requests.put(url, json = myobj)
        #print(x.text)
    except:
        None

def changeCounter(parking_id, counter):
    try:
         url = f'http://127.0.0.1:5000/parkings/{parking_id}/counter'
         myobj = {'counter': counter}
         x = requests.put(url, json = myobj)
         #print(x.text)
    except:
        None


def run_camera(parking_id):
    # Conexión a la BD
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345678",
        database="tracking"
    )
    cursor = db.cursor(dictionary=True)

    # Obtener datos del parking seleccionado
    cursor.execute("SELECT * FROM parking_lot WHERE id = %s", (parking_id,))
    parking = cursor.fetchone()
    cursor.close()
    db.close()

    if not parking:
        print(f"❌ Parking con id {parking_id} no encontrado.")
        return

    print(f"▶ Iniciando cámara para parking: {parking['name_parking']}")

    # Cargar zonas desde JSON
    with open("./json/" + parking["file_json"], "r") as f:
        zonas = json.load(f)

    zonas_poligonos = [np.array(zona["puntos"], dtype=np.int32) for zona in zonas]
    total_parqueos = len(zonas)


    changeCounter(parking_id, total_parqueos)

    # Cargar modelo YOLOv8
    model = YOLO("yolov8n.pt")

    # Abrir video del parking
    cap = cv2.VideoCapture("./videos/" + parking["file_video"])

    ocupados_anterior = None
    disponibles_anterior = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        ocupados_actual = 0

        # Dibujar zonas
        for puntos in zonas_poligonos:
            cv2.polylines(frame, [puntos], True, (255, 0, 0), 2)

        # Detección de autos
        results = model(frame, verbose=False)
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                if model.names[cls] == "car":
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    for puntos in zonas_poligonos:
                        if cv2.pointPolygonTest(puntos, (cx, cy), False) >= 0:
                            ocupados_actual += 1
                            break

        # Calcular disponibles
        disponibles_actual = total_parqueos - ocupados_actual

        # Inicializar en la API al arrancar la cámara (solo la primera vez)
        if ocupados_anterior is None:
            changeAvailable(parking_id, disponibles_actual)

        # Mostrar en pantalla
        cv2.putText(frame, f"Ocupados: {ocupados_actual}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (140, 7, 16), 2)
        cv2.putText(frame, f"Disponibles: {disponibles_actual}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (7, 140, 16), 2)

        # Comparar con valores anteriores
        if ocupados_anterior is not None:
            if ocupados_actual != ocupados_anterior:
                #print(f"[CAMBIO] Ocupados: {ocupados_anterior} → {ocupados_actual}")
                changeAvailable(parking_id, disponibles_actual)
            if disponibles_actual != disponibles_anterior:
                changeAvailable(parking_id, disponibles_actual)
                #print(f"[CAMBIO] Disponibles: {disponibles_anterior} → {disponibles_actual}")

        ocupados_anterior = ocupados_actual
        disponibles_anterior = disponibles_actual

        # Mostrar ventana
        cv2.namedWindow("Camera: " + str(parking_id), cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Camera: " + str(parking_id), 800, 450)
        cv2.imshow("Camera: " + str(parking_id), frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# Si se ejecuta directo desde terminal
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Debes pasar el ID del parking como argumento. Ejemplo: python camera.py 1")
    else:
        run_camera(int(sys.argv[1]))
