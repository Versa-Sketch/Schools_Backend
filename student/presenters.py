class StudentPresenter:
    """Response formatting for student workflows lives here."""

    def success(self, data):
        return {
            'success': True,
            **data,
        }, 200
