"""Pruebas del ciclo CREATE / READ / UPDATE / DELETE (baja lógica) y de las reglas de reservas."""
from datetime import datetime

from bson import Decimal128, ObjectId

from app.validators import VALIDATORS

INICIO = "2026-10-20T22:00:00Z"

SOCIO = {
    "dni": "30123456",
    "nombre": "Lucía",
    "apellido": "Fernández",
    "email": "lucia@example.com",
    "membresia": {"plan": "MENSUAL", "precio": 25000},
}
CLASE = {
    "nombre": "Boxeo",
    "instructor": {"nombre": "Martín Gómez"},
    "cupoMaximo": 1,
    "fechaInicio": INICIO,
}

TIPOS_BSON = {
    "string": str, "object": dict, "bool": bool, "array": list,
    "date": datetime, "objectId": ObjectId, "int": int, "null": type(None),
}


def cumple_validador(doc: dict, coleccion: str) -> None:
    """Chequea un documento contra el $jsonSchema real de la colección (required, bsonType y enum)."""
    esquema = VALIDATORS[coleccion]["$jsonSchema"]
    for campo in esquema["required"]:
        assert campo in doc, f"{coleccion}: falta el campo obligatorio '{campo}'"
    for campo, regla in esquema["properties"].items():
        if campo not in doc:
            continue
        valor = doc[campo]
        if "enum" in regla:
            assert valor in regla["enum"], f"{coleccion}.{campo}: valor fuera del enum"
        tipos = regla.get("bsonType", [])
        tipos = [tipos] if isinstance(tipos, str) else tipos
        if tipos:
            ok = any(isinstance(valor, TIPOS_BSON[t]) and not (t == "int" and isinstance(valor, bool)) for t in tipos)
            assert ok, f"{coleccion}.{campo}: {valor!r} no es de tipo {tipos}"


def crear_socio(client, **cambios):
    r = client.post("/socios", json={**SOCIO, **cambios})
    assert r.status_code == 201, r.text
    return r.json()


def crear_clase(client, **cambios):
    r = client.post("/clases", json={**CLASE, **cambios})
    assert r.status_code == 201, r.text
    return r.json()


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


# ---------------------------------------------------------------- SOCIOS
def test_socio_crud_con_baja_logica(client, db):
    socio = crear_socio(client)
    assert socio["activo"] is True and socio["fechaBaja"] is None and socio["fechaAlta"]

    assert [s["id"] for s in client.get("/socios").json()] == [socio["id"]]
    assert client.get(f"/socios/{socio['id']}").json()["dni"] == "30123456"

    # UPDATE parcial: solo cambia lo enviado, y la membresía se actualiza subcampo a subcampo
    r = client.patch(f"/socios/{socio['id']}", json={"telefono": "3515551234", "membresia": {"plan": "ANUAL"}})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["telefono"] == "3515551234"
    assert cuerpo["membresia"] == {"plan": "ANUAL", "precio": 25000.0, "fechaInicio": None, "fechaVencimiento": None}
    assert cuerpo["nombre"] == "Lucía"

    # DELETE = baja lógica
    r = client.delete(f"/socios/{socio['id']}")
    assert r.status_code == 200
    assert r.json()["activo"] is False and r.json()["fechaBaja"] is not None

    # ya no se lista ni se puede leer, modificar o volver a dar de baja...
    assert client.get("/socios").json() == []
    assert client.get(f"/socios/{socio['id']}").status_code == 404
    assert client.patch(f"/socios/{socio['id']}", json={"nombre": "X"}).status_code == 404
    assert client.delete(f"/socios/{socio['id']}").status_code == 404

    # ...pero el documento sigue físicamente en la colección
    crudo = db.socios.find_one({"_id": ObjectId(socio["id"])})
    assert crudo is not None and crudo["activo"] is False and crudo["fechaBaja"] is not None


def test_socio_con_precio_decimal128_se_lista(client, db):
    # Datos cargados desde mongosh con NumberDecimal llegan como Decimal128, no como float
    db.socios.insert_one({
        "dni": "30999888", "nombre": "Ana", "apellido": "Paz", "email": "ana@example.com",
        "membresia": {"plan": "ANUAL", "precio": Decimal128("45000.00")}, "activo": True, "fechaBaja": None,
    })
    r = client.get("/socios", params={"skip": 0, "limit": 50})
    assert r.status_code == 200, r.text
    assert r.json()[0]["membresia"]["precio"] == 45000.0


def test_socio_dni_duplicado_y_reuso_tras_baja(client):
    socio = crear_socio(client)
    assert client.post("/socios", json=SOCIO).status_code == 409
    client.delete(f"/socios/{socio['id']}")
    assert client.post("/socios", json=SOCIO).status_code == 201  # el DNI de un socio dado de baja se libera


def test_socio_validaciones(client):
    assert client.post("/socios", json={**SOCIO, "email": "no-es-un-email"}).status_code == 422
    assert client.post("/socios", json={**SOCIO, "activo": False}).status_code == 422  # campo no permitido
    assert client.post("/socios", json={k: v for k, v in SOCIO.items() if k != "membresia"}).status_code == 422
    assert client.get("/socios/abc").status_code == 400
    socio = crear_socio(client)
    assert client.patch(f"/socios/{socio['id']}", json={}).status_code == 400
    assert client.patch(f"/socios/{socio['id']}", json={"activo": False}).status_code == 422


def test_socio_update_dni_repetido(client):
    crear_socio(client)
    otro = crear_socio(client, dni="40111222", email="otro@example.com")
    assert client.patch(f"/socios/{otro['id']}", json={"dni": "30123456"}).status_code == 409


# ---------------------------------------------------------------- CLASES
def test_clase_crud_con_baja_logica(client, db):
    clase = crear_clase(client)
    assert clase["activo"] is True and clase["fechaBaja"] is None
    assert clase["fechaAlta"] is not None  # la pone el servidor
    assert clase["fechaInicio"].startswith("2026-10-20T22:00:00")
    assert "horarios" not in clase

    r = client.patch(
        f"/clases/{clase['id']}",
        json={"sala": "Sala 2", "fechaInicio": "2026-10-21T22:00:00Z", "instructor": {"especialidad": "Crossfit"}},
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["sala"] == "Sala 2" and cuerpo["fechaInicio"].startswith("2026-10-21T22:00:00")
    assert cuerpo["instructor"] == {"nombre": "Martín Gómez", "especialidad": "Crossfit"}
    assert cuerpo["fechaAlta"] == clase["fechaAlta"]  # fechaAlta no cambia

    assert client.delete(f"/clases/{clase['id']}").json()["activo"] is False
    assert client.get("/clases").json() == []
    assert client.get(f"/clases/{clase['id']}").status_code == 404
    assert db.clases.count_documents({}) == 1


def test_clases_son_ocurrencias_independientes(client):
    """Boxeo hoy y boxeo mañana son dos clases distintas, cada una con su cupo y su baja."""
    hoy = crear_clase(client)
    manana = crear_clase(client, fechaInicio="2026-10-21T22:00:00Z")
    assert hoy["id"] != manana["id"]
    client.delete(f"/clases/{hoy['id']}")
    assert [c["id"] for c in client.get("/clases").json()] == [manana["id"]]


def test_clase_validaciones(client):
    sin_inicio = {k: v for k, v in CLASE.items() if k != "fechaInicio"}
    assert client.post("/clases", json=sin_inicio).status_code == 422
    assert client.post("/clases", json={**CLASE, "fechaInicio": "mañana"}).status_code == 422
    assert client.post("/clases", json={**CLASE, "horarios": []}).status_code == 422  # ya no existe
    assert client.post("/clases", json={**CLASE, "fechaAlta": INICIO}).status_code == 422  # la pone el servidor
    assert client.post("/clases", json={**CLASE, "cupoMaximo": 0}).status_code == 422
    assert client.post("/clases", json={**CLASE, "cupoMaximo": "veinte"}).status_code == 422


# ---------------------------------------------------------------- RESERVAS
def test_reserva_ciclo_completo_cupo_y_baja_logica(client, db):
    a = crear_socio(client)
    b = crear_socio(client, dni="40111222", email="b@example.com")
    clase = crear_clase(client)  # cupo 1
    otra_clase = crear_clase(client, fechaInicio="2026-10-21T22:00:00Z")  # otra ocurrencia, cupo propio

    alta = {"socioId": a["id"], "claseId": clase["id"]}
    r = client.post("/reservas", json=alta)
    assert r.status_code == 201
    reserva = r.json()
    assert reserva["estado"] == "CONFIRMADA" and reserva["activo"] is True
    assert "fechaClase" not in reserva
    assert "fechaClase" not in db.reservas.find_one({"_id": ObjectId(reserva["id"])})

    # mismo socio otra vez -> duplicada; otro socio -> sin cupo
    assert client.post("/reservas", json=alta).status_code == 409
    assert client.post("/reservas", json={**alta, "socioId": b["id"]}).status_code == 409
    # la otra clase tiene su propio cupo
    assert client.post("/reservas", json={"socioId": b["id"], "claseId": otra_clase["id"]}).status_code == 201

    # filtros de listado
    assert len(client.get("/reservas", params={"socioId": a["id"]}).json()) == 1
    assert len(client.get("/reservas", params={"claseId": clase["id"], "estado": "CONFIRMADA"}).json()) == 1

    # cancelar libera el cupo; reactivar con cupo ocupado falla
    assert client.patch(f"/reservas/{reserva['id']}", json={"estado": "CANCELADA"}).json()["estado"] == "CANCELADA"
    r2 = client.post("/reservas", json={**alta, "socioId": b["id"]})
    assert r2.status_code == 201
    assert client.patch(f"/reservas/{reserva['id']}", json={"estado": "CONFIRMADA"}).status_code == 409

    # ya no se puede mandar fechaClase
    assert client.post("/reservas", json={**alta, "fechaClase": INICIO}).status_code == 422
    assert client.patch(f"/reservas/{reserva['id']}", json={"fechaClase": INICIO}).status_code == 422

    # baja lógica
    assert client.delete(f"/reservas/{reserva['id']}").json()["activo"] is False
    assert client.get(f"/reservas/{reserva['id']}").status_code == 404
    assert reserva["id"] not in [x["id"] for x in client.get("/reservas").json()]
    assert db.reservas.find_one({"_id": ObjectId(reserva["id"])})["activo"] is False


def test_reserva_requiere_socio_y_clase_activos(client):
    socio, clase = crear_socio(client), crear_clase(client)
    alta = {"socioId": socio["id"], "claseId": clase["id"]}

    assert client.post("/reservas", json={**alta, "socioId": str(ObjectId())}).status_code == 422
    assert client.post("/reservas", json={**alta, "socioId": "123"}).status_code == 422

    client.delete(f"/socios/{socio['id']}")
    assert client.post("/reservas", json=alta).status_code == 422  # socio dado de baja
    client.delete(f"/clases/{clase['id']}")
    otro = crear_socio(client, dni="40111222", email="b@example.com")
    assert client.post("/reservas", json={**alta, "socioId": otro["id"]}).status_code == 422  # clase dada de baja


# ---------------------------------------------------------------- ESQUEMA DE MONGODB
def test_documentos_cumplen_el_jsonschema(client, db):
    """mongomock no aplica validadores: se comprueba aparte que lo que se guarda cumple el $jsonSchema."""
    socio = crear_socio(client, telefono="3515551234")
    sin_tel = crear_socio(client, dni="40111222", email="b@example.com")
    clase = crear_clase(client, sala="Sala 1")
    crear_clase(client, nombre="Yoga", fechaInicio="2026-10-22T10:00:00Z")
    r = client.post("/reservas", json={"socioId": socio["id"], "claseId": clase["id"]})
    client.patch(f"/reservas/{r.json()['id']}", json={"estado": "CANCELADA"})
    client.patch(f"/socios/{socio['id']}", json={"membresia": {"plan": "ANUAL"}, "telefono": "1"})
    client.patch(f"/clases/{clase['id']}", json={"fechaInicio": "2026-10-23T22:00:00Z"})
    client.delete(f"/socios/{sin_tel['id']}")

    for coleccion in VALIDATORS:
        docs = list(db[coleccion].find())
        assert docs, f"no se guardó nada en {coleccion}"
        for doc in docs:
            cumple_validador(doc, coleccion)
