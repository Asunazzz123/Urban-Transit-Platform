from pydantic import BaseModel
from typing import List, Optional


class AskData(BaseModel):
    date: str
    departure: str
    destination: str
    highSpeed: bool
    studentTicket: bool
    askTime: int = None
    strictmode: bool = False


