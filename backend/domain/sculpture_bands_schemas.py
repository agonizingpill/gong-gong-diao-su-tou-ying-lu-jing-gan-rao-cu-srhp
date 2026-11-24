from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class BookBand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    cols: int
    rows: int
    scope: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
