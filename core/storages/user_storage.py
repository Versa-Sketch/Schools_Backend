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
        if user.role == 'TEACHER':
            from teacher.models import TeacherProfile
            try:
                return TeacherProfile.objects.select_related(
                    'primary_subject'
                ).prefetch_related(
                    'assigned_sections__academic_class'
                ).get(user=user)
            except TeacherProfile.DoesNotExist:
                return None
        elif user.role == 'STUDENT':
            from student.models import StudentProfile
            try:
                return StudentProfile.objects.select_related(
                    'academic_class', 'section'
                ).get(user=user)
            except StudentProfile.DoesNotExist:
                return None
        elif user.role == 'PARENT':
            from parent.models import ParentProfile
            try:
                return ParentProfile.objects.prefetch_related(
                    'students__academic_class', 'students__section'
                ).get(user=user)
            except ParentProfile.DoesNotExist:
                return None

        profile_attribute_by_role = {
            'ADMIN': 'adminprofile',
            'PRINCIPAL': 'principalprofile',
        }
        profile_attribute = profile_attribute_by_role.get(user.role)
        if not profile_attribute:
            return None
        return getattr(user, profile_attribute, None)

    def update_user_profile_pic(self, user, url):
        user.profile_pic = url
        user.save(update_fields=['profile_pic'])
        return user
