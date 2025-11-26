"""
Multi-tenant utility functions for industry-based data isolation.
"""
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()


def get_user_industry(user):
    """
    Get the industry for a user.
    - Global Admin (is_superuser=True): returns None (can access all industries)
    - Regular users: returns their industry
    """
    if user.is_superuser:
        return None
    return user.industry


def filter_by_industry(queryset, user):
    """
    Filter a queryset by industry based on user role.
    
    - Global Admin (is_superuser=True): no filtering (sees all)
    - Industry Admin (Owner): sees all data in their industry
    - Manager: sees data for their assigned FieldOfficers and Farmers
    - FieldOfficer: sees data for their assigned Farmers and Plots
    - Farmer: sees only their own data
    
    Args:
        queryset: Django QuerySet to filter
        user: User instance
        
    Returns:
        Filtered QuerySet
    """
    # Global Admin sees everything
    if user.is_superuser:
        return queryset
    
    user_industry = user.industry
    if not user_industry:
        # User has no industry, return empty queryset
        return queryset.none()
    
    # Industry Admin (Owner) - full access to their industry
    if user.has_role('owner'):
        return queryset.filter(industry=user_industry)
    
    # Manager - can see their assigned FieldOfficers and Farmers
    if user.has_role('manager'):
        # Get all field officers created by this manager
        field_officers = User.objects.filter(
            created_by=user,
            role__name='fieldofficer',
            industry=user_industry
        )
        # Get all farmers created by those field officers
        farmers = User.objects.filter(
            created_by__in=field_officers,
            role__name='farmer',
            industry=user_industry
        )
        
        # Filter queryset based on model type
        if hasattr(queryset.model, 'industry'):
            # For models with industry field, filter by industry and related users
            if hasattr(queryset.model, 'created_by'):
                # Models with created_by (e.g., Plot, Farm)
                return queryset.filter(
                    industry=user_industry
                ).filter(
                    Q(created_by__in=field_officers) | 
                    Q(created_by__in=farmers) |
                    Q(farmer__in=farmers) if hasattr(queryset.model, 'farmer') else Q()
                )
            elif hasattr(queryset.model, 'farm_owner'):
                # Farm model
                return queryset.filter(
                    industry=user_industry,
                    farm_owner__in=farmers
                )
            elif hasattr(queryset.model, 'assigned_to'):
                # Task model
                return queryset.filter(
                    industry=user_industry
                ).filter(
                    Q(assigned_to__in=field_officers) |
                    Q(assigned_to__in=farmers) |
                    Q(created_by=user)
                )
            else:
                # Generic: just filter by industry
                return queryset.filter(industry=user_industry)
        else:
            # Model doesn't have industry field, filter by related users
            return queryset.filter(
                Q(created_by__in=field_officers) |
                Q(created_by__in=farmers)
            )
    
    # FieldOfficer - can see their assigned Farmers and Plots
    if user.has_role('fieldofficer'):
        # Get all farmers created by this field officer
        farmers = User.objects.filter(
            created_by=user,
            role__name='farmer',
            industry=user_industry
        )
        
        # Filter queryset based on model type
        if hasattr(queryset.model, 'industry'):
            if hasattr(queryset.model, 'farmer'):
                # Plot model
                return queryset.filter(
                    industry=user_industry,
                    farmer__in=farmers
                )
            elif hasattr(queryset.model, 'farm_owner'):
                # Farm model
                return queryset.filter(
                    industry=user_industry,
                    farm_owner__in=farmers
                )
            elif hasattr(queryset.model, 'created_by'):
                # Models with created_by
                return queryset.filter(
                    industry=user_industry,
                    created_by=user
                )
            else:
                return queryset.filter(industry=user_industry)
        else:
            return queryset.filter(created_by=user)
    
    # Farmer - can see only their own data
    if user.has_role('farmer'):
        if hasattr(queryset.model, 'industry'):
            if hasattr(queryset.model, 'farmer'):
                # Plot model
                return queryset.filter(industry=user_industry, farmer=user)
            elif hasattr(queryset.model, 'farm_owner'):
                # Farm model
                return queryset.filter(industry=user_industry, farm_owner=user)
            elif hasattr(queryset.model, 'created_by'):
                return queryset.filter(industry=user_industry, created_by=user)
            else:
                return queryset.filter(industry=user_industry)
        else:
            return queryset.filter(created_by=user)
    
    # Default: filter by industry if model has it
    if hasattr(queryset.model, 'industry'):
        return queryset.filter(industry=user_industry)
    
    return queryset.none()


def get_accessible_users(user):
    """
    Get users that the current user can access based on their role and industry.
    
    Returns:
        QuerySet of User objects
    """
    # Global Admin sees all users
    if user.is_superuser:
        return User.objects.all()
    
    user_industry = user.industry
    if not user_industry:
        return User.objects.none()
    
    # Industry Admin (Owner) - sees all users in their industry
    if user.has_role('owner'):
        return User.objects.filter(industry=user_industry)
    
    # Manager - sees their FieldOfficers and Farmers
    if user.has_role('manager'):
        field_officers = User.objects.filter(
            created_by=user,
            role__name='fieldofficer',
            industry=user_industry
        )
        farmers = User.objects.filter(
            created_by__in=field_officers,
            role__name='farmer',
            industry=user_industry
        )
        return User.objects.filter(
            Q(id__in=field_officers.values_list('id', flat=True)) |
            Q(id__in=farmers.values_list('id', flat=True))
        )
    
    # FieldOfficer - sees their Farmers
    if user.has_role('fieldofficer'):
        return User.objects.filter(
            created_by=user,
            role__name='farmer',
            industry=user_industry
        )
    
    # Farmer - sees only themselves
    if user.has_role('farmer'):
        return User.objects.filter(id=user.id)
    
    return User.objects.none()

