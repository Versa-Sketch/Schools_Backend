from rest_framework.response import Response

class CommonErrorPresenter:
    def error(self, exception):
        payload = {
            'success': False,
            'code': exception.code,
            'details': exception.details,
        }
        return Response(payload, status=exception.status_code)

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
