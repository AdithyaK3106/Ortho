"""Order management business logic."""

from packages.data.order_repo import OrderRepository
from packages.data.user_repo import UserRepository


class OrderService:
    def __init__(self):
        self.order_repo = OrderRepository()
        self.user_repo = UserRepository()

    def create_order(self, user_id: str, items):
        user = self.user_repo.get(user_id)
        if not user:
            return None
        return self.order_repo.create(user_id, items)

    def get_order(self, order_id: str):
        return self.order_repo.get(order_id)

    def list_orders(self, user_id: str):
        return self.order_repo.get_by_user(user_id)
