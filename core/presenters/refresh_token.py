from rest_framework.response import Response

class RefreshTokenPresenter:
    def success(self, tokens):
        payload = {
            'success': True,
            'access': tokens['access'],
        }
        return Response(payload, status=200)
