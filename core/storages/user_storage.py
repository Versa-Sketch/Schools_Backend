from core.models import User


class UserDB:
    def __init__(self):
        pass

    def get_user_by_phone_number(self, phone_number):
        try:
            return User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return None

    def get_user_profile(self, user):
        profile_attribute_by_role = {
            'PRINCIPAL': 'principalprofile',
            'TEACHER': 'teacherprofile',
            'STUDENT': 'studentprofile',
            'PARENT': 'parentprofile',
        }
        profile_attribute = profile_attribute_by_role.get(user.role)
        if not profile_attribute:
            return None
        return getattr(user, profile_attribute, None)

    def update_user_profile_pic(self, user, url):
        user.profile_pic = url
        user.save(update_fields=['profile_pic'])
        return user
