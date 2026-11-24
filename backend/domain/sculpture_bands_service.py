from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.sculpture_bands_model import sculpture_bands
from domain.sight_cells_model import sight_cells
from domain.shadow_plans_model import shadow_plans
from domain.light_handoffs_model import light_handoffs


def book_band(conn, user, data):
    from domain.plot_checks import SCOPES
    need(data.scope in SCOPES and 3<=data.cols<=12 and 3<=data.rows<=12,'核对造型种类与网格边界')
    return insert(conn,sculpture_bands,**data.model_dump(),revision=0)
