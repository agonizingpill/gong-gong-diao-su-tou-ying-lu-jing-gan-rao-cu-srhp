from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.sculpture_bands_model import sculpture_bands
from domain.sight_cells_model import sight_cells
from domain.shadow_plans_model import shadow_plans
from domain.light_handoffs_model import light_handoffs


def record_beam(conn, user, data):
    from domain.plot_checks import record_beam
    return record_beam(conn,data)


def protect_station(conn, user, data):
    from domain.plot_checks import protect_station
    return protect_station(conn,data.code)
