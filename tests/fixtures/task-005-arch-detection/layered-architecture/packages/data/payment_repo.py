"""Payment repository (data access)."""


class Payment:
    def __init__(self, id: str, user_id: str, amount: float):
        self.id = id
        self.user_id = user_id
        self.amount = amount


class PaymentRepository:
    def create(self, user_id: str, amount: float):
        return Payment("new", user_id, amount)

    def get_by_user(self, user_id: str):
        return [Payment("1", user_id, 100.0)]

    def refund(self, payment_id: str):
        return Payment(payment_id, "user1", -100.0)
