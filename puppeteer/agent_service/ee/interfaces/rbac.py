class RBACInterface:
    """CE stub: all authenticated users are treated as admin."""

    def check_permission(self, user, permission: str) -> bool:
        return True  # CE has no RBAC — all users are implicitly admin
