from rest_framework.response import Response


class ProfilePicPresenter:
    def profile_pic_success(self, url):
        return Response({'profile_pic_url': url}, status=200)
