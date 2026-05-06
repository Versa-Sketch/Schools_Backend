class PrincipalDB:
    """Database queries for principal-owned workflows live here."""

    def get_principal_profile(self, user):
        return getattr(user, 'principalprofile', None)
