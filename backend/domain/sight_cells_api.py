from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import sight_cells_service as service
from domain.sight_cells_model import sight_cells
from domain.sight_cells_schemas import RecordBeam, ProtectStation

router = APIRouter()

@router.get('/sight_cells')
def list_sight_cells(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, sight_cells)


@router.post('/sight_cells/record-beam')
def record_beam(data: RecordBeam, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.record_beam(conn, user, data)
        record(conn, user, 'sight_cells.record_beam')
        return output


@router.post('/sight_cells/protect-station')
def protect_station(data: ProtectStation, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.protect_station(conn, user, data)
        record(conn, user, 'sight_cells.protect_station')
        return output
