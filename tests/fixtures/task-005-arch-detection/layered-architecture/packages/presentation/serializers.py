"""JSON serializers."""

from packages.business.user_service import UserService


def serialize_user(user_id: str):
    service = UserService()
    user = service.get_user(user_id)
    return {"id": user.id, "name": user.name, "email": user.email}
