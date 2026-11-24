from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.sculpture_bands_model import sculpture_bands
from domain.sight_cells_model import sight_cells
from domain.shadow_plans_model import shadow_plans
from domain.light_handoffs_model import light_handoffs


def offer_station(conn, user, data):
    from domain.plot_checks import offer_station
    return offer_station(conn,user,data)


def check_station(conn, user, data):
    from domain.plot_checks import check_station
    return check_station(conn,user,data.code)
