from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from mapper import grant_to_response
from schemas import (
    ApplicationCreateRequest,
    ApplicationStatusRequest,
    GrantCreateRequest,
    LoginRequest,
    ResearcherCreateRequest,
    ResearcherProfileRequest,
)
from service_impl import GrantServiceImpl, ServiceError

app = FastAPI(title="REST-сервис «Научные гранты»", version="3.0.0")
service = GrantServiceImpl()


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": "Проверьте переданные данные."})


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(data: LoginRequest):
    return service.login(data.email, data.password)


@app.post("/api/researchers", status_code=201)
def register_researcher(data: ResearcherCreateRequest):
    return service.register_researcher(data)


@app.put("/api/researchers/{user_id}/profile")
def update_researcher_profile(user_id: int, data: ResearcherProfileRequest):
    return service.update_profile(user_id, data)


@app.get("/api/researchers")
def get_researchers():
    return service.list_researchers()


@app.get("/api/grants")
def get_grants(search: str = ""):
    return [grant_to_response(grant) for grant in service.find_grants(search)]


@app.get("/api/grants/{grant_id}")
def get_grant(grant_id: str):
    try:
        wanted_id = int(grant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID должен быть целым числом.")
    return grant_to_response(service.find_grant(wanted_id))


@app.post("/api/grants", status_code=201)
def create_grant(data: GrantCreateRequest):
    return service.create_grant(data)


@app.put("/api/grants/{grant_id}")
def update_grant(grant_id: int, data: GrantCreateRequest):
    return service.update_grant(grant_id, data)


@app.post("/api/applications", status_code=201)
def create_application(data: ApplicationCreateRequest, response: Response):
    result = service.create_application(data.researcher_id, data.grant_id)
    response.headers["Location"] = f"/api/applications/{result['id']}"
    return result


@app.get("/api/applications")
def get_applications(researcher_id: int | None = Query(default=None, gt=0)):
    return service.list_applications(researcher_id)


@app.get("/api/applications/{application_id}")
def get_application(application_id: int):
    return service.find_application(application_id)


@app.put("/api/applications/{application_id}/status")
def update_application_status(application_id: int, status: str = Query(...)):
    return service.change_application_status(application_id, status)
