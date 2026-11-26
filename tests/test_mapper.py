import unittest
from datetime import date
from models import Grant
from mapper import grant_to_response


class MapperTests(unittest.TestCase):
    def test_grant_is_converted_to_response_dto(self):
        grant = Grant(4, "Новый грант", "Описание", "Биология", 1000,
                      date(2026, 1, 1), date(2026, 12, 31), True)
        response = grant_to_response(grant)
        self.assertEqual(response.id, 4)
        self.assertEqual(response.name, "Новый грант")
        self.assertEqual(response.direction, "Биология")


if __name__ == "__main__":
    unittest.main()
