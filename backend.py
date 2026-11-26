from fastapi import FastAPI, HTTPException, Query, Response, APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request

from mapper import grant_to_response
from schemas import (
    GrantCreateRequest,
    LoginRequest,
    ResearcherCreateRequest,
    ResearcherProfileRequest,
    ApplicationCreateRequest,
)
from service_impl import GrantServiceImpl, ServiceError

app = FastAPI(
    title="REST-сервис «Научные гранты»",
    version="3.0.0",
    description="Лабораторная работа №3. Разделение контроллеров, валидация, бизнес-правила."
)

service = GrantServiceImpl()


# --- Обработчики ошибок ---

@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Превращаем стандартный ответ Pydantic в понятное сообщение
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(x) for x in err["loc"] if x != "body")
        errors.append(f"{loc}: {err['msg']}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Ошибка валидации входных данных.", "errors": errors}
    )


# --- Контроллер: Проверка доступности ---

health_router = APIRouter(tags=["Сервис"])

@health_router.get("/api/health", summary="Проверка доступности сервиса")
def health_check():
    """Возвращает статус ok, если сервер запущен."""
    return {"status": "ok"}


# --- Контроллер: Аутентификация ---

auth_router = APIRouter(prefix="/api/auth", tags=["Аутентификация"])

@auth_router.post("/login", summary="Вход пользователя")
def login(data: LoginRequest):
    """
    Аутентификация по электронной почте и паролю.
    
    Возвращает данные пользователя (без пароля) или ошибку 401.
    """
    return service.login(data.email, data.password)


# --- Контроллер: Исследователи ---

researchers_router = APIRouter(prefix="/api/researchers", tags=["Исследователи"])

@researchers_router.post("", status_code=201, summary="Регистрация исследователя")
def register_researcher(data: ResearcherCreateRequest):
    """
    Регистрация нового исследователя.
    
    БП-01: обязательные поля ФИО, специальность, email, пароль.
    БП-07: email должен быть уникальным.
    """
    return service.register_researcher(data)


@researchers_router.put("/{user_id}/profile", summary="Изменение профиля исследователя")
def update_researcher_profile(user_id: int, data: ResearcherProfileRequest):
    """Обновление ФИО, специальности, степени и достижений."""
    return service.update_profile(user_id, data)


@researchers_router.get("", summary="Список исследователей")
def get_researchers():
    """Возвращает список всех зарегистрированных исследователей."""
    return service.list_researchers()


# --- Контроллер: Гранты ---

grants_router = APIRouter(prefix="/api/grants", tags=["Гранты"])

@grants_router.get("", summary="Список грантов и поиск")
def get_grants(search: str = Query(default="", description="Поисковый запрос по названию или направлению")):
    """
    Возвращает список грантов. Если указан `search` — фильтрует по названию или направлению.
    """
    return [grant_to_response(grant) for grant in service.find_grants(search)]


@grants_router.get("/{grant_id}", summary="Сведения о гранте")
def get_grant(grant_id: int):
    """Возвращает грант по ID или 404, если не найден."""
    return grant_to_response(service.find_grant(grant_id))


@grants_router.post("", status_code=201, summary="Добавление гранта")
def create_grant(data: GrantCreateRequest):
    """
    Создание нового гранта.
    
    БП-02: сумма > 0.
    БП-03: дата окончания не раньше даты начала.
    """
    return service.create_grant(data)


@grants_router.put("/{grant_id}", summary="Изменение гранта")
def update_grant(grant_id: int, data: GrantCreateRequest):
    """Обновление существующего гранта. Возвращает 404, если грант не найден."""
    return service.update_grant(grant_id, data)


# --- Контроллер: Заявки ---

applications_router = APIRouter(prefix="/api/applications", tags=["Заявки"])

@applications_router.post("", status_code=201, summary="Подача заявки")
def create_application(data: ApplicationCreateRequest, response: Response):
    """
    Подача заявки исследователя на грант.
    
    БП-04: грант должен быть активен.
    БП-05: специальность исследователя должна совпадать с направлением гранта.
    БП-06: нельзя подать повторную заявку на тот же грант.
    """
    result = service.create_application(data.researcher_id, data.grant_id)
    response.headers["Location"] = f"/api/applications/{result['id']}"
    return result


@applications_router.get("", summary="Список заявок")
def get_applications(
    researcher_id: int | None = Query(default=None, gt=0, description="Фильтр по ID исследователя")
):
    """Возвращает список заявок. Если указан `researcher_id` — только заявки этого исследователя."""
    return service.list_applications(researcher_id)


@applications_router.get("/{application_id}", summary="Сведения о заявке")
def get_application(application_id: int):
    """Возвращает заявку по ID или 404."""
    return service.find_application(application_id)


@applications_router.put("/{application_id}/status", summary="Изменение статуса заявки")
def update_application_status(
    application_id: int,
    status: str = Query(..., description="Новый статус: 'Одобрена' или 'Отклонена'")
):
    """
    Изменение статуса заявки администратором.
    
    БП-08: допустимы только статусы «Одобрена» и «Отклонена».
    Заявка должна быть в статусе «На рассмотрении».
    """
    return service.change_application_status(application_id, status)


# --- Подключаем все контроллеры ---

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(researchers_router)
app.include_router(grants_router)
app.include_router(applications_router)
