from rest_framework.response import Response
from core import constants

class LogoutPresenter:
    def success(self):
        payload = {
            'success': True,
            'code': constants.SUCCESS,
            'details': constants.LOGOUT_SUCCESS,
        }
        return Response(payload, status=200)
