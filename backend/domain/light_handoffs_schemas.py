from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class OfferStation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    plan: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    cell: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    target: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class CheckStation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
