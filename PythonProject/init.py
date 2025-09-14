import mysql.connector
import os
import shutil
import subprocess


python_cmd = shutil.which("py") or shutil.which("py") or shutil.which("python3")
if not python_cmd:
    raise Exception("No se encontró Python en el PATH")

# Conexión a la BD
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345678",
    database="tracking"
)
cursor = db.cursor(dictionary=True)

# Mostrar lista de parkings
cursor.execute("SELECT id, name_parking FROM parking_lot")
parkings = cursor.fetchall()
cursor.close()
db.close()

def selectCamera():
    print("=== Lista de parkings disponibles ===")
    for p in parkings:
        print(f"[{p['id']}] {p['name_parking']}")
    # Pedir selección
    parking_id = int(input("\nSeleccione el ID del parking a iniciar: "))
    # Ejecutar camera.py con ese ID
    #os.system(f"py camera.py {parking_id}")
    subprocess.Popen([python_cmd, "camera.py", str(parking_id)])

def callMenu():
    print("0: Cerrar Programa")
    print("1: Iniciar Parqueo")
    print("2: Agregar Parqueo")

while(True):
    callMenu()
    opcion = input();
    if opcion == "0":
        break
    if opcion == "1":
        selectCamera()
    if opcion == "2":
        subprocess.Popen([python_cmd, "add_parking.py"])
