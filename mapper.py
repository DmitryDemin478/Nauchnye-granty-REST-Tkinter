from models import Application, Grant, Researcher
from schemas import GrantResponse


def grant_to_response(grant: Grant) -> GrantResponse:
    return GrantResponse(
        id=grant.id,
        name=grant.name,
        description=grant.description,
        direction=grant.direction,
        amount=grant.amount,
        date_start=grant.date_start,
        date_end=grant.date_end,
        active=grant.active,
    )


def researcher_to_response(researcher: Researcher) -> dict:
    return {
        "id": researcher.id,
        "fio": researcher.fio,
        "specialty": researcher.specialty,
        "degree": researcher.degree,
        "achievements": researcher.achievements,
        "email": researcher.email,
        "role": researcher.role,
    }


def application_to_response(application: Application, researcher: Researcher, grant: Grant) -> dict:
    return {
        "id": application.id,
        "researcher": researcher.fio,
        "grant": grant.name,
        "status": application.status,
        "date": application.created_at,
    }
