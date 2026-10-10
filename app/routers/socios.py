from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.repositories.socio_repository import SocioRepository
from app.schemas.socio import SocioCreate, SocioOut, SocioUpdate
from app.services.socio_service import SocioService
from app.utils import serialize

router = APIRouter(prefix="/socios", tags=["Socios"])


def get_service() -> SocioService:
    return SocioService(SocioRepository(get_db()))


@router.post("", response_model=SocioOut, status_code=201, summary="Crear socio")
def crear_socio(datos: SocioCreate, service: SocioService = Depends(get_service)):
    return serialize(service.crear(datos))


@router.get("", response_model=list[SocioOut], summary="Listar socios activos")
def listar_socios(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SocioService = Depends(get_service),
):
    return serialize(service.listar(skip, limit))


@router.get("/{socio_id}", response_model=SocioOut, summary="Obtener un socio activo")
def obtener_socio(socio_id: str, service: SocioService = Depends(get_service)):
    return serialize(service.obtener(socio_id))


@router.patch("/{socio_id}", response_model=SocioOut, summary="Modificar campos de un socio")
def actualizar_socio(socio_id: str, datos: SocioUpdate, service: SocioService = Depends(get_service)):
    return serialize(service.actualizar(socio_id, datos))


@router.delete("/{socio_id}", response_model=SocioOut, summary="Baja lógica de un socio")
def eliminar_socio(socio_id: str, service: SocioService = Depends(get_service)):
    return serialize(service.eliminar(socio_id))
