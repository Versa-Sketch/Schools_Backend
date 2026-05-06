class TeacherPresenter:
    """Response formatting for teacher workflows lives here."""

    def success(self, data):
        return {
            'success': True,
            **data,
        }, 200
