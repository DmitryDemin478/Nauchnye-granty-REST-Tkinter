from dataclasses import dataclass
from datetime import date


@dataclass
class Grant:
    id: int
    name: str
    description: str
    direction: str
    amount: float
    date_start: date
    date_end: date
    active: bool


@dataclass
class Researcher:
    id: int
    fio: str
    specialty: str
    degree: str
    achievements: str
    email: str
    password: str
    role: str = "Исследователь"


@dataclass
class Application:
    id: int
    researcher_id: int
    grant_id: int
    status: str
    created_at: str
