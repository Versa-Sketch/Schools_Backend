from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    message = 'Only admins can access this endpoint.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
        )


class IsPrincipal(BasePermission):
    message = 'Only principals can access this endpoint.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'PRINCIPAL'
        )


class IsTeacher(BasePermission):
    message = 'Only teachers can access this endpoint.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'TEACHER'
        )


class IsStudent(BasePermission):
    message = 'Only students can access this endpoint.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'STUDENT'
        )


class IsParent(BasePermission):
    message = 'Only parents can access this endpoint.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'PARENT'
        )
