from dataclasses import dataclass
from typing import List, Dict

@dataclass
class s:
    name: str
    dist_from_start: int
    charg: int

@dataclass
class R:
    sta_s: List[s]
    battery_range: int
    charge_time: int
    speed_p_min: float

@dataclass
class Bus:
    bus_id: str
    Oper: str
    Direction: str
    Depart_time: int

@dataclass
class Scenario:
    Scenario_name: str
    weights: Dict[str, float]
    routes: R
    buses: List[Bus]