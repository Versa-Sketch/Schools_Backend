class ParentDB:
    """Database queries for parent-owned workflows live here."""

    def get_parent_profile(self, user):
        return getattr(user, 'parentprofile', None)
