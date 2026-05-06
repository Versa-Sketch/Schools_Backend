from rest_framework.response import Response
from .common import format_user, format_profile

class CurrentUserPresenter:
    def success(self, user, profile):
        payload = {
            'success': True,
            'user': format_user(user, profile),
            'profile': format_profile(profile),
        }
        return Response(payload, status=200)
