from flask import Flask, jsonify, redirect, abort, send_file, request
import mysql.connector
import jwt
import bcrypt
import os
import datetime
import mimetypes
from functools import wraps
from flask_cors import CORS
import paypalrestsdk

SECRET_KEY = "DevourStar"  # cámbialo por algo seguro
app = Flask(__name__)
CORS(app)  # 👈 Esto habilita CORS para todos los orígenes y rutas


# Configuración de PayPal
paypalrestsdk.configure({
    "mode": "sandbox",  # usa "live" en producción
    "client_id": "AdW7jg4-Y8O_baFv82Y3n7y4qyaUupkYFUzTi1NLylUxQs1ow3Ftm_2vUQnFutk-ts5Ro1JMRVPeD0vh",
    "client_secret": "EA1NHZAAd_UJvMBugrEnBhmhm24nerylxZbkaJVSS3EyRerEIg7Uh2WvenIz1Iz7H5b2c8QEd5BRXFA-"
})


# Función auxiliar para abrir conexión (recomendado hacerlo por petición)
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345678",
        database="tracking"
    )


# ------------------------
# Middleware para verificar token
# ------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Buscar token en header Authorization
        if "Authorization" in request.headers:
            try:
                token = request.headers["Authorization"].split(" ")[1]  # "Bearer <token>"
            except IndexError:
                return jsonify({"error": "Formato de token inválido"}), 401

        if not token:
            return jsonify({"error": "Token requerido"}), 401

        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_data = decoded   # Guardamos datos decodificados en request
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401

        return f(*args, **kwargs)
    return decorated

# ------------------------
# RUTAS DE AUTENTICACIÓN
# ------------------------




# Registro de usuario
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Faltan campos"}), 400

    # Hash de la contraseña
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    db = get_db_connection()
    cursor = db.cursor()

    # Verificar si ya existe el usuario
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        cursor.close()
        db.close()
        return jsonify({"error": "Usuario ya existe"}), 400

    # Insertar nuevo usuario
    cursor.execute(
        "INSERT INTO users (username, password_user) VALUES (%s, %s)",
        (username, hashed.decode('utf-8'))
    )
    db.commit()
    cursor.close()
    db.close()

    return jsonify({"message": "Usuario registrado con éxito"}), 201

# ------------------------
# LOGIN con JWT
# ------------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user["password_user"].encode('utf-8')):
        # Crear token JWT válido por 1 hora
        payload = {
            "user_id": user["id"],
            "username": user["username"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify({"token": token})
    
    else:
        return jsonify({"error": "Credenciales inválidas"}), 401
    

# ------------------------
# RUTA: verificar login (autosuficiente)
# ------------------------
@app.route('/verify-login', methods=['GET'])
@token_required
def verify_login():
    return jsonify({
        "valid": True,
        "data": request.user_data
    })

# GET: obtener todos los registros de parking_lot
@app.route('/parkings', methods=['GET'])
def get_parkings():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM parking_lot")
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)


@app.route("/imagen/<int:id>")
def obtener_imagen(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Buscar ruta de la imagen en la tabla
    cursor.execute("SELECT file_image FROM parking_lot WHERE id = %s", (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return abort(404, "Imagen no encontrada en la base de datos")

    file_path = row["file_image"]

    print(file_path)

    file_path = "./images/" + file_path

    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        return abort(404, "Archivo no encontrado en disco")

    # Detectar automáticamente el mimetype (png, jpg, gif, etc.)
    mime_type, _ = mimetypes.guess_type(file_path)

    return send_file(file_path, mimetype=mime_type)


# PUT: actualizar la cantidad disponible de un parking por id
@app.route('/parkings/<int:id>/available', methods=['PUT'])
def update_available(id):
    data = request.json
    new_available = data.get("available")

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE parking_lot SET available = %s WHERE id = %s", (new_available, id))
    db.commit()
    cursor.close()
    db.close()

    return jsonify({"message": f"Disponibilidad actualizada a {new_available} para parking ID {id}"})


# PUT: actualizar el contador de un parking por id
@app.route('/parkings/<int:id>/counter', methods=['PUT'])
def update_counter(id):
    data = request.json
    new_counter = data.get("counter")

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE parking_lot SET counter = %s WHERE id = %s", (new_counter, id))
    db.commit()
    cursor.close()
    db.close()

    return jsonify({"message": f"Contador actualizado a {new_counter} para parking ID {id}"})


""" PAGAR """

@app.route("/pagar/<int:id>/<int:user>")
def pagar(id, user):
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": f"http://localhost:5000/reservar/{user}/{id}",
            "cancel_url": "http://localhost:5173/"
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": f"PARQUEO",
                    "sku": str(id),
                    "price": "10.00",
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": "10.00",
                "currency": "USD"
            },
            "description": f"Pago por el servicio con ID {id}"
        }]
    })

    if payment.create():
        # Redirige a PayPal para que el usuario pague
        for link in payment.links:
            if link.method == "REDIRECT":
                return redirect(link.href)
    else:
        return jsonify({"error": payment.error})


# Endpoint para obtener reservas por usuario
@app.route("/mis_reservas/<int:id_user>", methods=["GET"])
def mis_reservas(id_user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM reservations WHERE id_user = %s ORDER BY id DESC",
        (id_user,)
    )
    reservas = cursor.fetchall()
    conn.close()

    return jsonify(reservas)


# Endpoint GET para crear una reserva
@app.route("/reservar/<int:id_user>/<int:id_parking>", methods=["GET"])
def reservar(id_user, id_parking):
    if not id_user or not id_parking:
        return jsonify({"error": "Faltan parámetros"}), 400

    try:
        id_user = int(id_user)
        id_parking = int(id_parking)
    except ValueError:
        return jsonify({"error": "id_user e id_parking deben ser números"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insertar solo id_user, id_parking; entrance y exit_date pueden quedar NULL
    cursor.execute(
        "INSERT INTO reservations (id_user, id_parking) VALUES (%s, %s)",
        (id_user, id_parking)
    )
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()

    return redirect("http://localhost:5173")

# Registrar hora de entrada
@app.route("/reservas/entrada/<int:reservation_id>", methods=["GET"])
def registrar_entrada(reservation_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "UPDATE reservations SET entrance = %s WHERE id = %s",
        (now, reservation_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": f"Hora de entrada registrada para reserva {reservation_id}", "entrance": now})

# Registrar hora de salida
@app.route("/reservas/salida/<int:reservation_id>", methods=["GET"])
def registrar_salida(reservation_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "UPDATE reservations SET exit_date = %s WHERE id = %s",
        (now, reservation_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": f"Hora de salida registrada para reserva {reservation_id}", "exit_date": now})


if __name__ == "__main__":
    app.run(debug=True)
