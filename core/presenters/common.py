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
        'school_name': profile.school.name if getattr(profile, 'school', None) else None,
        'school_logo_url': profile.school.logo if getattr(profile, 'school', None) else None,
        'profile_pic_url': user.profile_pic or None,
    }

def format_profile(profile):
    if profile is None:
        return None

    data = {
        'id': profile.id,
        'school_id': getattr(profile, 'school_id', None),
        'school_name': profile.school.name if getattr(profile, 'school', None) else None,
    }

    if hasattr(profile, 'name'):
        data['name'] = profile.name
    if hasattr(profile, 'roll_number'):
        data['roll_number'] = profile.roll_number
    if hasattr(profile, 'admission_number'):
        data['admission_number'] = profile.admission_number

    # Student specific
    if hasattr(profile, 'academic_class') and profile.academic_class:
        data['academic_class'] = {
            'id': str(profile.academic_class.id),
            'name': profile.academic_class.name
        }
    if hasattr(profile, 'section') and profile.section:
        data['section'] = {
            'id': str(profile.section.id),
            'name': profile.section.name
        }

    # Teacher specific
    if hasattr(profile, 'primary_subject') and profile.primary_subject:
        data['primary_subject'] = {
            'id': str(profile.primary_subject.id),
            'name': profile.primary_subject.name
        }
    if hasattr(profile, 'assigned_sections'):
        data['assigned_sections'] = [
            {
                'id': str(section.id),
                'class_name': section.academic_class.name,
                'section_name': section.name
            } for section in profile.assigned_sections.all()
        ]

    # Parent specific
    if hasattr(profile, 'students'):
        data['students'] = [
            {
                'id': str(student.id),
                'name': student.name,
                'academic_class_name': student.academic_class.name if student.academic_class else None,
                'section_name': student.section.name if student.section else None,
            } for student in profile.students.all()
        ]

    return data
