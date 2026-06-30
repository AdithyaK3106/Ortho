"""Authentication business logic."""

from packages.data.user_repo import UserRepository
from packages.utils.logger import log


class AuthService:
    def __init__(self):
        self.repo = UserRepository()

    def authenticate(self, username: str, password: str):
        log(f"Authenticating {username}")
        user = self.repo.get_by_username(username)
        if user and user.check_password(password):
            return {"token": "abc123", "user_id": user.id}
        return None

    def validate_token(self, token: str):
        return token == "abc123"
