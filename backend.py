from fastapi import FastAPI, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from mapper import grant_to_response
from schemas import (ApplicationCreateRequest, GrantCreateRequest, GrantResponse, LoginRequest,
                     ResearcherCreateRequest, ResearcherProfileRequest)
from service_impl import GrantServiceImpl, ServiceError

app = FastAPI(title="REST-сервис «Научные гранты»", version="3.0.0")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    messages = [item.get("msg", "Некорректные данные.") for item in exc.errors()]
    return JSONResponse(status_code=400, content={"detail": messages})
service = GrantServiceImpl()


def handle_error(error: ServiceError):
    raise HTTPException(status_code=error.status_code, detail=error.detail)


@app.get("/api/grants", response_model=list[GrantResponse])
def get_grants(search: str = ""):
    return [grant_to_response(g) for g in service.find_grants(search)]


@app.get("/api/grants/{grant_id}")
def get_grant(grant_id: str):
    try:
        wanted_id = int(grant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID должен быть целым числом.")
    try:
        return grant_to_response(service.find_grant(wanted_id))
    except ServiceError as error:
        handle_error(error)


@app.post("/api/auth/login")
def login(data: LoginRequest):
    try:
        return service.login(data.email, data.password)
    except ServiceError as error:
        handle_error(error)


@app.post("/api/researchers", status_code=201)
def register(data: ResearcherCreateRequest):
    try:
        return service.register_researcher(data)
    except ServiceError as error:
        handle_error(error)


@app.put("/api/researchers/{user_id}/profile")
def update_profile(user_id: int, data: ResearcherProfileRequest):
    try:
        return service.update_profile(user_id, data)
    except ServiceError as error:
        handle_error(error)


@app.get("/api/researchers")
def get_researchers():
    return service.list_researchers()


@app.post("/api/grants", status_code=201)
def create_grant(data: GrantCreateRequest):
    try:
        return service.create_grant(data)
    except ServiceError as error:
        handle_error(error)


@app.put("/api/grants/{grant_id}")
def update_grant(grant_id: int, data: GrantCreateRequest):
    try:
        return service.update_grant(grant_id, data)
    except ServiceError as error:
        handle_error(error)


@app.post("/api/applications", status_code=201)
def submit_application(data: ApplicationCreateRequest, response: Response):
    try:
        result = service.create_application(data.researcher_id, data.grant_id)
        response.headers["Location"] = f"/api/applications/{result['id']}"
        return result
    except ServiceError as error:
        handle_error(error)


@app.get("/api/applications/{application_id}")
def get_application(application_id: int):
    try:
        return service.find_application(application_id)
    except ServiceError as error:
        handle_error(error)


@app.get("/api/applications")
def get_applications(researcher_id: int | None = None):
    return service.list_applications(researcher_id)


@app.put("/api/applications/{application_id}/status")
def change_application_status(application_id: int, status: str):
    try:
        return service.change_application_status(application_id, status)
    except ServiceError as error:
        handle_error(error)
