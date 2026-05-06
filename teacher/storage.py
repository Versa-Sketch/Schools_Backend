class TeacherDB:
    """Database queries for teacher-owned workflows live here."""

    def get_teacher_profile(self, user):
        return getattr(user, 'teacherprofile', None)
