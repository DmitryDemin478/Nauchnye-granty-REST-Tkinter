from datetime import date, datetime
import hashlib
from models import Application, Grant, Researcher
from service import GrantService
from mapper import application_to_response, researcher_to_response


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class GrantServiceImpl(GrantService):
    def __init__(self):
        self.grants = {
            1: Grant(1, "Исследование биоразнообразия Астраханской области",
                     "Изучение состояния и сохранения биоразнообразия региона.",
                     "Биология", 450000.0, date(2026, 9, 1), date(2027, 8, 31), True),
            2: Grant(2, "Разработка информационной системы для научных исследований",
                     "Создание программных средств для хранения и анализа научных данных.",
                     "Информационные технологии", 700000.0, date(2026, 10, 1), date(2027, 9, 30), True),
            3: Grant(3, "Историческое наследие Нижнего Поволжья",
                     "Исследование исторических источников и культурного наследия региона.",
                     "История", 300000.0, date(2026, 6, 1), date(2027, 5, 31), False),
        }
        self.researchers = {
            1: Researcher(1, "Администратор", "Администрирование", "", "",
                          "admin@grant.ru", hash_password("admin123"), "Администратор")
        }
        self.applications = {}
        self.next_grant_id = 4
        self.next_researcher_id = 2
        self.next_application_id = 1

    def find_grants(self, search=""):
        query = search.strip().casefold()
        return [g for g in sorted(self.grants.values(), key=lambda x: x.id)
                if query in g.name.casefold() or query in g.direction.casefold()]

    def find_grant(self, grant_id):
        grant = self.grants.get(grant_id)
        if grant is None:
            raise ServiceError(404, "Грант не найден.")
        return grant

    def register_researcher(self, data):
        fio = data.fio.strip()
        specialty = data.specialty.strip()
        email = data.email.strip().lower()
        if not fio or not specialty or not email:
            raise ServiceError(400, "Для регистрации необходимо указать ФИО, специальность и адрес электронной почты.")
        if any(r.email == email for r in self.researchers.values()):
            raise ServiceError(409, "Пользователь с такой электронной почтой уже зарегистрирован.")
        researcher = Researcher(
            self.next_researcher_id, fio, specialty, data.degree.strip(),
            data.achievements.strip(), email, hash_password(data.password), "Исследователь"
        )
        self.researchers[researcher.id] = researcher
        self.next_researcher_id += 1
        return {"message": "Регистрация завершена.", "id": researcher.id}

    def login(self, email, password):
        email = email.strip().lower()
        for researcher in self.researchers.values():
            if researcher.email == email and researcher.password == hash_password(password):
                return researcher_to_response(researcher)
        raise ServiceError(401, "Неверная электронная почта или пароль.")

    def update_profile(self, researcher_id, data):
        researcher = self.researchers.get(researcher_id)
        if researcher is None or researcher.role != "Исследователь":
            raise ServiceError(404, "Исследователь не найден.")
        researcher.fio = data.fio.strip()
        researcher.specialty = data.specialty.strip()
        researcher.degree = data.degree.strip()
        researcher.achievements = data.achievements.strip()
        return researcher_to_response(researcher)

    def list_researchers(self):
        return [
            {"fio": r.fio, "specialty": r.specialty, "degree": r.degree,
             "achievements": r.achievements, "email": r.email}
            for r in sorted(self.researchers.values(), key=lambda x: x.fio.casefold())
            if r.role == "Исследователь"
        ]

    def create_grant(self, data):
        self._validate_grant(data)
        grant = Grant(self.next_grant_id, data.name.strip(), data.description.strip(),
                      data.direction.strip(), data.amount, data.date_start,
                      data.date_end, data.active)
        self.grants[grant.id] = grant
        self.next_grant_id += 1
        return {"id": grant.id, "message": "Грант добавлен."}

    def update_grant(self, grant_id, data):
        self._validate_grant(data)
        if grant_id not in self.grants:
            raise ServiceError(404, "Грант не найден.")
        self.grants[grant_id] = Grant(grant_id, data.name.strip(), data.description.strip(),
                                      data.direction.strip(), data.amount, data.date_start,
                                      data.date_end, data.active)
        return {"message": "Изменения сохранены."}

    @staticmethod
    def _validate_grant(data):
        if not data.name.strip() or not data.direction.strip():
            raise ServiceError(400, "Название и направление обязательны.")
        if data.amount <= 0:
            raise ServiceError(400, "Сумма гранта должна быть больше нуля.")
        if data.date_end < data.date_start:
            raise ServiceError(400, "Дата окончания не может быть раньше даты начала.")

    @staticmethod
    def _specialty_matches(specialty, direction):
        return specialty.strip().casefold().replace("ё", "е") == direction.strip().casefold().replace("ё", "е")

    def create_application(self, researcher_id, grant_id):
        researcher = self.researchers.get(researcher_id)
        grant = self.grants.get(grant_id)
        if researcher is None or researcher.role != "Исследователь":
            raise ServiceError(404, "Исследователь не найден.")
        if grant is None:
            raise ServiceError(404, "Грант не найден.")
        if not grant.active:
            raise ServiceError(400, "Подать заявку можно только на активный грант.")
        if not self._specialty_matches(researcher.specialty, grant.direction):
            raise ServiceError(400, "Специальность исследователя не соответствует направлению выбранного гранта.")
        if any(a.researcher_id == researcher_id and a.grant_id == grant_id
               for a in self.applications.values()):
            raise ServiceError(409, "Вы уже подавали заявку на этот грант.")
        application = Application(self.next_application_id, researcher_id, grant_id,
                                  "На рассмотрении", datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.applications[application.id] = application
        self.next_application_id += 1
        return {"message": "Заявка отправлена. Её статус: «На рассмотрении».",
                "id": application.id, "status": application.status}

    def find_application(self, application_id):
        application = self.applications.get(application_id)
        if application is None:
            raise ServiceError(404, "Заявка не найдена.")
        researcher = self.researchers.get(application.researcher_id)
        grant = self.grants.get(application.grant_id)
        return application_to_response(application, researcher, grant)

    def list_applications(self, researcher_id=None):
        result = []
        for application in sorted(self.applications.values(), key=lambda x: x.id, reverse=True):
            if researcher_id is not None and application.researcher_id != researcher_id:
                continue
            researcher = self.researchers.get(application.researcher_id)
            grant = self.grants.get(application.grant_id)
            if researcher and grant:
                result.append(application_to_response(application, researcher, grant))
        return result

    def change_application_status(self, application_id, status):
        if status not in ("Одобрена", "Отклонена"):
            raise ServiceError(400, "Недопустимый статус заявки.")
        application = self.applications.get(application_id)
        if application is None or application.status != "На рассмотрении":
            raise ServiceError(404, "Заявка не найдена или уже рассмотрена.")
        application.status = status
        return {"message": "Статус заявки изменён."}
