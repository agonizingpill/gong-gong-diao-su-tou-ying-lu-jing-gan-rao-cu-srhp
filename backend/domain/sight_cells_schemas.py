from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class RecordBeam(BaseModel):
    model_config = ConfigDict(extra="forbid")
    band: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    x: int
    y: int
    shade: FiniteFloat
    spill: FiniteFloat


class ProtectStation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
