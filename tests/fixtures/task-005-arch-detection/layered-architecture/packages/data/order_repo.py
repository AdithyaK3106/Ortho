"""Order repository (data access)."""


class Order:
    def __init__(self, id: str, user_id: str, items):
        self.id = id
        self.user_id = user_id
        self.items = items


class OrderRepository:
    def get(self, order_id: str):
        return Order(order_id, "user1", [])

    def get_by_user(self, user_id: str):
        return [Order("1", user_id, []), Order("2", user_id, [])]

    def create(self, user_id: str, items):
        return Order("new", user_id, items)
