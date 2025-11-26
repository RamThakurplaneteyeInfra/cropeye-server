from django.contrib import admin
from .models import Booking, BookingComment, BookingAttachment

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Booking Admin - matches the "Add Booking" form in screenshot
    Fields: Item Name, User Role, Start Date, End Date, Status
    """
    list_display = ('item_name', 'title', 'user_role', 'status', 'start_date', 'end_date', 'created_by')
    list_filter = ('status', 'user_role', 'start_date', 'created_at')
    search_fields = ('item_name', 'title', 'description', 'user_role__name')
    ordering = ('-created_at',)
    raw_id_fields = ('created_by', 'approved_by', 'user_role')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': (
                ('item_name', 'user_role'),
                ('start_date', 'end_date'),
                'status',
            ),
            'description': 'Enter the booking details. All fields are required.'
        }),
        ('Additional Information', {
            'fields': ('title', 'description', 'booking_type', 'industry'),
            'classes': ('collapse',),
        }),
        ('Approval', {
            'fields': ('created_by', 'approved_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'industry') and request.user.industry:
            return qs.filter(industry=request.user.industry)
        return qs.none()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Set default created_by to current user for new bookings
        if not obj:  # Creating new booking
            if 'created_by' in form.base_fields:
                form.base_fields['created_by'].initial = request.user
                form.base_fields['created_by'].required = False
        return form
    
    def save_model(self, request, obj, form, change):
        # Set created_by automatically for new bookings
        if not change:  # New booking
            obj.created_by = request.user
            # Set industry from user if not set
            if not obj.industry:
                if hasattr(request.user, 'industry') and request.user.industry:
                    obj.industry = request.user.industry
        super().save_model(request, obj, form, change)

@admin.register(BookingComment)
class BookingCommentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'user', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('content', 'booking__title')
    ordering = ('-created_at',)
    raw_id_fields = ('booking', 'user')

@admin.register(BookingAttachment)
class BookingAttachmentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_by', 'uploaded_at')
    search_fields = ('description', 'booking__title')
    ordering = ('-uploaded_at',)
    raw_id_fields = ('booking', 'uploaded_by') 