from rest_framework.response import Response
from .common import format_user

class LoginPresenter:
    def success(self, tokens, user, profile):
        payload = {
            'success': True,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': format_user(user, profile),
        }
        return Response(payload, status=200)
