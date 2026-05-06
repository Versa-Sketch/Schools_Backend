class PrincipalPresenter:
    """Response formatting for principal workflows lives here."""

    def success(self, data):
        return {
            'success': True,
            **data,
        }, 200
