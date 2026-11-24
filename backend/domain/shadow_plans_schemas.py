from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class SegmentBank(BaseModel):
    model_config = ConfigDict(extra="forbid")
    band: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    clusters: int


class PinMap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    token: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
