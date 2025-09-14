import { useEffect, useRef, useState } from "react";
//import './App.css'
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";

import "leaflet/dist/leaflet.css";
import { QRCodeCanvas } from "qrcode.react";

import "bootstrap/dist/css/bootstrap.min.css";
import { Button, Modal } from "react-bootstrap";

import axios from "axios";

import { BsArrowClockwise, BsPersonPlus, BsPersonLock, BsFillPinMapFill  } from "react-icons/bs";
import { BiLogOut, BiSolidMap } from "react-icons/bi";

interface User {
  user_id: number;
  username: string;
}

interface Reservation {
  id: number;
  id_parking: number;
  id_user: number;
  entrance: Date,
  exit_date: Date,
}



function App() {
  const [parkings, setParkings] = useState([]);
  const [user, setUser] = useState<User | null>(null);
  const [reservations, setReservations] = useState<Reservation[]>([]);

  //Search By Name
  const [search, setSearch] = useState("");

  // Filtrar por coincidencia parcial en el nombre
  const filteredParkings = parkings.filter((p: any) =>
    p.name_parking.toLowerCase().includes(search.toLowerCase())
  );


  const [token, setToken] = useState("");

  const mapRef = useRef<L.Map | null>(null);


  /* MODAL */
  const [showLogin, setShowLogin] = useState(false);

  const handleLoginClose = () => setShowLogin(false);
  const handleLoginShow = () => setShowLogin(true);

  /* SHOW REGISTER */
  const [showRegister, setShowRegister] = useState(false);

  const handleRegisterClose = () => setShowRegister(false);
  const handleRegisterShow = () => setShowRegister(true);

  const [form, setForm] = useState({
    username: "",
    password: "",
  });

  const handleClearForm = () =>
    setForm({
      username: "",
      password: "",
    });

  const handleLogin = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:5000/login", form);
      setToken(response.data.token);
      localStorage.setItem("token", response.data.token);

      verifiedLogin();
    } catch (error) {
      console.log(error);
    }
  };

  const handleRegister = async () => {
    try {
      await axios.post("http://127.0.0.1:5000/register", form);
      
      alert("Registrado con exito");

      verifiedLogin();
    } catch (error) {

      alert("Hubo un error en el registro");
      
    }
  };

  const fetchParkings = async () => {
    try {
      const response = await axios.get("http://127.0.0.1:5000/parkings");

      setParkings(response.data);
    } catch (error) {
      console.log(error);
    }
  };

  const logout = async () => {
    try {
      setUser(null);
      setToken("");
      localStorage.removeItem("token");
    } catch (error) {
      console.log(error);
    }
  };

  const fetchReservations = async () => {
    try {

      if(!user){
        console.log(user)
        console.log("No acceso")
        return;
      }
      
      const response = await axios.get('http://localhost:5000/mis_reservas/' + user?.user_id);
      setReservations(response.data);

    } catch (error) {
      console.log(error);
    }
  }

  const verifiedLogin = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      setToken(token);

      const response = await axios.get("http://127.0.0.1:5000/verify-login", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const user = response.data.data;

      setUser(user);

    } catch (error) {
      console.log(error);
    }
  };

  function GoToButton({ lat, lng }: { lat: number; lng: number }) {

    const goTo = () => {
      if (mapRef.current) {
        mapRef.current.flyTo([lat, lng], 16);
      }
    };

      return (
        <button className="btn btn-success w-100" onClick={goTo}>
          <BiSolidMap />
        </button>
      );
  }

  // 🔹 handleChange reutilizable para cualquier input
  const handleChange = (e: any) => {
    const { name, value } = e.target;
    setForm({
      ...form,
      [name]: value,
    });
  };

  const ParkingButton = ({
  p,
  user,
  reservations,
}: {
  p: any;
  user: User;
  reservations: Reservation[];
}) => {

  // Encontrar la reserva correspondiente cada vez que cambien `p` o `reservations`
  const findReservation = reservations.find((r) => r.id_parking === p.id && r.id_user == user.user_id);

  if (!(p.available > 0)) {
    return <button className="btn btn-info disabled">No hay parqueo disponible</button>;
  }

  if (findReservation && !findReservation.entrance) {
    return (
      <div>
        <h4>QR Para Entrar</h4>
        <QRCodeCanvas value={"http://localhost:5000/reservas/entrada/" + findReservation.id} />
      </div>
    );
  }

  if (findReservation && findReservation.entrance && !findReservation.exit_date) {
    return (
      <div>
        <h4>QR Para Salir</h4>
        <QRCodeCanvas value={"http://localhost:5000/reservas/salida/" + findReservation.id} />
      </div>
    );
  }

    

  return (
    <button
      className="btn btn-primary"
      onClick={() =>
        (window.location.href = `http://localhost:5000/pagar/${p.id}/${user?.user_id}`)
      }
    >
      Comprar Parqueo
    </button>
  );
};

  useEffect(() => {
    fetchParkings();
    verifiedLogin();
  }, []);

  useEffect(() => {
    fetchReservations();
  }, [user]);

  useEffect(() => {
    setInterval(() => {

      if(!user) return;

      fetchReservations();
    }, 10000);
  }, [user]);

  return (
    <>

      

      <div className="d-flex flex-row justify-content-around align-items-center">

        <div>
          <h3>ParkMapPark</h3>
        </div>

        {!user ? (
          <div className="m-2">
            <button className="btn btn-primary m-1" onClick={handleLoginShow}>
              <BsPersonLock />
            </button>
            <button className="btn btn-success m-1" onClick={handleRegisterShow}><BsPersonPlus /></button>
          </div>
        ) : (
          <div className="d-flex flex-column justify-content-center align-items-center">
            <h4>{user?.username}</h4>
            <button className="btn btn-danger" onClick={logout}>
              <BiLogOut />
            </button>
          </div>
        )}

        <div>
          <button className="btn btn-warning m-2" onClick={fetchParkings}>
              <BsArrowClockwise />
          </button>
        </div>
      </div>

      <div className="d-flex flex-row flex-wrap justify-content-center m-2">

        <div className="p-5 m-2 card">

          <h4 className="text-center"><BsFillPinMapFill /></h4>

          <input className="form-control" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar Parqueos" />

          <div>

            {filteredParkings.map((p: any) => (
              <div className="d-flex flex-row flex-wrap justify-content-evenly align-items-center alert alert-primary m-1" key={p.id}>
                {p.name_parking}

                <div className="w-100">

                  <GoToButton lat={p.latitud} lng={p.longitud}  />

                  {/* <button className="btn btn-success w-100">
                    <BiSolidMap />
                  </button> */}
                </div>

              </div>
            ))}

          </div>

        </div>

        <MapContainer
          center={[18.4861, -69.9312]}
          zoom={13}
          scrollWheelZoom={false}
          style={{ height: "90vh", width: '70%'}}
          ref={mapRef}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {parkings.map((p: any) => (
            <Marker key={p.id} position={[p.latitud, p.longitud]}>
              <Popup>
                <div style={{ textAlign: "center" }}>
                  {/* Imagen del sitio */}
                  <img
                    src={"http://127.0.0.1:5000/imagen/" + p.id}
                    alt="Parking"
                    style={{
                      width: "100%",
                      borderRadius: "8px",
                      marginBottom: "8px",
                    }}
                  />

                  <p>{p.name_parking}</p>

                  {/* Texto */}
                  <p style={{ margin: "6px 0", fontWeight: "bold" }}>
                    🚗 Estacionamientos libres
                  </p>

                  <p>{p.available}</p>

                  {/* QR Code */}
                  {/* <QRCodeCanvas value="https://tu-enlace-o-info.com" size={100} /> */}

                  {user ? (
                    <ParkingButton p={p} user={user} reservations={reservations} />
                  ) : (
                    <button
                      className="btn btn-primary m-1"
                      onClick={handleLoginShow}
                    >
                      <BsPersonLock />
                    </button>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>


      </div>

      {/* Modales */}
      <Modal
        show={showLogin}
        onHide={() => {
          handleLoginClose();
          handleClearForm();
        }}
      >
        <Modal.Header closeButton>
          <Modal.Title>Login</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          <div className="mb-3">
            <label className="form-label">Username:</label>
            <input
              type="email"
              className="form-control"
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="User"
            />
          </div>

          <div className="mb-3">
            <label className="form-label">Contraseña:</label>
            <input
              type="password"
              className="form-control"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Contraseña"
            />
          </div>
        </Modal.Body>

        <Modal.Footer>
          <Button
            variant="secondary"
            onClick={() => {
              handleLoginClose();
              handleClearForm();
            }}
          >
            Cerrar
          </Button>

          <Button
            variant="primary"
            onClick={() => {
              handleLogin();
              handleLoginClose();
              handleClearForm();
            }}
          >
            Guardar
          </Button>
        </Modal.Footer>
      </Modal>

      {/* REGISTRO */}

      <Modal
        show={showRegister}
        onHide={() => {
          handleRegisterClose();
          handleClearForm();
        }}
      >
        <Modal.Header closeButton>
          <Modal.Title>Registro</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          <div className="mb-3">
            <label className="form-label">Username:</label>
            <input
              type="email"
              className="form-control"
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="User"
            />
          </div>

          <div className="mb-3">
            <label className="form-label">Contraseña:</label>
            <input
              type="password"
              className="form-control"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Contraseña"
            />
          </div>
        </Modal.Body>

        <Modal.Footer>
          <Button
            variant="secondary"
            onClick={() => {
              handleRegisterClose();
              handleClearForm();
            }}
          >
            Cerrar
          </Button>

          <Button
            variant="primary"
            onClick={() => {
              handleRegister();
              handleRegisterClose();
              handleClearForm();
            }}
          >
            Guardar
          </Button>
        </Modal.Footer>
      </Modal>

    </>
  );
}

export default App;
