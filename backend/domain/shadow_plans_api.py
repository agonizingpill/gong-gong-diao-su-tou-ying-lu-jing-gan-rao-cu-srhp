from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import shadow_plans_service as service
from domain.shadow_plans_model import shadow_plans
from domain.shadow_plans_schemas import SegmentBank, PinMap

router = APIRouter()

@router.get('/shadow_plans')
def list_shadow_plans(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, shadow_plans)


@router.post('/shadow_plans/segment-bank')
def segment_bank(data: SegmentBank, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.segment_bank(conn, user, data)
        record(conn, user, 'shadow_plans.segment_bank')
        return output


@router.post('/shadow_plans/pin-map')
def pin_map(data: PinMap, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.pin_map(conn, user, data)
        record(conn, user, 'shadow_plans.pin_map')
        return output
