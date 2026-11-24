from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


sculpture_bands = Table('sculpture_bands', metadata,
    Column('code', String(64), primary_key=True),
    Column('title', String(160), nullable=False),
    Column('cols', Integer, nullable=False),
    Column('rows', Integer, nullable=False),
    Column('revision', Integer, nullable=False),
    Column('scope', String(160), nullable=False),
    CheckConstraint('cols between 3 and 12'),
    CheckConstraint('rows between 3 and 12'),
    CheckConstraint('revision>=0'),
)
