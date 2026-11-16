import sqlite3
import hashlib
import re
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DB_NAME = Path(__file__).with_name("nauchnye_granty.db")
ADMIN_EMAIL = "admin@grant.ru"
ADMIN_PASSWORD = "admin123"

app = FastAPI(title="REST-сервис «Научные гранты»", version="1.0.0")


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT NOT NULL, specialty TEXT NOT NULL, degree TEXT,
            achievements TEXT, email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL, role TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS grants (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            description TEXT, direction TEXT NOT NULL, amount REAL NOT NULL,
            date_start TEXT NOT NULL, date_end TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            researcher_id INTEGER NOT NULL, grant_id INTEGER NOT NULL,
            status TEXT NOT NULL, created_at TEXT NOT NULL,
            UNIQUE(researcher_id, grant_id),
            FOREIGN KEY(researcher_id) REFERENCES users(id),
            FOREIGN KEY(grant_id) REFERENCES grants(id))""")
        admin = conn.execute("SELECT id FROM users WHERE email=?", (ADMIN_EMAIL,)).fetchone()
        if admin is None:
            conn.execute("""INSERT INTO users
                (fio, specialty, degree, achievements, email, password, role)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("Администратор", "Администрирование", "", "", ADMIN_EMAIL,
                 hash_password(ADMIN_PASSWORD), "Администратор"))
        count = conn.execute("SELECT COUNT(*) AS n FROM grants").fetchone()["n"]
        if count == 0:
            conn.executemany("""INSERT INTO grants
                (name, description, direction, amount, date_start, date_end, active)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", [
                ("Исследование биоразнообразия Астраханской области",
                 "Изучение состояния и сохранения биоразнообразия региона.",
                 "Биология", 450000, "2026-09-01", "2027-08-31", 1),
                ("Разработка информационной системы для научных исследований",
                 "Создание программных средств для хранения и анализа научных данных.",
                 "Информационные технологии", 700000, "2026-10-01", "2027-09-30", 1),
                ("Историческое наследие Нижнего Поволжья",
                 "Исследование исторических источников и культурного наследия региона.",
                 "История", 300000, "2026-06-01", "2027-05-31", 0)
            ])


def specialty_matches(specialty, direction):
    s = specialty.lower().replace("ё", "е")
    d = direction.lower().replace("ё", "е")
    groups = [
        {"биология", "биолог", "биотехнолог", "экология", "медицина"},
        {"информацион", "информационные технологии", "ит", "программирован", "компьютер", "информатика"},
        {"история", "истор", "археология"},
        {"физика", "физик"}, {"химия", "химик"},
        {"экономика", "экономист"},
        {"педагогика", "педагог", "образование"}
    ]
    for group in groups:
        if any(x in s for x in group) and any(x in d for x in group):
            return True
    stop = {"научный", "научная", "исследование", "исследования", "и", "по", "в", "для"}
    sw = {w for w in re.findall(r"[а-яa-z]+", s) if len(w) > 3 and w not in stop}
    dw = {w for w in re.findall(r"[а-яa-z]+", d) if len(w) > 3 and w not in stop}
    return bool(sw & dw)


class LoginData(BaseModel):
    email: str
    password: str


class RegisterData(BaseModel):
    fio: str
    specialty: str
    degree: str = ""
    achievements: str = ""
    email: str
    password: str


class GrantData(BaseModel):
    name: str
    description: str = ""
    direction: str
    amount: float
    date_start: str
    date_end: str
    active: bool = True


class ProfileData(BaseModel):
    fio: str
    specialty: str
    degree: str = ""
    achievements: str = ""


class ApplicationData(BaseModel):
    researcher_id: int
    grant_id: int


def user_dict(row):
    return {k: row[k] for k in ("id", "fio", "specialty", "degree", "achievements", "email", "role")}


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Научные гранты"}


@app.post("/api/auth/login")
def login(data: LoginData):
    with connect_db() as conn:
        row = conn.execute("""SELECT * FROM users
            WHERE email=? AND password=?""",
            (data.email.strip().lower(), hash_password(data.password))).fetchone()
    if row is None:
        raise HTTPException(401, "Неверная электронная почта или пароль.")
    return user_dict(row)


@app.post("/api/researchers")
def register(data: RegisterData):
    fio, specialty, email = data.fio.strip(), data.specialty.strip(), data.email.strip().lower()
    if not fio or not specialty or not email or not data.password:
        raise HTTPException(400, "Заполните обязательные поля.")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Укажите корректный адрес электронной почты.")
    if len(data.password) < 4:
        raise HTTPException(400, "Пароль должен содержать не менее 4 символов.")
    try:
        with connect_db() as conn:
            cur = conn.execute("""INSERT INTO users
                (fio, specialty, degree, achievements, email, password, role)
                VALUES (?, ?, ?, ?, ?, ?, 'Исследователь')""",
                (fio, specialty, data.degree.strip(), data.achievements.strip(),
                 email, hash_password(data.password)))
            user_id = cur.lastrowid
        return {"message": "Регистрация завершена.", "id": user_id}
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Пользователь с такой электронной почтой уже зарегистрирован.")


@app.put("/api/researchers/{user_id}/profile")
def update_profile(user_id: int, data: ProfileData):
    if not data.fio.strip() or not data.specialty.strip():
        raise HTTPException(400, "ФИО и специальность обязательны.")
    with connect_db() as conn:
        cur = conn.execute("""UPDATE users SET fio=?, specialty=?, degree=?, achievements=?
            WHERE id=? AND role='Исследователь'""",
            (data.fio.strip(), data.specialty.strip(), data.degree.strip(),
             data.achievements.strip(), user_id))
        if cur.rowcount == 0:
            raise HTTPException(404, "Исследователь не найден.")
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return user_dict(row)


@app.get("/api/grants")
def get_grants(search: str = ""):
    with connect_db() as conn:
        rows = conn.execute("""SELECT id, name, direction, amount, date_start,
            date_end, active FROM grants
            WHERE name LIKE ? OR direction LIKE ? ORDER BY id""",
            (f"%{search}%", f"%{search}%")).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/grants/{grant_id}")
def get_grant(grant_id: int):
    with connect_db() as conn:
        row = conn.execute("SELECT * FROM grants WHERE id=?", (grant_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Грант не найден.")
    return dict(row)


@app.post("/api/grants")
def create_grant(data: GrantData):
    validate_grant(data)
    with connect_db() as conn:
        cur = conn.execute("""INSERT INTO grants
            (name, description, direction, amount, date_start, date_end, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (data.name.strip(), data.description.strip(), data.direction.strip(),
             data.amount, data.date_start, data.date_end, int(data.active)))
        return {"id": cur.lastrowid, "message": "Грант добавлен."}


@app.put("/api/grants/{grant_id}")
def update_grant(grant_id: int, data: GrantData):
    validate_grant(data)
    with connect_db() as conn:
        cur = conn.execute("""UPDATE grants SET name=?, description=?, direction=?,
            amount=?, date_start=?, date_end=?, active=? WHERE id=?""",
            (data.name.strip(), data.description.strip(), data.direction.strip(),
             data.amount, data.date_start, data.date_end, int(data.active), grant_id))
        if cur.rowcount == 0:
            raise HTTPException(404, "Грант не найден.")
    return {"message": "Изменения сохранены."}


def validate_grant(data):
    if not data.name.strip() or not data.direction.strip():
        raise HTTPException(400, "Название и направление обязательны.")
    if data.amount <= 0:
        raise HTTPException(400, "Сумма гранта должна быть больше нуля.")
    try:
        start = datetime.strptime(data.date_start, "%Y-%m-%d").date()
        end = datetime.strptime(data.date_end, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "Даты указываются в формате ГГГГ-ММ-ДД.")
    if end < start:
        raise HTTPException(400, "Дата окончания не может быть раньше даты начала.")


@app.post("/api/applications")
def submit_application(data: ApplicationData):
    with connect_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id=? AND role='Исследователь'",
                            (data.researcher_id,)).fetchone()
        grant = conn.execute("SELECT * FROM grants WHERE id=?", (data.grant_id,)).fetchone()
        if user is None:
            raise HTTPException(404, "Исследователь не найден.")
        if grant is None:
            raise HTTPException(404, "Грант не найден.")
        if not grant["active"]:
            raise HTTPException(400, "Подать заявку можно только на активный грант.")
        if not specialty_matches(user["specialty"], grant["direction"]):
            raise HTTPException(400, "Специальность исследователя не соответствует направлению выбранного гранта.")
        try:
            conn.execute("""INSERT INTO applications
                (researcher_id, grant_id, status, created_at)
                VALUES (?, ?, 'На рассмотрении', ?)""",
                (data.researcher_id, data.grant_id, datetime.now().strftime("%Y-%m-%d %H:%M")))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Вы уже подавали заявку на этот грант.")
    return {"message": "Заявка отправлена. Её статус: «На рассмотрении»."}


@app.get("/api/applications")
def get_applications(researcher_id: int | None = None):
    sql = """SELECT a.id, u.fio AS researcher, g.name AS grant,
        a.status, a.created_at AS date
        FROM applications a JOIN users u ON u.id=a.researcher_id
        JOIN grants g ON g.id=a.grant_id"""
    params = ()
    if researcher_id is not None:
        sql += " WHERE a.researcher_id=?"
        params = (researcher_id,)
    sql += " ORDER BY a.id DESC"
    with connect_db() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


@app.put("/api/applications/{application_id}/status")
def change_application_status(application_id: int, status: str):
    if status not in ("Одобрена", "Отклонена"):
        raise HTTPException(400, "Недопустимый статус заявки.")
    with connect_db() as conn:
        cur = conn.execute("""UPDATE applications SET status=?
            WHERE id=? AND status='На рассмотрении'""", (status, application_id))
        if cur.rowcount == 0:
            raise HTTPException(404, "Заявка не найдена или уже рассмотрена.")
    return {"message": "Статус заявки изменён."}


@app.get("/api/researchers")
def get_researchers():
    with connect_db() as conn:
        rows = conn.execute("""SELECT fio, specialty, degree, achievements, email
            FROM users WHERE role='Исследователь' ORDER BY fio""").fetchall()
    return [dict(r) for r in rows]
