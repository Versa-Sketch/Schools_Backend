from rest_framework.response import Response
from core import constants


class ChangePasswordPresenter:
    def success(self):
        return Response({'success': True, 'message': constants.PASSWORD_CHANGED_SUCCESS}, status=200)
