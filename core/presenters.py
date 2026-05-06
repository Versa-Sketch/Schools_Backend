from . import constants


class CommonErrorPresenter:
    def error(self, exception):
        return {
            'success': False,
            'code': exception.code,
            'details': exception.details,
        }, exception.status_code


class LoginPresenter:
    def success(self, tokens, user, profile):
        return {
            'success': True,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': format_user(user, profile),
        }, 200


class RefreshTokenPresenter:
    def success(self, tokens):
        return {
            'success': True,
            'access': tokens['access'],
        }, 200


class LogoutPresenter:
    def success(self):
        return {
            'success': True,
            'code': constants.SUCCESS,
            'details': constants.LOGOUT_SUCCESS,
        }, 200


class CurrentUserPresenter:
    def success(self, user, profile):
        return {
            'success': True,
            'user': format_user(user, profile),
            'profile': format_profile(profile),
        }, 200


def format_user(user, profile=None):
    return {
        'id': user.id,
        'username': user.username,
        'phone_number': user.phone_number,
        'email': user.email,
        'role': user.role,
        'school_id': getattr(profile, 'school_id', None),
    }


def format_profile(profile):
    if profile is None:
        return None

    data = {
        'id': profile.id,
        'school_id': getattr(profile, 'school_id', None),
    }

    if hasattr(profile, 'name'):
        data['name'] = profile.name
    if hasattr(profile, 'mobile_number'):
        data['mobile_number'] = profile.mobile_number
    if hasattr(profile, 'roll_number'):
        data['roll_number'] = profile.roll_number
    if hasattr(profile, 'admission_number'):
        data['admission_number'] = profile.admission_number
    if hasattr(profile, 'academic_class_id'):
        data['academic_class_id'] = profile.academic_class_id
    if hasattr(profile, 'section_id'):
        data['section_id'] = profile.section_id

    return data
