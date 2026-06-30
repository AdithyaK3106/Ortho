"""HTTP handlers for user endpoints."""

from packages.business.auth_service import AuthService
from packages.business.user_service import UserService


class UserHandler:
    def __init__(self):
        self.auth = AuthService()
        self.user = UserService()

    def get_user(self, user_id: str):
        return self.user.get_user(user_id)

    def create_user(self, name: str, email: str):
        return self.user.create_user(name, email)

    def authenticate(self, username: str, password: str):
        return self.auth.authenticate(username, password)
