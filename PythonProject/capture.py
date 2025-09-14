import cv2
import json
import numpy as np


# Ruta de imagen del parqueo
image_path = "2.png"
image = cv2.imread(image_path)
clone = image.copy()

zonas = []  # Lista de zonas (cada zona = lista de puntos)
zona_actual = []

def click_event(event, x, y, flags, param):
    global zona_actual, image

    if event == cv2.EVENT_LBUTTONDOWN:
        zona_actual.append((x, y))
        cv2.circle(image, (x, y), 5, (0, 0, 255), -1)
        if len(zona_actual) > 1:
            cv2.line(image, zona_actual[-2], zona_actual[-1], (0, 255, 0), 2)

# Crear ventana
cv2.namedWindow("Definir Zonas", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Definir Zonas", click_event)



while True:
    cv2.resizeWindow("Definir Zonas", 800, 450)  # Ancho x Alto
    cv2.imshow("Definir Zonas", image)
    key = cv2.waitKey(1) & 0xFF

    if key == 13:  # Enter -> Guardar zona actual
        if len(zona_actual) >= 3:  # Un polígono necesita mínimo 3 puntos
            zonas.append(zona_actual.copy())
            print(f"Zona guardada: {zona_actual}")
        zona_actual.clear()
        image = clone.copy()
        # Redibujar zonas guardadas
        for z in zonas:
            pts = cv2.polylines(clone.copy(), [np.array(z, np.int32)], True, (255, 0, 0), 2)
        image = clone.copy()
        for z in zonas:
            cv2.polylines(image, [np.array(z, np.int32)], True, (255, 0, 0), 2)

    elif key == 27:  # ESC -> Salir
        break

cv2.destroyAllWindows()

# Guardar zonas en JSON
with open("zonas.json", "w") as f:
    json.dump(zonas, f)

print("Zonas guardadas en zonas.json")
