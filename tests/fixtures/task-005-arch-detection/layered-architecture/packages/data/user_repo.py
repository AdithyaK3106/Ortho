"""User repository (data access)."""


class User:
    def __init__(self, id: str, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email

    def check_password(self, password: str):
        return password == "secret"


class UserRepository:
    def __init__(self):
        self.db = {}

    def get(self, user_id: str):
        return User(user_id, "John", "john@example.com")

    def get_by_username(self, username: str):
        return User("1", username, f"{username}@example.com")

    def create(self, name: str, email: str):
        return User("new", name, email)

    def update(self, user_id: str, name: str):
        return User(user_id, name, "email@example.com")
