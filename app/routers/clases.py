from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.repositories.clase_repository import ClaseRepository
from app.schemas.clase import ClaseCreate, ClaseOut, ClaseUpdate
from app.services.clase_service import ClaseService
from app.utils import serialize

router = APIRouter(prefix="/clases", tags=["Clases"])


def get_service() -> ClaseService:
    return ClaseService(ClaseRepository(get_db()))


@router.post("", response_model=ClaseOut, status_code=201, summary="Crear clase")
def crear_clase(datos: ClaseCreate, service: ClaseService = Depends(get_service)):
    return serialize(service.crear(datos))


@router.get("", response_model=list[ClaseOut], summary="Listar clases activas")
def listar_clases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ClaseService = Depends(get_service),
):
    return serialize(service.listar(skip, limit))


@router.get("/{clase_id}", response_model=ClaseOut, summary="Obtener una clase activa")
def obtener_clase(clase_id: str, service: ClaseService = Depends(get_service)):
    return serialize(service.obtener(clase_id))


@router.patch("/{clase_id}", response_model=ClaseOut, summary="Modificar campos de una clase")
def actualizar_clase(clase_id: str, datos: ClaseUpdate, service: ClaseService = Depends(get_service)):
    return serialize(service.actualizar(clase_id, datos))


@router.delete("/{clase_id}", response_model=ClaseOut, summary="Baja lógica de una clase")
def eliminar_clase(clase_id: str, service: ClaseService = Depends(get_service)):
    return serialize(service.eliminar(clase_id))
