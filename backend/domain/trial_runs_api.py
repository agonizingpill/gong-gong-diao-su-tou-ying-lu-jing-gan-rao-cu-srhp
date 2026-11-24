from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import trial_runs_service as service
from domain.trial_runs_model import trial_runs, trial_cells, trial_maps
from domain.trial_runs_schemas import OpenTrial, RecordTrial, SegmentTrial, PinTrial, AdoptTrial

router = APIRouter()


@router.get('/trial_runs')
def list_trial_runs(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, trial_runs)


@router.get('/trial_cells')
def list_trial_cells(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, trial_cells)


@router.get('/trial_maps')
def list_trial_maps(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, trial_maps)


@router.post('/trial_runs/open-trial')
def open_trial(data: OpenTrial, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.open_trial(conn, user, data)
        record(conn, user, 'trial_runs.open_trial')
        return output


@router.post('/trial_runs/record-trial')
def record_trial(data: RecordTrial, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    # 先在独立事务里令落后于现用底图的旧封存批次失效并提交，再做本次补测校验。
    with transaction() as conn:
        _, band = service.sync_stale(conn, data.band)
    with transaction() as conn:
        output = service.record_trial(conn, user, data, band=band)
        record(conn, user, 'trial_runs.record_trial')
        return output


@router.post('/trial_runs/segment-trial')
def segment_trial(data: SegmentTrial, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.segment_trial(conn, user, data)
        record(conn, user, 'trial_runs.segment_trial')
        return output


@router.post('/trial_runs/pin-trial')
def pin_trial(data: PinTrial, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.pin_trial(conn, user, data)
        record(conn, user, 'trial_runs.pin_trial')
        return output


@router.post('/trial_runs/adopt-trial')
def adopt_trial(data: AdoptTrial, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.adopt_trial(conn, user, data)
        record(conn, user, 'trial_runs.adopt_trial')
        return output
