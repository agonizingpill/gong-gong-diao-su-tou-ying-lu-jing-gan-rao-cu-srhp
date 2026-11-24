from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.sculpture_bands_model import sculpture_bands
from domain.sight_cells_model import sight_cells
from domain.shadow_plans_model import shadow_plans
from domain.light_handoffs_model import light_handoffs


def segment_bank(conn, user, data):
    from domain.plot_checks import observations
    band=get(conn,sculpture_bands,data.band,lock=True)
    points=observations(conn,band['code'])
    need(2<=data.clusters<=4,'灯组数量须在 2 到 4 组')
    need(len(points)==band['cols']*band['rows'],'网格有缺测，补齐后再划分灯组')
    return submit(user,{'band':band,'points':points,'clusters':data.clusters})


def pin_map(conn, user, data):
    run=result(user,data.token)
    band=get(conn,sculpture_bands,run['input']['band']['code'],lock=True)
    model=run['result']
    need(band['revision']==run['input']['band']['revision'],'观测版本已有更新，重新划分灯组')
    return insert(conn,shadow_plans,code=data.code,band=band['code'],revision=band['revision'],
                  clusters=model['clusters'],layout=model['layout'],evidence=model['evidence'],token=data.token)
