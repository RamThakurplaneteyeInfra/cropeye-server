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


class CropType(models.Model):
    PLANTATION_TYPE_CHOICES = [
        ('adsali',         'Adsali'),
        ('suru',           'Suru'),
        ('ratoon',         'Ratoon'),
        ('pre-seasonal',   'Pre-Seasonal'),
        ('post-seasonal',  'Post-Seasonal'),
        ('other',          'Other'),
    ]
    PLANTATION_METHOD_CHOICES = [
        ('3_bud',           '3 Bud Method'),
        ('2_bud',           '2 Bud Method'),
        ('1_bud',           '1 Bud Method'),
        ('1_bud_stip_Method','1 Bud (stip Method)'),
        ('other',           'Other'),
    ]

    crop_type        = models.CharField(max_length=100, blank=True)
    plantation_type  = models.CharField(max_length=100, choices=PLANTATION_TYPE_CHOICES, blank=True)
    planting_method  = models.CharField(max_length=100, choices=PLANTATION_METHOD_CHOICES, blank=True)

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
    farm_uid      = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    farm_owner    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='farms'
    )
    created_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_farms'
    )
    plot          = models.ForeignKey(
        Plot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='farms'
    )

    address       = models.TextField()
    area_size     = models.DecimalField(max_digits=10, decimal_places=2,
                                        help_text="Size in acres")
    soil_type     = models.ForeignKey(
        SoilType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    crop_type     = models.ForeignKey(
        CropType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    farm_document = models.FileField(upload_to='farm_documents/',
                                     null=True,
                                     blank=True)
    
    # Plantation date field
    plantation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when crops were planted"
    )
    
    # Spacing fields for plant calculation
    spacing_a     = models.DecimalField(max_digits=8, decimal_places=2,
                                        null=True, blank=True,
                                        help_text="Spacing A in meters")
    spacing_b     = models.DecimalField(max_digits=8, decimal_places=2,
                                        null=True, blank=True,
                                        help_text="Spacing B in meters")
    
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.farm_owner.username} – {self.farm_uid}"

    def farm_uid_str(self) -> str:
        """
        Returns a readable code:
          - If no plot: USERNAME-UUID
          - If plot with both gat & plot numbers: USERNAME-GAT-PLOT-UUID
        """
        uid = str(self.farm_uid).replace('-', '').upper()
        if self.plot and self.plot.gat_number and self.plot.plot_number:
            return f"{self.farm_owner.username}-{self.plot.gat_number}-{self.plot.plot_number}-{uid}"
        return f"{self.farm_owner.username}-{uid}"
    
    @property
    def plants_in_field(self):
        """
        Calculate number of plants in field using formula:
        total area * 43560 / (spacing_a * spacing_b)
        where spacing_a and spacing_b are used as-is without unit conversion
        """
        if not self.spacing_a or not self.spacing_b or not self.area_size:
            return None
        
        try:
            # Convert area_size from acres to square feet
            area_sq_ft = float(self.area_size) * 43560  # 1 acre = 43560 sq feet
            
            # Calculate plants using formula: total area * 43560 / (spacing_a * spacing_b)
            # spacing_a and spacing_b are used as-is without any unit conversion
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
            name = self.irrigation_type.name
            if name == 'flood':
                if not self.motor_horsepower:
                    raise ValidationError("Motor horsepower is required for flood irrigation.")
                if not self.pipe_width_inches:
                    raise ValidationError("Pipe width is required for flood irrigation.")
                if not self.distance_motor_to_plot_m:
                    raise ValidationError("Distance from motor to plot is required for flood irrigation.")
            elif name == 'drip':
                # These fields are now optional as they can be calculated or are not always required.
                # We can keep some soft validation if needed, but for now, we'll relax it.
                # For example, if flow_rate is given, emitters_count might be expected.
                if self.flow_rate_lph and not self.emitters_count:
                    # This is an example of a softer validation. For now, we remove the strict checks.
                    pass
                # The strict check for plants_per_acre is removed to allow for automatic calculation.

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
