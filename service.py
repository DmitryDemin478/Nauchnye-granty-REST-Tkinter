from abc import ABC, abstractmethod


class GrantService(ABC):
    @abstractmethod
    def find_grants(self, search: str = ""):
        raise NotImplementedError

    @abstractmethod
    def find_grant(self, grant_id: int):
        raise NotImplementedError

    @abstractmethod
    def register_researcher(self, data):
        raise NotImplementedError

    @abstractmethod
    def login(self, email: str, password: str):
        raise NotImplementedError

    @abstractmethod
    def update_profile(self, researcher_id: int, data):
        raise NotImplementedError

    @abstractmethod
    def list_researchers(self):
        raise NotImplementedError

    @abstractmethod
    def create_grant(self, data):
        raise NotImplementedError

    @abstractmethod
    def update_grant(self, grant_id: int, data):
        raise NotImplementedError

    @abstractmethod
    def create_application(self, researcher_id: int, grant_id: int):
        raise NotImplementedError

    @abstractmethod
    def find_application(self, application_id: int):
        raise NotImplementedError

    @abstractmethod
    def list_applications(self, researcher_id=None):
        raise NotImplementedError

    @abstractmethod
    def change_application_status(self, application_id: int, status: str):
        raise NotImplementedError
