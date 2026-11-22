import unittest
from fastapi.testclient import TestClient
import backend
from service_impl import GrantServiceImpl


class ApiTests(unittest.TestCase):
    def setUp(self):
        backend.service = GrantServiceImpl()
        self.client = TestClient(backend.app)

    def test_existing_get_routes(self):
        self.assertEqual(self.client.get("/api/grants").status_code, 200)
        self.assertEqual(self.client.get("/api/grants?search=Биология").json()[0]["id"], 1)
        self.assertEqual(self.client.get("/api/grants/1").status_code, 200)
        self.assertEqual(self.client.get("/api/grants/999").status_code, 404)
        self.assertEqual(self.client.get("/api/grants/abc").status_code, 400)

    def test_create_and_read_application_with_location(self):
        registered = self.client.post("/api/researchers", json={
            "fio": "Иванов Иван", "specialty": "Биология", "email": "ivan@example.ru", "password": "1234"
        })
        self.assertEqual(registered.status_code, 201)
        response = self.client.post("/api/applications", json={
            "researcher_id": registered.json()["id"], "grant_id": 1
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["location"], f"/api/applications/{response.json()['id']}")
        read_back = self.client.get(response.headers["location"])
        self.assertEqual(read_back.status_code, 200)
        self.assertEqual(read_back.json()["status"], "На рассмотрении")

    def test_invalid_dto_returns_400_without_creating_application(self):
        before = self.client.get("/api/applications").json()
        response = self.client.post("/api/applications", json={"researcher_id": 0, "grant_id": 1})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/applications").json(), before)

    def test_duplicate_returns_409(self):
        user_id = self.client.post("/api/researchers", json={
            "fio": "Иванов Иван", "specialty": "Биология", "email": "ivan@example.ru", "password": "1234"
        }).json()["id"]
        payload = {"researcher_id": user_id, "grant_id": 1}
        self.assertEqual(self.client.post("/api/applications", json=payload).status_code, 201)
        self.assertEqual(self.client.post("/api/applications", json=payload).status_code, 409)


if __name__ == "__main__":
    unittest.main()
