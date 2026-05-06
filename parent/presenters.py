class ParentPresenter:
    """Response formatting for parent workflows lives here."""

    def success(self, data):
        return {
            'success': True,
            **data,
        }, 200
