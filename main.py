"""Punto de entrada de la API.  Ejecutar con:  uvicorn main:app --reload"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError, WriteError

from app.database import close_db, get_db, init_db
from app.exceptions import AppError
from app.routers import clases, reservas, socios

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("tpi")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(get_db())  # crea colecciones con validador e índices si faltan
    yield
    close_db()


app = FastAPI(
    title="TPI Gimnasio - API",
    description="CRUD con baja lógica sobre MongoDB Atlas: socios, clases y reservas.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(socios.router)
app.include_router(clases.router)
app.include_router(reservas.router)


@app.get("/health", tags=["Sistema"], summary="Estado de la API y de la conexión a MongoDB")
def health():
    get_db().command("ping")
    return {"status": "ok", "db": get_db().name}


@app.exception_handler(AppError)
async def manejar_error_de_negocio(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(WriteError)
async def manejar_error_de_escritura(request: Request, exc: WriteError):
    if exc.code == 121:  # falló el $jsonSchema de la colección
        return JSONResponse(status_code=422, content={"detail": "El documento no cumple la validación del esquema de MongoDB"})
    log.exception("Error de escritura en MongoDB")
    return JSONResponse(status_code=500, content={"detail": "Error al escribir en la base de datos"})


@app.exception_handler(ServerSelectionTimeoutError)
async def manejar_sin_conexion(request: Request, exc: ServerSelectionTimeoutError):
    log.error("Sin conexión con MongoDB: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "No se pudo conectar con MongoDB Atlas"})


@app.exception_handler(PyMongoError)
async def manejar_error_de_mongo(request: Request, exc: PyMongoError):
    log.exception("Error de MongoDB")
    return JSONResponse(status_code=500, content={"detail": "Error en la base de datos"})
