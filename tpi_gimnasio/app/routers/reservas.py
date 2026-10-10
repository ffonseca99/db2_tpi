from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.repositories.clase_repository import ClaseRepository
from app.repositories.reserva_repository import ReservaRepository
from app.repositories.socio_repository import SocioRepository
from app.schemas.reserva import Estado, ReservaCreate, ReservaOut, ReservaUpdate
from app.services.reserva_service import ReservaService
from app.utils import serialize

router = APIRouter(prefix="/reservas", tags=["Reservas"])


def get_service() -> ReservaService:
    db = get_db()
    return ReservaService(ReservaRepository(db), SocioRepository(db), ClaseRepository(db))


@router.post("", response_model=ReservaOut, status_code=201, summary="Crear reserva")
def crear_reserva(datos: ReservaCreate, service: ReservaService = Depends(get_service)):
    return serialize(service.crear(datos))


@router.get("", response_model=list[ReservaOut], summary="Listar reservas activas")
def listar_reservas(
    socioId: str | None = Query(None, description="Filtra por socio"),
    claseId: str | None = Query(None, description="Filtra por clase"),
    estado: Estado | None = Query(None, description="Filtra por estado"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ReservaService = Depends(get_service),
):
    return serialize(service.listar(skip, limit, socioId, claseId, estado))


@router.get("/{reserva_id}", response_model=ReservaOut, summary="Obtener una reserva activa")
def obtener_reserva(reserva_id: str, service: ReservaService = Depends(get_service)):
    return serialize(service.obtener(reserva_id))


@router.patch("/{reserva_id}", response_model=ReservaOut, summary="Modificar el estado de una reserva (confirmar / cancelar)")
def actualizar_reserva(reserva_id: str, datos: ReservaUpdate, service: ReservaService = Depends(get_service)):
    return serialize(service.actualizar(reserva_id, datos))


@router.delete("/{reserva_id}", response_model=ReservaOut, summary="Baja lógica de una reserva")
def eliminar_reserva(reserva_id: str, service: ReservaService = Depends(get_service)):
    return serialize(service.eliminar(reserva_id))
