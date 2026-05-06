from django.contrib.auth import get_user_model


class UserDB:
    def __init__(self):
        self.user_model = get_user_model()

    def get_user_by_phone_number(self, phone_number):
        try:
            return self.user_model.objects.get(phone_number=phone_number)
        except self.user_model.DoesNotExist:
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
