from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


light_handoffs = Table('light_handoffs', metadata,
    Column('code', String(64), primary_key=True),
    Column('plan', String(64), ForeignKey('shadow_plans.code'), nullable=False),
    Column('cell', String(64), ForeignKey('sight_cells.code'), nullable=False),
    Column('cluster', Integer, nullable=False),
    Column('source', String(64), nullable=False),
    Column('target', String(64), nullable=False),
    Column('status', String(160), nullable=False),
    Column('first_sign', String(64), nullable=False),
    Column('second_sign', String(64), nullable=True),
    CheckConstraint("status in ('待二签','已移交','版本失效')"),
    CheckConstraint('source<>target'),
)
