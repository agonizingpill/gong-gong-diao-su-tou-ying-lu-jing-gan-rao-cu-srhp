from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import light_handoffs_service as service
from domain.light_handoffs_model import light_handoffs
from domain.light_handoffs_schemas import OfferStation, CheckStation

router = APIRouter()

@router.get('/light_handoffs')
def list_light_handoffs(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, light_handoffs)


@router.post('/light_handoffs/offer-station')
def offer_station(data: OfferStation, user=Depends(actor)):
    allow(user, ('operator',))
    with transaction() as conn:
        output = service.offer_station(conn, user, data)
        record(conn, user, 'light_handoffs.offer_station')
        return output


@router.post('/light_handoffs/check-station')
def check_station(data: CheckStation, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.check_station(conn, user, data)
        record(conn, user, 'light_handoffs.check_station')
        return output
