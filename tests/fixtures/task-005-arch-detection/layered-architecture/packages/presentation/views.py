"""View serializers and template rendering."""

from packages.business.user_service import UserService


class UserView:
    def __init__(self):
        self.user_service = UserService()

    def render_user(self, user_id: str):
        user = self.user_service.get_user(user_id)
        return {"id": user.id, "name": user.name}

    def render_list(self, users):
        return [{"id": u.id, "name": u.name} for u in users]
