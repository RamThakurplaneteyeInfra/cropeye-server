from rest_framework import permissions
from .multi_tenant_utils import get_user_industry


class HasRolePermission(permissions.BasePermission):
    """
    Generic permission that checks if the user has any of the given roles.
    Set `roles` in subclasses.
    """
    roles = []

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (
            user.is_superuser or user.has_any_role(self.roles)
        )


class IsGlobalAdmin(permissions.BasePermission):
    """
    Permission for Global Admin (single superuser who can manage all industries).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


class IsIndustryAdmin(permissions.BasePermission):
    """
    Permission for Industry Admin (Owner role within an industry).
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Global Admin can also access
        if user.is_superuser:
            return True
        return user.has_role('owner') and user.industry is not None


class IsSuperAdmin(HasRolePermission):
    roles = ['admin']


class IsAdmin(HasRolePermission):
    roles = ['admin']


class IsManager(permissions.BasePermission):
    """
    Custom permission to only allow managers to access.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.has_role('manager')
        )


class IsAgronomist(HasRolePermission):
    roles = ['agronomist']


class IsQualityControl(HasRolePermission):
    roles = ['qualitycontrol']


class IsFieldOfficer(permissions.BasePermission):
    """
    Custom permission to only allow field officers to access.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.has_role('fieldofficer')
        )


class IsFarmer(permissions.BasePermission):
    """
    Custom permission to only allow farmers to access.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.has_role('farmer')
        )


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners to access.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.has_role('owner')
        )


class IsOwnerOrManager(permissions.BasePermission):
    """
    Custom permission to allow owners or managers to access.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.has_any_role(['owner', 'manager']))
        )


class MultiTenantPermission(permissions.BasePermission):
    """
    Base permission class that enforces industry-based access control.
    Checks if user can access the object based on their industry.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Global Admin can access everything
        if user.is_superuser:
            return True
        
        # Check if object has industry field
        if not hasattr(obj, 'industry'):
            return True  # If no industry field, allow access (backward compatibility)
        
        user_industry = get_user_industry(user)
        
        # If user has no industry, deny access
        if not user_industry:
            return False
        
        # Industry Admin (Owner) can access all objects in their industry
        if user.has_role('owner'):
            return obj.industry == user_industry
        
        # For other roles, check if object belongs to user's industry
        if obj.industry != user_industry:
            return False
        
        # Additional role-specific checks
        if user.has_role('manager'):
            # Manager can access objects related to their FieldOfficers/Farmers
            if hasattr(obj, 'created_by'):
                # Check if created_by is in manager's hierarchy
                from .multi_tenant_utils import get_accessible_users
                accessible_users = get_accessible_users(user)
                return obj.created_by in accessible_users
            elif hasattr(obj, 'farm_owner'):
                # For Farm objects
                from .multi_tenant_utils import get_accessible_users
                accessible_users = get_accessible_users(user)
                return obj.farm_owner in accessible_users
        
        if user.has_role('fieldofficer'):
            # FieldOfficer can access objects they created or related to their farmers
            if hasattr(obj, 'created_by'):
                return obj.created_by == user
            elif hasattr(obj, 'farmer'):
                from .multi_tenant_utils import get_accessible_users
                accessible_users = get_accessible_users(user)
                return obj.farmer in accessible_users
        
        if user.has_role('farmer'):
            # Farmer can only access their own objects
            if hasattr(obj, 'farm_owner'):
                return obj.farm_owner == user
            elif hasattr(obj, 'farmer'):
                return obj.farmer == user
            elif hasattr(obj, 'created_by'):
                return obj.created_by == user
        
        return True
