from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table, UniqueConstraint

from core.db import metadata


# 一次双队试投对照：两队在同一投影带、同一封存底图版本上各自记满同一网格。
trial_runs = Table('trial_runs', metadata,
    Column('code', String(64), primary_key=True),
    Column('band', String(64), ForeignKey('sculpture_bands.code'), nullable=False),
    Column('baseline_revision', Integer, nullable=False),
    Column('status', String(32), nullable=False),
    Column('sealed_by', String(100), nullable=False),
    Column('adopted_team', String(16), nullable=True),
    Column('adopted_plan', String(64), ForeignKey('shadow_plans.code'), nullable=True),
    UniqueConstraint('band', 'baseline_revision'),
    CheckConstraint('baseline_revision>=0'),
    CheckConstraint("status in ('对照中','已采纳','底图失效')"),
    CheckConstraint("adopted_team is null or adopted_team in ('NORTH','SOUTH')"),
)


# 某队在某次对照中的逐格读数。两队同格各存一行，互不覆盖。
trial_cells = Table('trial_cells', metadata,
    Column('code', String(80), primary_key=True),
    Column('run', String(64), ForeignKey('trial_runs.code'), nullable=False),
    Column('team', String(16), nullable=False),
    Column('x', Integer, nullable=False),
    Column('y', Integer, nullable=False),
    Column('shade', Float, nullable=False),
    Column('spill', Float, nullable=False),
    UniqueConstraint('run', 'team', 'x', 'y'),
    CheckConstraint("team in ('NORTH','SOUTH')"),
    CheckConstraint('x>=0'),
    CheckConstraint('y>=0'),
    CheckConstraint('shade between 0 and 1'),
    CheckConstraint('spill between 0 and 1'),
)


# 某队分簇并封存的图谱，含与另一队相比仅本队同簇的格对。
trial_maps = Table('trial_maps', metadata,
    Column('code', String(80), primary_key=True),
    Column('run', String(64), ForeignKey('trial_runs.code'), nullable=False),
    Column('team', String(16), nullable=False),
    Column('clusters', Integer, nullable=False),
    Column('revision', Integer, nullable=False),
    Column('layout', JSON, nullable=False),
    Column('evidence', JSON, nullable=False),
    Column('diff_pairs', JSON, nullable=False),
    Column('token', String(64), nullable=False, unique=True),
    UniqueConstraint('run', 'team'),
    CheckConstraint("team in ('NORTH','SOUTH')"),
    CheckConstraint('clusters between 2 and 4'),
    CheckConstraint('revision>=0'),
)
