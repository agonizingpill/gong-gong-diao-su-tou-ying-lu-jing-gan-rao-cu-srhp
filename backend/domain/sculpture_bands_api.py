from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import sculpture_bands_service as service
from domain.sculpture_bands_model import sculpture_bands
from domain.sculpture_bands_schemas import BookBand

router = APIRouter()

@router.get('/sculpture_bands')
def list_sculpture_bands(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, sculpture_bands)


@router.post('/sculpture_bands/book-band')
def book_band(data: BookBand, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.book_band(conn, user, data)
        record(conn, user, 'sculpture_bands.book_band')
        return output
