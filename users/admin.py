from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.urls import path, re_path
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from django.utils.html import format_html
from django.urls import reverse
from .models import Role

User = get_user_model()


class IndustryFilteredAdmin(admin.ModelAdmin):
    """
    Base admin class that automatically filters by industry for non-superusers.
    Use this for models that have an 'industry' field.
    """
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superuser sees everything
        if request.user.is_superuser:
            return qs
        # Filter by user's industry
        if hasattr(request.user, 'industry') and request.user.industry:
            return qs.filter(industry=request.user.industry)
        # Return empty queryset if user has no industry
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        # Auto-assign industry if not set and user has industry
        if not change and hasattr(obj, 'industry') and not obj.industry:
            if hasattr(request.user, 'industry') and request.user.industry:
                obj.industry = request.user.industry
        super().save_model(request, obj, form, change)

# Register Industry - will work after migrations are applied
try:
    from .models import Industry
    @admin.register(Industry)
    class IndustryAdmin(admin.ModelAdmin):
        list_display = ('name', 'test_phone_number', 'description', 'view_all_data_link', 'created_at', 'updated_at')
        search_fields = ('name', 'description', 'test_phone_number')
        list_filter = ('created_at', 'updated_at')
        ordering = ('name',)
        
        fieldsets = (
            (None, {
                'fields': ('name', 'description'),
                'description': 'Enter the industry name (e.g., "Industry A", "Industry B") and optional description.'
            }),
            ('Test Credentials', {
                'fields': ('test_phone_number', 'test_password'),
                'description': 'Test phone number and password for this industry. Use these credentials for API testing.'
            }),
            ('Timestamps', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',),
            }),
        )
        
        readonly_fields = ('created_at', 'updated_at')
        
        def view_all_data_link(self, obj):
            """Add a link to view all data for this industry"""
            if obj:
                url = reverse('admin:users_industry_data_view', args=[obj.pk])
                return format_html(
                    '<a class="button" href="{}" style="background-color: #417690; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px; display: inline-block;">📊 View All Data</a>',
                    url
                )
            return "-"
        view_all_data_link.short_description = 'View All Data'
        
        def change_view(self, request, object_id, form_url='', extra_context=None):
            """Add 'View All Data' button to the change form"""
            extra_context = extra_context or {}
            # Only add URL if object_id is a valid integer (not a path like '2/view-all-data')
            if object_id:
                try:
                    industry_id = int(object_id)
                    url = reverse('admin:users_industry_data_view', args=[industry_id])
                    extra_context['view_all_data_url'] = url
                except (ValueError, TypeError):
                    # object_id is not a valid integer, skip adding the URL
                    pass
            return super().change_view(request, object_id, form_url, extra_context)
        
        def get_urls(self):
            """Add custom URLs for industry data view"""
            urls = super().get_urls()
            # Custom URLs must come BEFORE default URLs to be matched first
            # Use re_path with specific pattern to ensure it matches before the default change view
            # Match both with and without trailing slash
            custom_urls = [
                re_path(
                    r'^(?P<industry_id>\d+)/view-all-data/$',
                    self.admin_site.admin_view(self.industry_data_view),
                    name='users_industry_data_view',
                ),
                re_path(
                    r'^(?P<industry_id>\d+)/view-all-data$',
                    self.admin_site.admin_view(self.industry_data_view),
                    name='users_industry_data_view_no_slash',
                ),
            ]
            # Insert custom URLs at the beginning so they're matched first
            return custom_urls + urls
        
        def industry_data_view(self, request, industry_id):
            """
            Custom admin view to display all data for a specific industry.
            Shows complete hierarchy: Owners, Managers, Field Officers, Farmers,
            Plots, Farms, Tasks, Bookings, Inventory Items.
            """
            # Convert industry_id to int if it's a string
            try:
                industry_id = int(industry_id)
            except (ValueError, TypeError):
                return HttpResponseForbidden("Invalid industry ID.")
            
            # Permission check
            if not request.user.is_superuser:
                if not (request.user.has_role('owner') and request.user.industry and request.user.industry.id == industry_id):
                    return HttpResponseForbidden("You don't have permission to view this industry's data.")
            
            industry = get_object_or_404(Industry, id=industry_id)
            
            # Get all users in this industry by role
            owners = User.objects.filter(industry=industry, role__name='owner').select_related('role', 'industry')
            managers = User.objects.filter(industry=industry, role__name='manager').select_related('role', 'industry')
            field_officers = User.objects.filter(industry=industry, role__name='fieldofficer').select_related('role', 'industry')
            farmers = User.objects.filter(industry=industry, role__name='farmer').select_related('role', 'industry')
            
            # Calculate counts
            owners_count = owners.count()
            managers_count = managers.count()
            field_officers_count = field_officers.count()
            farmers_count = farmers.count()
            
            # Calculate total user count
            total_users_count = owners_count + managers_count + field_officers_count + farmers_count
            
            # Get all data in this industry
            context = {
                'industry': industry,
                'owners': owners,
                'managers': managers,
                'field_officers': field_officers,
                'farmers': farmers,
                'owners_count': owners_count,
                'managers_count': managers_count,
                'field_officers_count': field_officers_count,
                'farmers_count': farmers_count,
                'total_users_count': total_users_count,
            }
            
            # Try to get plots and farms
            try:
                from farms.models import Plot, Farm
                plots = Plot.objects.filter(industry=industry).select_related('farmer', 'created_by', 'industry')
                farms = Farm.objects.filter(industry=industry).select_related(
                    'farm_owner', 'plot', 'crop_type', 'soil_type', 'industry'
                )
                context['plots'] = plots
                context['farms'] = farms
                context['plots_count'] = plots.count()
                context['farms_count'] = farms.count()
            except ImportError:
                context['plots'] = []
                context['farms'] = []
                context['plots_count'] = 0
                context['farms_count'] = 0
            
            # Try to get tasks
            try:
                from tasks.models import Task
                tasks = Task.objects.filter(industry=industry).select_related('assigned_to', 'created_by', 'industry')
                context['tasks'] = tasks
                context['tasks_count'] = tasks.count()
            except ImportError:
                context['tasks'] = []
                context['tasks_count'] = 0
            
            # Try to get bookings
            try:
                from bookings.models import Booking
                bookings = Booking.objects.filter(industry=industry).select_related('created_by', 'approved_by', 'industry')
                context['bookings'] = bookings
                context['bookings_count'] = bookings.count()
            except ImportError:
                context['bookings'] = []
                context['bookings_count'] = 0
            
            # Try to get inventory items
            try:
                from inventory.models import InventoryItem
                inventory_items = InventoryItem.objects.filter(industry=industry).select_related('industry')
                context['inventory_items'] = inventory_items
                context['inventory_items_count'] = inventory_items.count()
            except ImportError:
                context['inventory_items'] = []
                context['inventory_items_count'] = 0
            
            # Try to get vendors (filter by created_by's industry)
            try:
                from vendors.models import Vendor
                vendors = Vendor.objects.filter(created_by__industry=industry).select_related('created_by')
                context['vendors'] = vendors
                context['vendors_count'] = vendors.count()
            except ImportError:
                context['vendors'] = []
                context['vendors_count'] = 0
            
            # Try to get stock items (Stock model from inventory)
            try:
                from inventory.models import Stock
                stock_items = Stock.objects.filter(industry=industry).select_related('created_by', 'industry')
                stock_items_count = stock_items.count()
                # Always set stock_items - use queryset directly (Django templates handle querysets)
                context['stock_items'] = stock_items
                context['stock_items_count'] = stock_items_count
                print(f"DEBUG: Stock items for industry {industry.id}: {stock_items_count} items")
            except Exception as e:
                # If Stock model doesn't exist or any error occurs, set empty
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error loading stock items for industry {industry.id}: {str(e)}")
                print(f"DEBUG: Error loading stock items: {str(e)}")
                context['stock_items'] = []
                context['stock_items_count'] = 0
            
            # Try to get orders (filter by created_by's industry)
            try:
                from vendors.models import Order
                orders = Order.objects.filter(created_by__industry=industry).select_related('vendor', 'created_by')
                context['orders'] = orders
                context['orders_count'] = orders.count()
            except ImportError:
                context['orders'] = []
                context['orders_count'] = 0
            
            # Add admin context
            context.update({
                'opts': self.model._meta,
                'has_view_permission': True,
                'has_add_permission': self.has_add_permission(request),
                'has_change_permission': self.has_change_permission(request, industry),
                'has_delete_permission': self.has_delete_permission(request, industry),
                'site_header': self.admin_site.site_header,
                'site_title': self.admin_site.site_title,
            })
            
            return render(request, 'admin/users/industry_data_view.html', context)
            
except (ImportError, Exception):
    # Industry model or table doesn't exist yet - skip registration
    # This will be registered after migrations are applied
    pass

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display  = ('name', 'display_name')
    search_fields = ('name', 'display_name')

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal info', {'fields': (
            'first_name', 'last_name', 'email', 'username',
            'address', 'village', 'state', 'district', 'taluka',
            'profile_picture'
        )}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Industry & Hierarchy', {'fields': ('industry', 'created_by')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'phone_number', 'email', 'role', 'industry', 'created_by',
                'password1', 'password2',
                'is_active', 'is_staff', 'is_superuser'
            ),
        }),
    )
    list_display    = (
        'phone_number', 'username', 'email', 'role', 'industry', 'get_created_by_email',
        'is_active', 'is_staff', 'is_superuser', 'date_joined'
    )
    list_filter     = ('role', 'industry', 'is_active', 'is_staff', 'is_superuser', 'created_by')
    search_fields   = ('phone_number', 'username', 'email', 'created_by__phone_number', 'created_by__email', 'industry__name')
    ordering        = ('-date_joined',)
    filter_horizontal = ('groups', 'user_permissions',)
    
    def get_created_by_email(self, obj):
        """Display the email of the user who created this user"""
        if obj.created_by:
            return obj.created_by.email
        return "No creator"
    get_created_by_email.short_description = 'Created By (Email)'
    get_created_by_email.admin_order_field = 'created_by__email'
    
    def get_queryset(self, request):
        """Filter users by industry for non-superusers"""
        qs = super().get_queryset(request)
        # Global Admin sees all users
        if request.user.is_superuser:
            return qs
        # Use multi-tenant utility to get accessible users
        from .multi_tenant_utils import get_accessible_users
        return get_accessible_users(request.user)
    
    def save_model(self, request, obj, form, change):
        """Automatically set created_by to the current user when creating new users"""
        if not change:  # Only for new objects
            obj.created_by = request.user
            # Auto-generate username if not provided
            if not obj.username or obj.username.strip() == '':
                # Use email as username if available, otherwise use phone_number or generate one
                if obj.email:
                    base_username = obj.email.split('@')[0]
                    # Ensure uniqueness
                    username = base_username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    obj.username = username
                elif obj.phone_number:
                    base_username = f"user_{obj.phone_number}"
                    # Ensure uniqueness
                    username = base_username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}_{counter}"
                        counter += 1
                    obj.username = username
                else:
                    # Generate a unique username
                    import uuid
                    obj.username = f"user_{uuid.uuid4().hex[:8]}"
        super().save_model(request, obj, form, change)
