class StudentDB:
    """Database queries for student-owned workflows live here."""

    def get_student_profile(self, user):
        return getattr(user, 'studentprofile', None)
