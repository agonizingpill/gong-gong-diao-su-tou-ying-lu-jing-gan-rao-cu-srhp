from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

BandRef = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
CodeRef = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Team = Literal['NORTH', 'SOUTH']


class OpenTrial(BaseModel):
    model_config = ConfigDict(extra="forbid")
    band: BandRef


class RecordTrial(BaseModel):
    model_config = ConfigDict(extra="forbid")
    band: BandRef
    team: Team
    x: int
    y: int
    shade: FiniteFloat
    spill: FiniteFloat


class SegmentTrial(BaseModel):
    model_config = ConfigDict(extra="forbid")
    band: BandRef
    team: Team
    clusters: int


class PinTrial(BaseModel):
    model_config = ConfigDict(extra="forbid")
    band: BandRef
    team: Team
    token: CodeRef


class AdoptTrial(BaseModel):
    model_config = ConfigDict(extra="forbid")
    band: BandRef
    team: Team
    plan_code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
