from typing import Any
from dataclasses import dataclass


@dataclass
class Update:
    update_id: int
    payload: Any