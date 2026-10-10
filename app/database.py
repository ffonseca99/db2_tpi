"""Conexión única al clúster de MongoDB Atlas e inicialización de colecciones e índices."""
import logging

from pymongo import ASCENDING, MongoClient
from pymongo.database import Database
from pymongo.errors import OperationFailure

from app.config import get_settings
from app.validators import VALIDATORS

log = logging.getLogger("tpi.database")

_client: MongoClient | None = None
_db: Database | None = None


def get_db() -> Database:
    """Devuelve la base de datos; crea el cliente la primera vez (una sola conexión por proceso)."""
    global _client, _db
    if _db is None:
        settings = get_settings()
        _client = MongoClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=5000,
            tz_aware=True,
            appname="tpi-gimnasio",
        )
        _db = _client[settings.db_name]
    return _db


def set_db(db: Database | None) -> None:
    """Reemplaza la base (se usa en los tests para inyectar una base simulada)."""
    global _db
    _db = db


def close_db() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def init_db(db: Database) -> None:
    """Crea las colecciones con su validador si no existen y asegura los índices."""
    existentes = set(db.list_collection_names())
    for nombre, validador in VALIDATORS.items():
        if nombre not in existentes:
            db.create_collection(nombre, validator=validador)
            log.info("Colección '%s' creada con validador $jsonSchema", nombre)

    # El DNI es único solo entre socios activos: así un DNI dado de baja se puede volver a registrar.
    _crear_indice(
        db.socios,
        [("dni", ASCENDING)],
        name="uq_socios_dni_activo",
        unique=True,
        partialFilterExpression={"activo": True},
    )
    _crear_indice(db.reservas, [("claseId", ASCENDING), ("estado", ASCENDING)], name="ix_reservas_clase_estado")
    _crear_indice(db.reservas, [("socioId", ASCENDING)], name="ix_reservas_socio")


def _crear_indice(coleccion, claves, **opciones) -> None:
    try:
        coleccion.create_index(claves, **opciones)
    except OperationFailure as exc:
        # No se frena el arranque: el servicio igual valida el DNI duplicado por código.
        log.warning("No se pudo crear el índice %s en '%s': %s", opciones.get("name"), coleccion.name, exc)
