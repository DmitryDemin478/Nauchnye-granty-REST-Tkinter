from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class Grant(BaseModel):
    id: int
    name: str
    description: str
    direction: str
    amount: float
    date_start: date
    date_end: date
    active: bool


GRANTS = [
    Grant(
        id=1,
        name="Исследование биоразнообразия Астраханской области",
        description="Изучение состояния и сохранения биоразнообразия региона.",
        direction="Биология",
        amount=450000.0,
        date_start=date(2026, 9, 1),
        date_end=date(2027, 8, 31),
        active=True,
    ),
    Grant(
        id=2,
        name="Разработка информационной системы для научных исследований",
        description="Создание программных средств для хранения и анализа научных данных.",
        direction="Информационные технологии",
        amount=700000.0,
        date_start=date(2026, 10, 1),
        date_end=date(2027, 9, 30),
        active=True,
    ),
    Grant(
        id=3,
        name="Историческое наследие Нижнего Поволжья",
        description="Исследование исторических источников и культурного наследия региона.",
        direction="История",
        amount=300000.0,
        date_start=date(2026, 6, 1),
        date_end=date(2027, 5, 31),
        active=False,
    ),
]

app = FastAPI(title="REST-сервис «Научные гранты»", version="2.0.0")


@app.get("/api/grants", response_model=list[Grant])
def get_grants(search: str = ""):
    query = search.strip().casefold()
    return [
        grant for grant in GRANTS
        if query in grant.name.casefold() or query in grant.direction.casefold()
    ]


@app.get("/api/grants/{grant_id}", response_model=Grant)
def get_grant(grant_id: str):
    try:
        wanted_id = int(grant_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="ID должен быть целым числом."
        )

    for grant in GRANTS:
        if grant.id == wanted_id:
            return grant

    raise HTTPException(status_code=404, detail="Грант не найден.")
