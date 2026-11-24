from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table, UniqueConstraint

from core.db import metadata


sight_cells = Table('sight_cells', metadata,
    Column('code', String(64), primary_key=True),
    Column('band', String(64), ForeignKey('sculpture_bands.code'), nullable=False),
    Column('x', Integer, nullable=False),
    Column('y', Integer, nullable=False),
    Column('shade', Float, nullable=False),
    Column('spill', Float, nullable=False),
    Column('owner', String(64), nullable=False),
    Column('protected', Boolean, nullable=False),
    UniqueConstraint('band', 'x', 'y'),
    CheckConstraint('x>=0'),
    CheckConstraint('y>=0'),
    CheckConstraint('shade between 0 and 1'),
    CheckConstraint('spill between 0 and 1'),
)
