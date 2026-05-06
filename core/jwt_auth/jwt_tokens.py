from rest_framework_simplejwt.tokens import RefreshToken


class UserAuthentication:
    def create_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role
        refresh['email'] = user.email
        refresh['phone_number'] = user.phone_number
        refresh['user_id'] = str(user.id)

        access_token = refresh.access_token
        access_token['role'] = user.role
        access_token['email'] = user.email
        access_token['phone_number'] = user.phone_number
        access_token['user_id'] = str(user.id)

        return {
            'access': str(access_token),
            'refresh': str(refresh),
        }

    def refresh_access_token(self, refresh_token_str: str):
        refresh = RefreshToken(refresh_token_str)
        access_token = refresh.access_token
        access_token['role'] = refresh.get('role')
        access_token['email'] = refresh.get('email')
        access_token['phone_number'] = refresh.get('phone_number')
        access_token['user_id'] = refresh.get('user_id')
        return {
            'access': str(access_token),
        }

    def blacklist_refresh_token(self, refresh_token_str: str):
        refresh = RefreshToken(refresh_token_str)
        if hasattr(refresh, 'blacklist'):
            refresh.blacklist()
