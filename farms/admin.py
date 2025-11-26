from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin

from .models import (
    SoilType,
    CropType,
    IrrigationType,
    SensorType,
    Plot,
    Farm,
    FarmImage,
    FarmSensor,
    FarmIrrigation,
)


@admin.register(SoilType)
class SoilTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(CropType)
class CropTypeAdmin(admin.ModelAdmin):
    list_display = ('crop_type', 'plantation_type', 'planting_method')
    search_fields = ('crop_type',)


@admin.register(IrrigationType)
class IrrigationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(SensorType)
class SensorTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class FarmImageInline(admin.TabularInline):
    model = FarmImage
    extra = 0
    fields = ('title', 'image', 'capture_date', 'uploaded_by')
    readonly_fields = ('uploaded_by',)


class FarmSensorInline(admin.TabularInline):
    model = FarmSensor
    extra = 0
    fields = ('name', 'sensor_type', 'installation_date', 'status')


class FarmIrrigationInline(admin.TabularInline):
    model = FarmIrrigation
    extra = 0
    fields = (
        'irrigation_type',
        'status',
    )


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = (
        'farm_owner',
        'farm_uid',
        'industry',
        'area_size',
        'soil_type',
        'crop_type',
        'get_created_by_email',
        'created_at',
    )
    list_filter = ('industry', 'soil_type', 'crop_type', 'created_at', 'created_by')
    search_fields = ('farm_owner__username', 'farm_uid', 'address', 'created_by__email', 'industry__name')
    readonly_fields = ('farm_uid', 'created_at', 'updated_at')

    inlines = [
        FarmIrrigationInline,
        FarmImageInline,
        FarmSensorInline,
    ]

    fieldsets = (
        (None, {
            'fields': (
                'farm_owner',
                'plot',
                'industry',
                'address',
                'area_size',
                'soil_type',
                'crop_type',
                'farm_document',
            )
        }),
        ('Metadata', {
            'fields': ('farm_uid', 'created_by', 'created_at', 'updated_at'),
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
    
    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, 'industry') and not obj.industry:
            if hasattr(request.user, 'industry') and request.user.industry:
                obj.industry = request.user.industry
        super().save_model(request, obj, form, change)
    
    def get_created_by_email(self, obj):
        """Display the email of the user who created this farm"""
        if obj.created_by:
            return obj.created_by.email
        return "No creator"
    get_created_by_email.short_description = 'Created By (Email)'
    get_created_by_email.admin_order_field = 'created_by__email'


@admin.register(Plot)
class PlotAdmin(LeafletGeoAdmin):
    list_display = (
        'gat_number',
        'plot_number',
        'industry',
        'village',
        'taluka',
        'district',
        'state',
        'country',
        'get_created_by_email',
    )
    list_filter = ('industry', 'village', 'taluka', 'district', 'state', 'country', 'created_by')
    search_fields = ('gat_number', 'plot_number', 'created_by__email', 'industry__name')

    fieldsets = (
        (None, {
            'fields': (
                'gat_number',
                'plot_number',
                'industry',
                'village',
                'taluka',
                'district',
                'state',
                'country',
                'pin_code',
            )
        }),
        ('Geo Data', {'fields': ('location', 'boundary')}),
        ('Metadata', {
            'fields': ('created_by',),
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
    
    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, 'industry') and not obj.industry:
            if hasattr(request.user, 'industry') and request.user.industry:
                obj.industry = request.user.industry
        super().save_model(request, obj, form, change)
    
    def get_created_by_email(self, obj):
        """Display the email of the user who created this plot"""
        if obj.created_by:
            return obj.created_by.email
        return "No creator"
    get_created_by_email.short_description = 'Created By (Email)'
    get_created_by_email.admin_order_field = 'created_by__email'


@admin.register(FarmImage)
class FarmImageAdmin(LeafletGeoAdmin):
    list_display = ('title', 'farm', 'capture_date', 'uploaded_by', 'uploaded_at')
    list_filter = ('farm', 'capture_date', 'uploaded_at')
    search_fields = ('title',)
    readonly_fields = ('uploaded_by', 'uploaded_at')

    fieldsets = (
        (None, {'fields': ('farm', 'title', 'image', 'capture_date', 'notes')}),
        ('Location', {'fields': ('location',)}),
        ('Metadata', {'fields': ('uploaded_by', 'uploaded_at')}),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FarmSensor)
class FarmSensorAdmin(LeafletGeoAdmin):
    list_display = ('name', 'farm', 'sensor_type', 'installation_date', 'status')
    list_filter = ('farm', 'sensor_type', 'status', 'installation_date')
    search_fields = ('name',)

    fieldsets = (
        (None, {
            'fields': (
                'farm',
                'name',
                'sensor_type',
                'installation_date',
                'last_maintenance',
                'status',
            )
        }),
        ('Location', {'fields': ('location',)}),
    )


@admin.register(FarmIrrigation)
class FarmIrrigationAdmin(LeafletGeoAdmin):
    list_display = ('farm', 'irrigation_type', 'status')
    list_filter = ('farm', 'irrigation_type', 'status')
    search_fields = ('farm__farm_owner__username',)

    fieldsets = (
        (None, {
            'fields': (
                'farm',
                'irrigation_type',
                'status',
                'motor_horsepower',
                'pipe_width_inches',
                'distance_motor_to_plot_m',   # updated field name
                'plants_per_acre',
                'flow_rate_lph',
                'emitters_count',
            )
        }),
        ('Geographic', {'fields': ('location',)}),
    )
