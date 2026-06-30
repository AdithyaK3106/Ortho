"""User management business logic."""

from packages.data.user_repo import UserRepository
from packages.data.order_repo import OrderRepository


class UserService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.order_repo = OrderRepository()

    def get_user(self, user_id: str):
        return self.user_repo.get(user_id)

    def create_user(self, name: str, email: str):
        return self.user_repo.create(name, email)

    def get_user_orders(self, user_id: str):
        return self.order_repo.get_by_user(user_id)

    def update_user(self, user_id: str, name: str):
        return self.user_repo.update(user_id, name)
