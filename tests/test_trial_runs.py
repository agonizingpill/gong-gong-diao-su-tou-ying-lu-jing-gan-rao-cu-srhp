"""双队试投对照端到端逻辑测试（SQLite + 内联计算，绕过 Redis/FastAPI）。"""
import os
import sys
import uuid

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('JWT_SECRET', 'test-secret')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, select

import core.db as db
from core.db import metadata, transaction
import core.queueing as queueing
from domain.learning import calculate_job
from domain import sculpture_bands_model, sight_cells_model, shadow_plans_model
from domain import light_handoffs_model, trial_runs_model
from domain import trial_runs_service as svc
from domain.sculpture_bands_model import sculpture_bands
from domain.shadow_plans_model import shadow_plans
from domain.trial_runs_model import trial_runs, trial_cells, trial_maps
from domain.trial_runs_schemas import (OpenTrial, RecordTrial, SegmentTrial,
                                       PinTrial, AdoptTrial)

engine = create_engine('sqlite:///:memory:')
db.engine = engine


class FakeBroker:
    def pipeline(self):
        return self
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def set(self, *a, **k): return self
    def rpush(self, *a): return self
    def execute(self): pass


queueing.broker = FakeBroker()
JOBS = {}


def fake_submit(user, payload):
    token = uuid.uuid4().hex
    # 内联执行 worker 的计算分派
    JOBS[token] = {'owner': user['sub'], 'status': 'ready',
                   'input': payload, 'result': calculate_job(payload)}
    return {'token': token, 'status': 'queued'}


def fake_result(user, token):
    return JOBS[token]


svc.submit = fake_submit
svc.result = fake_result

OPERATOR = {'sub': 'operator@demo.test', 'role': 'operator'}
REVIEWER = {'sub': 'reviewer@demo.test', 'role': 'reviewer'}

metadata.create_all(engine)

COLS, ROWS = 4, 3
N = COLS * ROWS
failures = []


def check(name, cond, detail=''):
    status = 'PASS' if cond else 'FAIL'
    print(f'[{status}] {name}' + (f' -- {detail}' if detail and not cond else ''))
    if not cond:
        failures.append(name)


def grid_values(team_offset):
    # 两队读数略有系统差异，制造不同分簇
    vals = []
    for y in range(ROWS):
        for x in range(COLS):
            base = 0.2 + 0.5 * (x / max(1, COLS - 1))
            shade = round(min(1.0, base + team_offset + 0.02 * y), 3)
            spill = round(1.0 - shade, 3)
            vals.append((x, y, shade, spill))
    return vals


with transaction() as conn:
    conn.execute(sculpture_bands.insert().values(
        code='BANK-T', title='测试带', cols=COLS, rows=ROWS, revision=0, scope='抽象几何雕塑'))

# 1. 开启对照
with transaction() as conn:
    run = svc.open_trial(conn, OPERATOR, OpenTrial(band='BANK-T'))
check('开启对照批次', run['code'] == 'TRIAL-BANK-T-R0' and run['status'] == '对照中')
run_code = run['code']

# 重复开启返回同一批次（幂等）
with transaction() as conn:
    again = svc.open_trial(conn, OPERATOR, OpenTrial(band='BANK-T'))
check('重复开启不新建批次', again['code'] == run_code)

# 2. 两队各自记满网格，同格互不覆盖
for team, offset in (('NORTH', 0.0), ('SOUTH', 0.12)):
    for x, y, shade, spill in grid_values(offset):
        with transaction() as conn:
            svc.record_trial(conn, OPERATOR,
                             RecordTrial(band='BANK-T', team=team, x=x, y=y,
                                         shade=shade, spill=spill))
with transaction() as conn:
    n_cells = conn.execute(select(trial_cells)).mappings().all()
check('两队同格各存一行（共 2N 行）', len(n_cells) == 2 * N, f'got {len(n_cells)}')
# 同格读数不同，互不覆盖
with transaction() as conn:
    n0 = conn.execute(select(trial_cells).where(
        trial_cells.c.code == f'{run_code}-NORTH-0-0')).mappings().one()
    s0 = conn.execute(select(trial_cells).where(
        trial_cells.c.code == f'{run_code}-SOUTH-0-0')).mappings().one()
check('同格两队读数独立不覆盖', n0['shade'] != s0['shade'])

# 补测相同读数 -> 幂等返回，不报错也不产生重复
with transaction() as conn:
    before = len(conn.execute(select(trial_cells)).mappings().all())
    svc.record_trial(conn, OPERATOR, RecordTrial(
        band='BANK-T', team='NORTH', x=0, y=0, shade=n0['shade'], spill=n0['spill']))
    after = len(conn.execute(select(trial_cells)).mappings().all())
check('相同读数补测幂等', before == after)

# 3. 缺测时分簇被拒（构造一个新带，只填部分格）
with transaction() as conn:
    conn.execute(sculpture_bands.insert().values(
        code='BANK-X', title='缺测带', cols=3, rows=3, revision=0, scope='抽象几何雕塑'))
    svc.open_trial(conn, OPERATOR, OpenTrial(band='BANK-X'))
    svc.record_trial(conn, OPERATOR, RecordTrial(
        band='BANK-X', team='NORTH', x=0, y=0, shade=0.3, spill=0.7))
try:
    with transaction() as conn:
        svc.segment_trial(conn, OPERATOR, SegmentTrial(band='BANK-X', team='NORTH', clusters=2))
    check('缺测网格拒绝分簇', False)
except Exception as e:
    check('缺测网格拒绝分簇', '缺测' in str(e.detail if hasattr(e, 'detail') else e))

# 4. 两队分别分簇 + 封存
tokens = {}
for team in ('NORTH', 'SOUTH'):
    with transaction() as conn:
        queued = svc.segment_trial(conn, OPERATOR,
                                   SegmentTrial(band='BANK-T', team=team, clusters=3))
        tokens[team] = queued['token']
maps = {}
for team in ('NORTH', 'SOUTH'):
    with transaction() as conn:
        maps[team] = svc.pin_trial(conn, OPERATOR,
                                   PinTrial(band='BANK-T', team=team, token=tokens[team]))
check('两队各封存一张图谱', maps['NORTH'] is not None and maps['SOUTH'] is not None)
check('图谱布局覆盖整网格', len(maps['NORTH']['layout']) == N and len(maps['SOUTH']['layout']) == N)

# 5. 差异格对：非对称、且只在单队同簇
dn, ds = maps['NORTH']['diff_pairs'], maps['SOUTH']['diff_pairs']
check('差异格对为列表结构', isinstance(dn, list) and isinstance(ds, list))
if dn:
    pair = dn[0]
    check('差异对带簇号字段', all(k in pair for k in ('cell_a', 'cell_b', 'own_cluster',
                                                       'other_cluster_a', 'other_cluster_b')))
    # NORTH 同簇、SOUTH 不同簇
    south_cluster = {p['code']: p['cluster'] for p in maps['SOUTH']['layout']}
    north_cluster = {p['code']: p['cluster'] for p in maps['NORTH']['layout']}
    valid = (north_cluster[pair['cell_a']] == north_cluster[pair['cell_b']]
             and south_cluster[pair['cell_a']] != south_cluster[pair['cell_b']])
    check('NORTH 差异对：本队同簇、SOUTH 异簇', valid)

# 单队先封存时差异应为空（重建一个带验证）
with transaction() as conn:
    conn.execute(sculpture_bands.insert().values(
        code='BANK-Y', title='单队带', cols=3, rows=3, revision=0, scope='抽象几何雕塑'))
    svc.open_trial(conn, OPERATOR, OpenTrial(band='BANK-Y'))
    for x in range(3):
        for y in range(3):
            v = 0.2 + 0.3 * x
            svc.record_trial(conn, OPERATOR, RecordTrial(
                band='BANK-Y', team='NORTH', x=x, y=y, shade=v, spill=1 - v))
    q = svc.segment_trial(conn, OPERATOR, SegmentTrial(band='BANK-Y', team='NORTH', clusters=2))
    only = svc.pin_trial(conn, OPERATOR, PinTrial(band='BANK-Y', team='NORTH', token=q['token']))
check('仅一队封存时差异为空', only['diff_pairs'] == [])

# 6. 底图换版 -> 旧对照失效，需重新对照
with transaction() as conn:
    conn.execute(sculpture_bands.update().where(sculpture_bands.c.code == 'BANK-T')
                 .values(revision=1))
try:
    # 与 API 一致：先在独立事务提交旧批次失效，再在新事务尝试补测被拒
    with transaction() as conn:
        stale_codes, band_now = svc.sync_stale(conn, 'BANK-T')
    check('换版预同步识别出失效批次', run_code in stale_codes)
    with transaction() as conn:
        svc.record_trial(conn, OPERATOR, RecordTrial(
            band='BANK-T', team='NORTH', x=0, y=0, shade=0.5, spill=0.5), band=band_now)
    check('换版后补测被拒绝', False)
except Exception as e:
    msg = str(e.detail if hasattr(e, 'detail') else e)
    check('换版后补测被拒绝', '对照' in msg or '失效' in msg)
with transaction() as conn:
    stale = conn.execute(select(trial_runs).where(trial_runs.c.code == run_code)).mappings().one()
check('旧批次被标记底图失效', stale['status'] == '底图失效')
with transaction() as conn:
    new_run = svc.open_trial(conn, OPERATOR, OpenTrial(band='BANK-T'))
check('换版后可开启新对照批次', new_run['code'] == 'TRIAL-BANK-T-R1' and new_run['baseline_revision'] == 1)

# 7. 采纳流程：在新批次上重新记满、分簇、封存
for team, offset in (('NORTH', 0.0), ('SOUTH', 0.12)):
    for x, y, shade, spill in grid_values(offset):
        with transaction() as conn:
            svc.record_trial(conn, OPERATOR,
                             RecordTrial(band='BANK-T', team=team, x=x, y=y, shade=shade, spill=spill))
new_tokens = {}
for team in ('NORTH', 'SOUTH'):
    with transaction() as conn:
        new_tokens[team] = svc.segment_trial(
            conn, OPERATOR, SegmentTrial(band='BANK-T', team=team, clusters=3))['token']
for team in ('NORTH', 'SOUTH'):
    with transaction() as conn:
        svc.pin_trial(conn, OPERATOR, PinTrial(band='BANK-T', team=team, token=new_tokens[team]))

# 先放一张旧现用图，验证采纳时一次性切换
with transaction() as conn:
    conn.execute(shadow_plans.insert().values(
        code='MAP-OLD', band='BANK-T', revision=1, clusters=2, layout=[], evidence={},
        token=uuid.uuid4().hex, superseded=False))

# 只封存一队时不能采纳 —— 这里两队都已封存，先验证缺队拒绝：用 BANK-Y（仅 NORTH）
try:
    with transaction() as conn:
        svc.adopt_trial(conn, REVIEWER, AdoptTrial(
            band='BANK-Y', team='NORTH', plan_code='MAP-Y-1'))
    check('另一队未封存时拒绝采纳', False)
except Exception as e:
    check('另一队未封存时拒绝采纳', '两队' in str(e.detail if hasattr(e, 'detail') else e))

# 采纳 NORTH 整套
with transaction() as conn:
    adoption = svc.adopt_trial(conn, REVIEWER, AdoptTrial(
        band='BANK-T', team='NORTH', plan_code='MAP-BANK-T-TRIAL'))
check('采纳返回新归档图', adoption['plan'] == 'MAP-BANK-T-TRIAL' and adoption['retried'] is False)

with transaction() as conn:
    cur = conn.execute(select(shadow_plans).where(
        shadow_plans.c.code == 'MAP-BANK-T-TRIAL')).mappings().one()
    old = conn.execute(select(shadow_plans).where(
        shadow_plans.c.code == 'MAP-OLD')).mappings().one()
    run_after = conn.execute(select(trial_runs).where(
        trial_runs.c.code == new_run['code'])).mappings().one()
    check('新归档图为现用底图', cur['superseded'] is False)
    check('旧现用图被一次性置为历史', old['superseded'] is True)
    check('批次记录采纳队与归档图', run_after['status'] == '已采纳'
          and run_after['adopted_team'] == 'NORTH'
          and run_after['adopted_plan'] == 'MAP-BANK-T-TRIAL')
    check('归档图采用被采纳队的簇数', cur['clusters'] == 3)
    north_layout = {p['code']: p['cluster'] for p in
                    conn.execute(select(trial_maps).where(trial_maps.c.run == new_run['code'],
                                                          trial_maps.c.team == 'NORTH')).mappings().one()['layout']}
    cur_layout = {p['code']: p['cluster'] for p in cur['layout']}
    check('归档图布局等于被采纳队整套读数分簇', north_layout == cur_layout)

# 8. 采纳重试：同队不重复升版/建图；异队拒绝
with transaction() as conn:
    retry = svc.adopt_trial(conn, REVIEWER, AdoptTrial(
        band='BANK-T', team='NORTH', plan_code='MAP-BANK-T-TRIAL'))
check('同队采纳重试幂等且标记 retried', retry['retried'] is True and retry['plan'] == 'MAP-BANK-T-TRIAL')
try:
    with transaction() as conn:
        svc.adopt_trial(conn, REVIEWER, AdoptTrial(
            band='BANK-T', team='SOUTH', plan_code='MAP-OTHER'))
    check('已采纳后异队采纳被拒', False)
except Exception as e:
    check('已采纳后异队采纳被拒', '另一灯组' in str(e.detail if hasattr(e, 'detail') else e))
with transaction() as conn:
    plan_count = len(conn.execute(select(shadow_plans).where(
        shadow_plans.c.band == 'BANK-T')).mappings().all())
check('重试未产生重复归档图', plan_count == 2)  # MAP-OLD + MAP-BANK-T-TRIAL

# 9. 已结束批次不能再补测
try:
    with transaction() as conn:
        svc.record_trial(conn, OPERATOR, RecordTrial(
            band='BANK-T', team='NORTH', x=0, y=0, shade=0.9, spill=0.1))
    check('已采纳批次拒绝补测', False)
except Exception as e:
    check('已采纳批次拒绝补测', '结束' in str(e.detail if hasattr(e, 'detail') else e))

# 10. 两队分簇确有不同：差异格对非空、非对称且方向正确
with transaction() as conn:
    conn.execute(sculpture_bands.insert().values(
        code='BANK-D', title='差异带', cols=4, rows=3, revision=0, scope='抽象几何雕塑'))
    svc.open_trial(conn, OPERATOR, OpenTrial(band='BANK-D'))
    north_vals = {(x, y): round(0.2 + 0.6 * (x / 3) + 0.02 * y, 3)
                  for y in range(ROWS) for x in range(COLS)}
    south_vals = {(0, 0): 0.2, (1, 0): 0.277, (2, 0): 0.356, (3, 0): 0.8,
                  (0, 1): 0.22, (1, 1): 0.526, (2, 1): 0.321, (3, 1): 0.82,
                  (0, 2): 0.24, (1, 2): 0.465, (2, 2): 0.546, (3, 2): 0.84}
    for (x, y), shade in north_vals.items():
        svc.record_trial(conn, OPERATOR, RecordTrial(
            band='BANK-D', team='NORTH', x=x, y=y, shade=shade, spill=round(1 - shade, 3)))
    for (x, y), shade in south_vals.items():
        svc.record_trial(conn, OPERATOR, RecordTrial(
            band='BANK-D', team='SOUTH', x=x, y=y, shade=shade, spill=round(1 - shade, 3)))
    t_north = svc.segment_trial(conn, OPERATOR, SegmentTrial(band='BANK-D', team='NORTH', clusters=3))['token']
    t_south = svc.segment_trial(conn, OPERATOR, SegmentTrial(band='BANK-D', team='SOUTH', clusters=3))['token']
    svc.pin_trial(conn, OPERATOR, PinTrial(band='BANK-D', team='NORTH', token=t_north))
    svc.pin_trial(conn, OPERATOR, PinTrial(band='BANK-D', team='SOUTH', token=t_south))
    run_d = conn.execute(select(trial_runs).where(trial_runs.c.band == 'BANK-D')).mappings().one()['code']
    m_north = svc._team_map(conn, run_d, 'NORTH')
    m_south = svc._team_map(conn, run_d, 'SOUTH')

# 用 (x,y) 对齐两队各自的格编码，再比较簇归属
def cluster_by_xy(layout):
    return {(p['x'], p['y']): p['cluster'] for p in layout}
nc = cluster_by_xy(m_north['layout'])
sc = cluster_by_xy(m_south['layout'])
check('两队分簇结果确实不同', nc != sc)
check('NORTH 差异格对非空', len(m_north['diff_pairs']) > 0)
check('SOUTH 差异格对非空', len(m_south['diff_pairs']) > 0)
check('两视角差异格对数量不同（非对称）',
      len(m_north['diff_pairs']) != len(m_south['diff_pairs']),
      f"{len(m_north['diff_pairs'])} vs {len(m_south['diff_pairs'])}")
# 差异对里的格编码形如 TRIAL-BANK-D-R0-NORTH-x-y，末两段即列、行
def pos_of(code):
    tail = code.rsplit('-', 2)
    return int(tail[1]), int(tail[2])
north_ok = all(nc[pos_of(p['cell_a'])] == nc[pos_of(p['cell_b'])]
               and sc[pos_of(p['cell_a'])] != sc[pos_of(p['cell_b'])]
               for p in m_north['diff_pairs'])
south_ok = all(sc[pos_of(p['cell_a'])] == sc[pos_of(p['cell_b'])]
               and nc[pos_of(p['cell_a'])] != nc[pos_of(p['cell_b'])]
               for p in m_south['diff_pairs'])
check('NORTH 差异对方向正确', north_ok)
check('SOUTH 差异对方向正确', south_ok)

print()
if failures:
    print(f'{len(failures)} 项失败: {failures}')
    sys.exit(1)
print('全部断言通过')
