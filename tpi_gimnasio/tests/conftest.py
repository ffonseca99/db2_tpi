"""Fixtures: la API corre contra una base simulada (mongomock), sin tocar MongoDB Atlas."""
import mongomock
import pytest
from fastapi.testclient import TestClient

from app import database
from app.validators import VALIDATORS
from main import app


@pytest.fixture()
def db():
    cliente = mongomock.MongoClient(tz_aware=True)
    base = cliente["gimnasio_test"]
    # mongomock no soporta create_collection(validator=...): se crean vacías y el esquema
    # se verifica aparte en test_documentos_cumplen_el_jsonschema.
    for nombre in VALIDATORS:
        base.create_collection(nombre)
    database.set_db(base)
    yield base
    database.set_db(None)


@pytest.fixture()
def client(db):
    with TestClient(app) as c:  # el lifespan ejecuta init_db sobre la base simulada
        yield c
