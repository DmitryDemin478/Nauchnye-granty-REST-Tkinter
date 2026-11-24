import unittest
from datetime import date
from pydantic import ValidationError
from schemas import GrantCreateRequest, ResearcherCreateRequest


class DtoValidationTests(unittest.TestCase):
    def test_required_researcher_fields(self):
        with self.assertRaises(ValidationError):
            ResearcherCreateRequest(fio="", specialty="Биология", email="ivan@example.ru", password="1234")

    def test_registration_cannot_assign_admin_role(self):
        with self.assertRaises(ValidationError):
            ResearcherCreateRequest(fio="Иванов", specialty="Биология", email="ivan@example.ru",
                                    password="1234", role="Администратор")

    def test_grant_amount_must_be_positive(self):
        with self.assertRaises(ValidationError):
            GrantCreateRequest(name="Грант", direction="Биология", amount=0,
                               date_start=date(2026, 1, 1), date_end=date(2026, 2, 1))

    def test_grant_end_date_must_not_precede_start_date(self):
        with self.assertRaises(ValidationError):
            GrantCreateRequest(name="Грант", direction="Биология", amount=100,
                               date_start=date(2026, 2, 1), date_end=date(2026, 1, 1))


if __name__ == "__main__":
    unittest.main()
