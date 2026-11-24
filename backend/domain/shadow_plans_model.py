from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


shadow_plans = Table('shadow_plans', metadata,
    Column('code', String(64), primary_key=True),
    Column('band', String(64), ForeignKey('sculpture_bands.code'), nullable=False),
    Column('revision', Integer, nullable=False),
    Column('clusters', Integer, nullable=False),
    Column('layout', JSON, nullable=False),
    Column('evidence', JSON, nullable=False),
    Column('token', String(64), nullable=False, unique=True),
    CheckConstraint('revision>=0'),
    CheckConstraint('clusters between 2 and 4'),
)
