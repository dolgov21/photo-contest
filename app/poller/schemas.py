from dataclasses import dataclass
from typing import Any


@dataclass
class Update:
    update_id: int
    payload: Any