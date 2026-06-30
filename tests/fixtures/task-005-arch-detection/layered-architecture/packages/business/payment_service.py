"""Payment processing business logic."""

from packages.data.payment_repo import PaymentRepository
from packages.utils.logger import log


class PaymentService:
    def __init__(self):
        self.repo = PaymentRepository()

    def process_payment(self, user_id: str, amount: float):
        log(f"Processing payment: ${amount}")
        return self.repo.create(user_id, amount)

    def get_payment_history(self, user_id: str):
        return self.repo.get_by_user(user_id)

    def refund(self, payment_id: str):
        return self.repo.refund(payment_id)
