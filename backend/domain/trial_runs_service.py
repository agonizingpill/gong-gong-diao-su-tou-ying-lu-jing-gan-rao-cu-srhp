from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, update
from domain.sculpture_bands_model import sculpture_bands
from domain.shadow_plans_model import shadow_plans
from domain.trial_runs_model import trial_runs, trial_cells, trial_maps

TEAMS = ('NORTH', 'SOUTH')


def _active_run(conn, band_code, lock=False):
    query = select(trial_runs).where(trial_runs.c.band == band_code,
                                     trial_runs.c.status != '底图失效').order_by(trial_runs.c.baseline_revision.desc())
    if lock:
        query = query.with_for_update()
    row = conn.execute(query).mappings().first()
    return dict(row) if row is not None else None


def _stale_runs(conn, band):
    """底图换版后，把封存版本落后于现用底图的对照中批次标记失效，需重新对照。"""
    rows = conn.execute(select(trial_runs).where(
        trial_runs.c.band == band['code'],
        trial_runs.c.status == '对照中',
        trial_runs.c.baseline_revision != band['revision']).with_for_update()).mappings()
    codes = [row['code'] for row in rows]
    if codes:
        conn.execute(trial_runs.update().where(trial_runs.c.code.in_(codes)).values(status='底图失效'))
    return codes


def _team_cells(conn, run_code, team):
    query = select(trial_cells).where(trial_cells.c.run == run_code, trial_cells.c.team == team)\
        .order_by(trial_cells.c.y, trial_cells.c.x)
    return [dict(row) for row in conn.execute(query).mappings()]


def _team_map(conn, run_code, team):
    row = conn.execute(select(trial_maps).where(trial_maps.c.run == run_code,
                                                trial_maps.c.team == team)).mappings().first()
    return dict(row) if row is not None else None


def _same_cluster_pairs(layout):
    """返回在该布局中同簇的无序格对集合，元素为排序后的格坐标 ((x, y), (x, y))。

    两队同一网格的格编码不同（编码里含队名），因此一律按格坐标对齐。
    """
    by_cluster = {}
    for point in layout:
        by_cluster.setdefault(point['cluster'], []).append((point['x'], point['y']))
    pairs = set()
    for positions in by_cluster.values():
        positions = sorted(positions)
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                pairs.add((positions[i], positions[j]))
    return pairs


def _diff_pairs(own_layout, other_layout):
    """只在本队图中同簇、另一队图中不同簇的格对（非对称，按本队视角列出）。"""
    own_pairs = _same_cluster_pairs(own_layout)
    other_pairs = _same_cluster_pairs(other_layout)
    own_cluster = {(p['x'], p['y']): p['cluster'] for p in own_layout}
    other_cluster = {(p['x'], p['y']): p['cluster'] for p in other_layout}
    own_code = {(p['x'], p['y']): p['code'] for p in own_layout}
    diff = []
    for pos_a, pos_b in sorted(own_pairs - other_pairs):
        diff.append({'cell_a': own_code[pos_a], 'cell_b': own_code[pos_b],
                     'own_cluster': own_cluster[pos_a],
                     'other_cluster_a': other_cluster.get(pos_a),
                     'other_cluster_b': other_cluster.get(pos_b)})
    return diff


def _refresh_diff(conn, run_code):
    """两队都封存后重算各自的差异格对；只有一队时差异留空。"""
    map_a = _team_map(conn, run_code, 'NORTH')
    map_b = _team_map(conn, run_code, 'SOUTH')
    if map_a is None or map_b is None:
        for team_map in (map_a, map_b):
            if team_map is not None and team_map['diff_pairs']:
                update(conn, trial_maps, team_map['code'], diff_pairs=[])
        return
    diff_a = _diff_pairs(map_a['layout'], map_b['layout'])
    diff_b = _diff_pairs(map_b['layout'], map_a['layout'])
    update(conn, trial_maps, map_a['code'], diff_pairs=diff_a)
    update(conn, trial_maps, map_b['code'], diff_pairs=diff_b)


def open_trial(conn, user, data):
    band = get(conn, sculpture_bands, data.band, lock=True)
    _stale_runs(conn, band)
    existing = _active_run(conn, band['code'])
    if existing is not None:
        return existing
    code = f'TRIAL-{band["code"]}-R{band["revision"]}'
    return insert(conn, trial_runs, code=code, band=band['code'],
                  baseline_revision=band['revision'], status='对照中',
                  sealed_by=user['sub'], adopted_team=None, adopted_plan=None)


def sync_stale(conn, band_code):
    """把落后于现用底图的对照中批次标记失效，随所在事务一并提交。"""
    band = get(conn, sculpture_bands, band_code, lock=True)
    return _stale_runs(conn, band), band


def record_trial(conn, user, data, band=None):
    if band is None:
        band = get(conn, sculpture_bands, data.band, lock=True)
    need(data.team in TEAMS, '试投队须为 NORTH 或 SOUTH')
    need(0 <= data.x < band['cols'] and 0 <= data.y < band['rows'], '观测格超出网格边界')
    need(0 <= data.shade <= 1 and 0 <= data.spill <= 1, '面积比须在 0 到 1')
    run = _active_run(conn, band['code'], lock=True)
    need(run is not None, '该投影带尚无对照批次，先开启双队试投对照')
    need(run['status'] == '对照中', '该对照批次已结束，不能再补测')
    need(run['baseline_revision'] == band['revision'], '底图已换版，旧对照已失效，请重新开启对照后再补测')
    code = f'{run["code"]}-{data.team}-{data.x}-{data.y}'
    existing = conn.execute(select(trial_cells).where(trial_cells.c.code == code)).mappings().first()
    payload = dict(run=run['code'], team=data.team, x=data.x, y=data.y,
                   shade=data.shade, spill=data.spill)
    if existing is None:
        result = insert(conn, trial_cells, code=code, **payload)
    elif (data.shade, data.spill) == (existing['shade'], existing['spill']):
        return dict(existing)
    else:
        result = update(conn, trial_cells, code, shade=data.shade, spill=data.spill)
    return result


def segment_trial(conn, user, data):
    band = get(conn, sculpture_bands, data.band, lock=True)
    need(data.team in TEAMS, '试投队须为 NORTH 或 SOUTH')
    need(2 <= data.clusters <= 4, '灯组数量须在 2 到 4 组')
    run = _active_run(conn, band['code'], lock=True)
    need(run is not None, '该投影带尚无对照批次，先开启双队试投对照')
    need(run['status'] == '对照中', '该对照批次已结束')
    need(run['baseline_revision'] == band['revision'], '底图已换版，封存对照已失效，请重新对照')
    points = _team_cells(conn, run['code'], data.team)
    need(len(points) == band['cols'] * band['rows'], '该队网格有缺测，补齐后再分簇')
    return submit(user, {'kind': 'trial', 'team': data.team, 'band': dict(band),
                         'points': points, 'clusters': data.clusters, 'run': run['code']})


def pin_trial(conn, user, data):
    run_job = result(user, data.token)
    need(run_job['input'].get('kind') == 'trial', '该凭证不是双队试投分簇任务')
    band = get(conn, sculpture_bands, data.band, lock=True)
    need(data.team in TEAMS, '试投队须为 NORTH 或 SOUTH')
    run = _active_run(conn, band['code'], lock=True)
    need(run is not None and run['code'] == run_job['input']['run'], '任务与当前对照批次不一致')
    need(run['status'] == '对照中', '该对照批次已结束')
    need(run_job['input']['team'] == data.team, '任务归属灯组与提交灯组不一致')
    need(run['baseline_revision'] == band['revision'],
          '底图版本已有更新，封存读数失效，请重新对照后再分簇')
    model = run_job['result']
    points = _team_cells(conn, run['code'], data.team)
    need(len(points) == band['cols'] * band['rows'], '该队网格有缺测，补齐后再分簇')
    code = f'MAP-{run["code"]}-{data.team}'
    existing = _team_map(conn, run['code'], data.team)
    values = dict(clusters=model['clusters'], revision=band['revision'], layout=model['layout'],
                  evidence=model['evidence'], diff_pairs=[], token=data.token)
    if existing is None:
        insert(conn, trial_maps, code=code, run=run['code'], team=data.team, **values)
    else:
        update(conn, trial_maps, existing['code'], **values)
    _refresh_diff(conn, run['code'])
    # 回读封存结果，确保返回值包含本次重算的差异格对而非写入前的空列表。
    return get(conn, trial_maps, code)


def adopt_trial(conn, user, data):
    band = get(conn, sculpture_bands, data.band, lock=True)
    need(data.team in TEAMS, '试投队须为 NORTH 或 SOUTH')
    run = _active_run(conn, band['code'], lock=True)
    need(run is not None, '该投影带没有可采纳的对照批次')
    # 采纳重试：已采纳同一队则原样返回，不重复升版、不重复建图。
    if run['status'] == '已采纳':
        need(run['adopted_team'] == data.team, '该批次已采纳另一灯组读数')
        plan = get(conn, shadow_plans, run['adopted_plan'])
        return {'run': run['code'], 'team': run['adopted_team'], 'plan': plan['code'],
                'revision': plan['revision'], 'retried': True}
    need(run['status'] == '对照中', '该对照批次已失效，请重新对照')
    need(run['baseline_revision'] == band['revision'], '底图已换版，封存对照失效，请重新对照')
    team_map = _team_map(conn, run['code'], data.team)
    need(team_map is not None, '该灯组尚未封存分簇图谱，不能采纳')
    other = _team_map(conn, run['code'], data.team == 'NORTH' and 'SOUTH' or 'NORTH')
    need(other is not None, '两队图谱都封存后才能采纳其中一队的整套读数')
    # 归档图与现用底图一次性切换：新建正式 shadow_plan 取代该投影带旧图，旧图保留为历史。
    conn.execute(shadow_plans.update().where(shadow_plans.c.band == band['code'],
                                             shadow_plans.c.superseded.is_(False))
                 .values(superseded=True))
    plan = insert(conn, shadow_plans, code=data.plan_code, band=band['code'],
                  revision=band['revision'], clusters=team_map['clusters'],
                  layout=team_map['layout'], evidence=team_map['evidence'],
                  token=team_map['token'], superseded=False)
    update(conn, trial_runs, run['code'], status='已采纳', adopted_team=data.team,
           adopted_plan=data.plan_code)
    return {'run': run['code'], 'team': data.team, 'plan': plan['code'],
            'revision': plan['revision'], 'retried': False}
