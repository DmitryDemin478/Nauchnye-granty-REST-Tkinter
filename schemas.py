from datetime import date
from pydantic import BaseModel, ConfigDict, Field, field_validator


class GrantCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1)
    description: str = ""
    direction: str = Field(min_length=1)
    amount: float = Field(gt=0)
    date_start: date
    date_end: date
    active: bool = True

    @field_validator("date_end")
    @classmethod
    def validate_dates(cls, value, info):
        start = info.data.get("date_start")
        if start is not None and value < start:
            raise ValueError("Дата окончания не может быть раньше даты начала.")
        return value


class GrantResponse(BaseModel):
    id: int
    name: str
    description: str
    direction: str
    amount: float
    date_start: date
    date_end: date
    active: bool


class ResearcherCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    fio: str = Field(min_length=1)
    specialty: str = Field(min_length=1)
    degree: str = ""
    achievements: str = ""
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Укажите корректный адрес электронной почты.")
        return value.lower()


class ResearcherProfileRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    fio: str = Field(min_length=1)
    specialty: str = Field(min_length=1)
    degree: str = ""
    achievements: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class ApplicationCreateRequest(BaseModel):
    researcher_id: int = Field(gt=0)
    grant_id: int = Field(gt=0)


class ApplicationStatusRequest(BaseModel):
    status: str = Field(min_length=1)
