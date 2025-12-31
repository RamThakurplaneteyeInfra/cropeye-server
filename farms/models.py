import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.gis.db import models as gis_models


class SoilType(models.Model):
    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    properties  = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name


class PlantationType(models.Model):
    """
    Industry-specific plantation types (e.g., Adsali, Suru, Ratoon, Kharif, Rabi, etc.)
    """
    crop_type = models.ForeignKey(
        'CropType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='plantation_types',
        help_text="Crop type this plantation type belongs to"
    )
    industry = models.ForeignKey(
        'users.Industry',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='plantation_types',
        help_text="Industry this plantation type belongs to"
    )
    name = models.CharField(max_length=100, help_text="Plantation type name (e.g., Adsali, Suru, Kharif)")
    code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Short code for this plantation type (used in CropType.plantation_type field)"
    )
    description = models.TextField(blank=True, help_text="Description of this plantation type")
    is_active = models.BooleanField(default=True, help_text="Whether this plantation type is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['crop_type', 'industry', 'code']]  # Same code can't exist twice for same crop and industry
        ordering = ['name']

    def __str__(self):
        crop_name = self.crop_type.crop_type if self.crop_type else "No Crop"
        industry_name = self.industry.name if self.industry else "Global"
        return f"{self.name} ({crop_name} - {industry_name})"


class PlantingMethod(models.Model):
    """
    Industry-specific planting methods (e.g., 3 Bud Method, 2 Bud Method, Broadcast, etc.)
    """
    plantation_type = models.ForeignKey(
        'PlantationType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='planting_methods',
        help_text="Plantation type this planting method belongs to"
    )
    industry = models.ForeignKey(
        'users.Industry',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='planting_methods',
        help_text="Industry this planting method belongs to"
    )
    name = models.CharField(max_length=100, help_text="Planting method name (e.g., 3 Bud Method, Broadcast)")
    code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Short code for this planting method (used in CropType.planting_method field)"
    )
    description = models.TextField(blank=True, help_text="Description of this planting method")
    is_active = models.BooleanField(default=True, help_text="Whether this planting method is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['plantation_type', 'industry', 'code']]  # Same code can't exist twice for same plantation type and industry
        ordering = ['name']

    def __str__(self):
        plantation_name = self.plantation_type.name if self.plantation_type else "No Plantation"
        industry_name = self.industry.name if self.industry else "Global"
        return f"{self.name} ({plantation_name} - {industry_name})"


class CropType(models.Model):
    """
    Crop types (e.g., Sugarcane, Wheat, Rice, etc.)
    Uses CharField with choices for plantation_type and planting_method
    """
    PLANTATION_TYPE_CHOICES = [
        ('adsali',         'Adsali'),
        ('suru',           'Suru'),
        ('ratoon',         'Ratoon'),
        ('pre-seasonal',   'Pre-Seasonal'),
        ('post-seasonal',  'Post-Seasonal'),
        ('pre_seasonal',   'Pre-Seasonal'),  # Alternative spelling
        ('other',          'Other'),
    ]
    PLANTATION_METHOD_CHOICES = [
        ('3_bud',           '3 Bud Method'),
        ('2_bud',           '2 Bud Method'),
        ('1_bud',           '1 Bud Method'),
        ('1_bud_stip_Method','1 Bud (stip Method)'),
        ('other',           'Other'),
    ]

    # Multi-tenant: Industry association
    industry = models.ForeignKey(
        'users.Industry',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='crop_types',
        help_text="Industry this crop type belongs to"
    )
    crop_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of the crop type"
    )
    plantation_type = models.CharField(
        max_length=100,
        choices=PLANTATION_TYPE_CHOICES,
        blank=True,
        help_text="Plantation type for this crop"
    )
    planting_method = models.CharField(
        max_length=100,
        choices=PLANTATION_METHOD_CHOICES,
        blank=True,
        help_text="Planting method for this crop"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['crop_type']
        verbose_name = 'Crop Type'
        verbose_name_plural = 'Crop Types'

    def __str__(self):
        return self.crop_type or "Unnamed CropType"


class IrrigationType(models.Model):
    IRRIGATION_CHOICES = [
        ('drip',         'Drip Irrigation'),
        ('sprinkler',    'Sprinkler Irrigation'),
        ('flood',        'Flood Irrigation'),
        ('center_pivot', 'Center Pivot Irrigation'),
        ('manual',       'Manual Irrigation'),
        ('none',         'None'),
    ]

    name        = models.CharField(max_length=50, choices=IRRIGATION_CHOICES)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.get_name_display()


class SensorType(models.Model):
    SENSOR_CHOICES = [
        ('soil_moisture','Soil Moisture'),
        ('temperature',  'Temperature'),
        ('humidity',     'Humidity'),
        ('rainfall',     'Rainfall'),
        ('wind',         'Wind'),
        ('light',        'Light'),
        ('other',        'Other'),
    ]

    name        = models.CharField(max_length=50, choices=SENSOR_CHOICES)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.get_name_display()


class Plot(models.Model):
    """
    Represents a land plot identified by a GAT number and optional plot number.
    """
    gat_number  = models.CharField(max_length=50)
    plot_number = models.CharField(max_length=50, blank=True)
    village     = models.CharField(max_length=100, blank=True)
    taluka      = models.CharField(max_length=100, blank=True)
    district    = models.CharField(max_length=100, blank=True)
    state       = models.CharField(max_length=100, blank=True)
    country     = models.CharField(max_length=100, default='India', blank=True)
    pin_code    = models.CharField(max_length=6, blank=True)

    # Multi-tenant: Industry association
    industry = models.ForeignKey(
        'users.Industry',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='plots',
        help_text="Industry this plot belongs to"
    )
    
    # Auto-assigned farmer (most recent farmer created by field officer)
    farmer      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plots',
        help_text="Farmer who owns this plot"
    )
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_plots',
        help_text="Field officer who created this plot"
    )

    location    = gis_models.PointField(geography=True, null=True, blank=True, db_index=True)
    boundary    = gis_models.PolygonField(geography=True, null=True, blank=True, db_index=True)
    
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('gat_number', 'plot_number', 'village', 'taluka', 'district')
        indexes = [
            models.Index(fields=['gat_number', 'plot_number']),
        ]

    def __str__(self):
        return f"Gat {self.gat_number} / Plot {self.plot_number or 'N/A'} – {self.village or 'Unknown'}"

    def save(self, *args, **kwargs):
        """Override save to auto-assign farmer and sync with all FastAPI services"""
        is_new = self.pk is None
        
        # Auto-assign farmer if this is a new plot and no farmer is assigned
        if is_new and not self.farmer and self.created_by:
            try:
                from .auto_assignment_service import AutoAssignmentService
                recent_farmer = AutoAssignmentService.get_most_recent_farmer_by_field_officer(self.created_by)
                if recent_farmer:
                    self.farmer = recent_farmer
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to auto-assign farmer to plot: {str(e)}")
        
        super().save(*args, **kwargs)
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Sync with FastAPI services after saving (only if not in unified registration)
        # Skip sync during unified registration to avoid geometry conversion issues
        if not getattr(self, '_skip_fastapi_sync', False):
            # Sync with events.py after saving
            try:
                from .services import EventsSyncService
                sync_service = EventsSyncService()
                sync_service.sync_plot_to_events(self)
            except Exception as e:
                logger.error(f"Failed to sync plot {self.id} to events.py: {str(e)}")
            
            # Sync with soil.py after saving (main.py)
            try:
                from .soil_services import SoilSyncService
                soil_sync_service = SoilSyncService()
                soil_sync_service.sync_plot_to_soil(self)
            except Exception as e:
                logger.error(f"Failed to sync plot {self.id} to soil.py: {str(e)}")
            
            # Sync with Admin.py after saving
            try:
                from .admin_services import AdminSyncService
                admin_sync_service = AdminSyncService()
                admin_sync_service.sync_plot_to_admin(self)
            except Exception as e:
                logger.error(f"Failed to sync plot {self.id} to Admin.py: {str(e)}")
            
            # Sync with ET.py after saving
            try:
                from .et_services import ETSyncService
                et_sync_service = ETSyncService()
                et_sync_service.sync_plot_to_et(self)
            except Exception as e:
                logger.error(f"Failed to sync plot {self.id} to ET.py: {str(e)}")
            
            # Sync with field.py after saving
            try:
                from .field_services import FieldSyncService
                field_sync_service = FieldSyncService()
                field_sync_service.sync_plot_to_field(self)
            except Exception as e:
                logger.error(f"Failed to sync plot {self.id} to field.py: {str(e)}")

    def delete(self, *args, **kwargs):
        """Override delete to sync with all FastAPI services"""
        plot_id = self.pk
        super().delete(*args, **kwargs)
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Sync deletion with events.py after deleting
        try:
            from .services import EventsSyncService
            sync_service = EventsSyncService()
            sync_service.delete_plot_from_events(plot_id)
        except Exception as e:
            logger.error(f"Failed to delete plot {plot_id} from events.py: {str(e)}")
        
        # Sync deletion with soil.py after deleting (main.py)
        try:
            from .soil_services import SoilSyncService
            soil_sync_service = SoilSyncService()
            soil_sync_service.delete_plot_from_soil(plot_id)
        except Exception as e:
            logger.error(f"Failed to delete plot {plot_id} from soil.py: {str(e)}")
        
        # Sync deletion with Admin.py after deleting
        try:
            from .admin_services import AdminSyncService
            admin_sync_service = AdminSyncService()
            admin_sync_service.delete_plot_from_admin(plot_id)
        except Exception as e:
            logger.error(f"Failed to delete plot {plot_id} from Admin.py: {str(e)}")
        
        # Sync deletion with ET.py after deleting
        try:
            from .et_services import ETSyncService
            et_sync_service = ETSyncService()
            et_sync_service.delete_plot_from_et(plot_id)
        except Exception as e:
            logger.error(f"Failed to delete plot {plot_id} from ET.py: {str(e)}")
        
        # Sync deletion with field.py after deleting
        try:
            from .field_services import FieldSyncService
            field_sync_service = FieldSyncService()
            field_sync_service.delete_plot_from_field(plot_id)
        except Exception as e:
            logger.error(f"Failed to delete plot {plot_id} from field.py: {str(e)}")


class Farm(models.Model):
    farm_uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Multi-tenant: Industry association
    industry = models.ForeignKey(
        'users.Industry',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='farms',
        help_text="Industry this farm belongs to"
    )
    
    farm_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='farms'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_farms'
    )
    plot = models.ForeignKey(
        Plot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='farms'
    )

    address = models.TextField()
    area_size = models.DecimalField(max_digits=10, decimal_places=2, help_text="Size in acres")
    soil_type = models.ForeignKey(
        SoilType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    crop_type = models.ForeignKey(
        CropType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    farm_document = models.FileField(upload_to='farm_documents/', null=True, blank=True)
    
    plantation_date = models.DateField(null=True, blank=True, help_text="Date when crops were planted")
    
    spacing_a = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Spacing A in meters")
    spacing_b = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Spacing B in meters")
    
    crop_variety = models.CharField(max_length=200, null=True, blank=True, help_text="Crop variety (e.g., Co 86032, Co 8371, etc.)")
    
    SUGARCANE_PLANTATION_CHOICES = [
        ('', '---------'),
        ('adsali', 'Adsali'),
        ('suru', 'Suru'),
        ('ratoon', 'Ratoon'),
        ('pre-seasonal', 'Pre-Seasonal'),
        ('post-seasonal', 'Post-Seasonal'),
        ('pre_seasonal', 'Pre-Seasonal'),
        ('other', 'Other'),
    ]
    sugarcane_plantation_type = models.CharField(
        max_length=20,
        choices=SUGARCANE_PLANTATION_CHOICES,
        null=True,
        blank=True
    )

    SUGARCANE_PLANTING_METHOD_CHOICES = [
        ('', '---------'),
        ('3_bud', '3 Bud Method'),
        ('2_bud', '2 Bud Method'),
        ('1_bud', '1 Bud Method'),
        ('1_bud_stip_Method', '1 Bud (stip Method)'),
        ('other', 'Other')
    ]
    sugarcane_planting_method = models.CharField(
        max_length=30,
        choices=SUGARCANE_PLANTING_METHOD_CHOICES,
        null=True,
        blank=True
    )

    # ===== Grapes Dropdowns =====
    GRAPES_PLANTATION_CHOICES = [
        ('', '---------'),
        ('wine', 'Wine Grapes'),
        ('table', 'Table Grapes'),
        ('late', 'Late'),
        ('early', 'Early'),
        ('pre_season', 'Pre-Season'),
        ('seasonal', 'Seasonal'),
    ]
    grapes_plantation_type = models.CharField(
        max_length=20,
        choices=GRAPES_PLANTATION_CHOICES,
        null=True,
        blank=True
    )


    # ===== New Fields for Variety Info =====
    VARIETY_TYPE_CHOICES = [
        ('pre_season', 'Pre-season'),
        ('seasonal', 'Seasonal'),
    ]
    variety_type = models.CharField(max_length=20, choices=VARIETY_TYPE_CHOICES, null=True, blank=True)

    VARIETY_SUBTYPE_CHOICES = [
        ('wine_grapes', 'Wine Grapes'),
        ('table_grapes', 'Table Grapes'),
    ]
    variety_subtype = models.CharField(max_length=20, choices=VARIETY_SUBTYPE_CHOICES, null=True, blank=True)

    VARIETY_TIMING_CHOICES = [
        ('early', 'Early'),
        ('late', 'Late'),
    ]
    variety_timing = models.CharField(max_length=10, choices=VARIETY_TIMING_CHOICES, null=True, blank=True)

    PLANT_AGE_CHOICES = [
        ('0_2', '0-2 years'),
        ('2_3', '2-3 years'),
        ('above_3', 'Above 3 years'),
    ]
    plant_age = models.CharField(max_length=10, choices=PLANT_AGE_CHOICES, null=True, blank=True)
    # Grapes-specific lifecycle fields
    foundation_pruning_date = models.DateField(
        null=True,
        blank=True,
        help_text="Foundation pruning date (Grapes only)"
    )
    fruit_pruning_date = models.DateField(
        null=True,
        blank=True,
        help_text="Fruit pruning date (Grapes only)"
    )
    last_harvesting_date = models.DateField(
        null=True,
        blank=True,
        help_text="Last harvesting date (Grapes only)"
    )
    resting_period_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Resting period in days (Grapes only)"
    )

    # Grapes drip irrigation
    row_spacing = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Row spacing in meters (Grapes drip irrigation)"
    )
    plant_spacing = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Plant spacing in meters (Grapes drip irrigation)"
    )
    flow_rate_liter_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Flow rate in liters/hour (Grapes drip irrigation)"
    )
    emitters_per_plant = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of emitters per plant (Grapes drip irrigation)"
    )

    # =====================================

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.farm_owner.username} – {self.farm_uid}"

    def farm_uid_str(self) -> str:
        uid = str(self.farm_uid).replace('-', '').upper()
        if self.plot and self.plot.gat_number and self.plot.plot_number:
            return f"{self.farm_owner.username}-{self.plot.gat_number}-{self.plot.plot_number}-{uid}"
        return f"{self.farm_owner.username}-{uid}"

    @property
    def plants_in_field(self):
        if not self.spacing_a or not self.spacing_b or not self.area_size:
            return None
        try:
            area_sq_ft = float(self.area_size) * 43560
            plants = area_sq_ft / (float(self.spacing_a) * float(self.spacing_b))
            return int(plants)
        except (ValueError, ZeroDivisionError, TypeError):
            return None
    
    

class FarmIrrigation(models.Model):
    farm                     = models.ForeignKey(Farm,
                                                 on_delete=models.CASCADE,
                                                 related_name='irrigations')
    irrigation_type          = models.ForeignKey(IrrigationType,
                                                 on_delete=models.SET_NULL,
                                                 null=True,
                                                 blank=True)
    location                 = gis_models.PointField(geography=True)
    status                   = models.BooleanField(default=True, db_index=True)

    # Specific fields per type
    motor_horsepower         = models.FloatField(null=True, blank=True)
    pipe_width_inches        = models.FloatField(null=True, blank=True)
    distance_motor_to_plot_m = models.FloatField(null=True, blank=True)
    plants_per_acre          = models.IntegerField(null=True, blank=True)
    flow_rate_lph            = models.FloatField(null=True, blank=True)
    emitters_count           = models.IntegerField(null=True, blank=True)

   

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.farm.farm_uid_str()} – {self.irrigation_type.name if self.irrigation_type else 'Unknown'}"

    def clean(self):
        """Ensure required fields for each irrigation type."""
        if self.irrigation_type:
            name = self.irrigation_type.name.lower()
            if name == 'flood':
                if not self.motor_horsepower:
                    raise ValidationError("Motor horsepower is required for flood irrigation.")
                if not self.pipe_width_inches:
                    raise ValidationError("Pipe width is required for flood irrigation.")
                if not self.distance_motor_to_plot_m:
                    raise ValidationError("Distance from motor to plot is required for flood irrigation.")
            elif name == 'drip':
                # Optional fields, soft validation
                if self.flow_rate_lph and not self.emitters_count:
                    pass
            elif name == 'sprinkler' and not self.pipe_width_inches:
                raise ValidationError("Pipe width (inches) is required for sprinkler irrigation.")

        super().clean()

    def save(self, *args, **kwargs):
        # enforce clean() on every save
        self.full_clean()
        super().save(*args, **kwargs)


class FarmSensor(models.Model):
    farm              = models.ForeignKey(Farm,
                                          on_delete=models.CASCADE,
                                          related_name='sensors')
    sensor_type       = models.ForeignKey(SensorType,
                                          on_delete=models.SET_NULL,
                                          null=True,
                                          blank=True)
    name              = models.CharField(max_length=100)
    location          = gis_models.PointField(geography=True)
    installation_date = models.DateField(default=timezone.now)
    last_maintenance  = models.DateField(null=True, blank=True)
    status            = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return f"{self.farm.farm_uid_str()} – {self.name} ({self.sensor_type.name if self.sensor_type else 'Unknown'})"


class FarmImage(models.Model):
    farm         = models.ForeignKey(Farm,
                                     on_delete=models.CASCADE,
                                     related_name='images')
    title        = models.CharField(max_length=100)
    image        = models.ImageField(upload_to='farm_images/')
    location     = gis_models.PointField(geography=True, null=True, blank=True)
    capture_date = models.DateField(null=True, blank=True)
    notes        = models.TextField(blank=True)
    uploaded_by  = models.ForeignKey(settings.AUTH_USER_MODEL,
                                     on_delete=models.CASCADE,
                                     related_name='farm_images')
    uploaded_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.farm.farm_uid_str()} – {self.title}"
    
class GrapseReport(models.Model):
    FILE_TYPE_CHOICES = [
        ('residue', 'Residue Analysis'),
        ('variety', 'Variety Identification'),
        ('soil', 'Soil Report'),
    ]

    plot = models.ForeignKey('Plot', on_delete=models.CASCADE, related_name='files')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file = models.FileField(upload_to='plot_files/')
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_files')
    field_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='field_officer_files', null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plot} – {self.get_file_type_display()} – {self.uploaded_at.date()}"
class GrapseReport(models.Model):
    FILE_TYPE_CHOICES = [
        ('residue', 'Residue Analysis'),
        ('variety', 'Variety Identification'),
        ('soil', 'Soil Report'),
    ]

    plot = models.ForeignKey('Plot', on_delete=models.CASCADE, related_name='files')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file = models.FileField(upload_to='plot_files/')
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_files')
    field_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='field_officer_files', null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plot} – {self.get_file_type_display()} – {self.uploaded_at.date()}"
