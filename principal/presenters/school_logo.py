from rest_framework.response import Response


class SchoolLogoPresenter:
    def success(self, logo_url):
        return Response({'logo': logo_url}, status=200)
