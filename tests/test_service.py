import unittest
from datetime import date
from types import SimpleNamespace

from schemas import GrantCreateRequest, ResearcherCreateRequest
from service_impl import GrantServiceImpl, ServiceError


class GrantServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = GrantServiceImpl()
        self.researcher = ResearcherCreateRequest(
            fio="Иванов Иван Иванович", specialty="Биология", degree="Кандидат наук",
            achievements="Публикации", email="ivan@example.ru", password="1234"
        )
        self.researcher_id = self.service.register_researcher(self.researcher)["id"]

    def test_bp01_registration_requires_fio_specialty_email(self):
        with self.assertRaises(Exception):
            ResearcherCreateRequest(fio="", specialty="Биология", email="ivan@example.ru", password="1234")

    def test_bp02_grant_amount_must_be_positive(self):
        with self.assertRaises(Exception):
            GrantCreateRequest(name="Грант", direction="Биология", amount=0,
                               date_start=date(2026, 1, 1), date_end=date(2026, 2, 1))

    def test_bp03_end_date_cannot_precede_start_date(self):
        with self.assertRaises(Exception):
            GrantCreateRequest(name="Грант", direction="Биология", amount=100,
                               date_start=date(2026, 2, 1), date_end=date(2026, 1, 1))

    def test_bp04_only_active_grant_accepts_application(self):
        with self.assertRaises(ServiceError) as ctx:
            self.service.create_application(self.researcher_id, 3)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_bp05_specialty_must_match_direction(self):
        with self.assertRaises(ServiceError) as ctx:
            self.service.create_application(self.researcher_id, 2)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_bp06_duplicate_application_is_rejected(self):
        self.service.create_application(self.researcher_id, 1)
        with self.assertRaises(ServiceError) as ctx:
            self.service.create_application(self.researcher_id, 1)
        self.assertEqual(ctx.exception.status_code, 409)

    def test_bp07_application_status_and_admin_decision(self):
        created = self.service.create_application(self.researcher_id, 1)
        self.assertEqual(created["status"], "На рассмотрении")
        self.service.change_application_status(created["id"], "Одобрена")
        self.assertEqual(self.service.find_application(created["id"])["status"], "Одобрена")

    def test_bp08_registration_assigns_researcher_role(self):
        user = self.service.login("ivan@example.ru", "1234")
        self.assertEqual(user["role"], "Исследователь")
        admin = self.service.login("admin@grant.ru", "admin123")
        self.assertEqual(admin["role"], "Администратор")

    def test_bp07_application_can_be_rejected(self):
        created = self.service.create_application(self.researcher_id, 1)
        self.service.change_application_status(created["id"], "Отклонена")
        self.assertEqual(self.service.find_application(created["id"])["status"], "Отклонена")

    def test_existing_grant_list_and_search(self):
        self.assertEqual(len(self.service.find_grants()), 3)
        self.assertEqual([g.id for g in self.service.find_grants("Биология")], [1])

    def test_state_is_reset_after_new_service_instance(self):
        self.service.create_application(self.researcher_id, 1)
        new_service = GrantServiceImpl()
        self.assertEqual(new_service.list_applications(), [])
        self.assertEqual(len(new_service.find_grants()), 3)


if __name__ == "__main__":
    unittest.main()
