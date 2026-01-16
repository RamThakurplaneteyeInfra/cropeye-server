from rest_framework import permissions
from users.permissions import IsSuperAdmin, IsManager

class CanManageBookings(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.is_superuser or
             request.user.has_role('owner') or
             request.user.has_role('manager') or
             request.user.has_role('fieldofficer'))
        )

class CanViewBookings(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_superuser or
            request.user.has_role('owner') or
            request.user.has_role('manager') or
            obj.created_by == request.user or
            obj.booking_type == 'public'
        ) 