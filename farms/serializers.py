from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework_gis.fields import GeometryField
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.gis.geos import Point
import json

from .models import (
    SoilType,
    CropType,
    PlantationType,
    PlantingMethod,
    Farm,
    Plot,
    FarmImage,
    FarmSensor,
    FarmIrrigation,
    IrrigationType,
    GrapseReport 
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class SoilTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoilType
        fields = ['id', 'name', 'description', 'properties']


class PlantationTypeSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    crop_type_id = serializers.PrimaryKeyRelatedField(
        source='crop_type',
        queryset=CropType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = PlantationType
        fields = ['id', 'industry', 'industry_name', 'crop_type', 'crop_type_id', 'name', 'code', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'crop_type']


class PlantingMethodSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    plantation_type_id = serializers.PrimaryKeyRelatedField(
        source='plantation_type',
        queryset=PlantationType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = PlantingMethod
        fields = ['id', 'industry', 'industry_name', 'plantation_type', 'plantation_type_id', 'name', 'code', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'plantation_type']


class CropTypeSerializer(serializers.ModelSerializer):
    # Plantation type and planting method are now CharField with choices
    plantation_type_display = serializers.CharField(source='get_plantation_type_display', read_only=True)
    planting_method_display = serializers.CharField(source='get_planting_method_display', read_only=True)
    plantation_date = serializers.SerializerMethodField()
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    
    class Meta:
        model = CropType
        fields = ['id', 'crop_type', 'industry', 'industry_name', 'plantation_type', 'plantation_type_display', 'planting_method', 'planting_method_display', 'plantation_date']
    
    def get_plantation_date(self, obj):
        # Get plantation_date from the parent Farm instance passed through context
        farm = self.context.get('farm')
        if farm and hasattr(farm, 'plantation_date'):
            return farm.plantation_date.isoformat() if farm.plantation_date else None
        return None


class PlotSerializer(serializers.ModelSerializer):
    # Replace read-only method fields with writeable GeometryFields
    # GeometryField accepts GeoJSON format: {"type": "Point/Polygon", "coordinates": [...]}
    location = GeometryField(
        required=False, 
        allow_null=True,
        help_text="Point geometry as GeoJSON: {\"type\": \"Point\", \"coordinates\": [longitude, latitude]}"
    )
    boundary = GeometryField(
        required=False, 
        allow_null=True,
        help_text="Polygon geometry as GeoJSON: {\"type\": \"Polygon\", \"coordinates\": [[[lng, lat], [lng, lat], ...]]}"
    )
    
    # Include farmer and created_by relationships
    farmer = UserSerializer(read_only=True)
    farmer_id = serializers.PrimaryKeyRelatedField(
        source='farmer',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Plot
        fields = [
            'id',
            'gat_number',
            'plot_number',
            'village',
            'taluka',
            'district',
            'state',
            'country',
            'pin_code',
            'location',
            'boundary',
            'farmer',
            'farmer_id',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['farmer', 'created_by', 'created_at', 'updated_at']
    
    def validate_boundary(self, value):
        """Validate that boundary is a Polygon if provided"""
        if value is not None:
            from django.contrib.gis.geos import GEOSGeometry
            if hasattr(value, 'geom_type'):
                if value.geom_type != 'Polygon':
                    raise serializers.ValidationError(
                        f"Boundary must be a Polygon geometry, got {value.geom_type}"
                    )
            elif isinstance(value, (str, dict)):
                # If it's still in GeoJSON format, validate it
                try:
                    import json
                    if isinstance(value, dict):
                        geojson_str = json.dumps(value)
                    else:
                        geojson_str = value
                    geom = GEOSGeometry(geojson_str)
                    if geom.geom_type != 'Polygon':
                        raise serializers.ValidationError(
                            f"Boundary must be a Polygon geometry, got {geom.geom_type}"
                        )
                except Exception as e:
                    raise serializers.ValidationError(f"Invalid boundary geometry: {str(e)}")
        return value


class FarmImageSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = FarmImage
        fields = [
            'id',
            'farm',
            'title',
            'image',
            'capture_date',
            'notes',
            'uploaded_by',
            'uploaded_at',
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at']

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class FarmSensorSerializer(serializers.ModelSerializer):
    location = GeometryField(required=False, allow_null=True)

    class Meta:
        model = FarmSensor
        fields = [
            'id',
            'farm',
            'name',
            'sensor_type',
            'location',
            'installation_date',
            'last_maintenance',
            'status',
        ]


class FarmIrrigationSerializer(serializers.ModelSerializer):
    location = GeometryField()
    irrigation_type_name = serializers.CharField(source='irrigation_type.name', read_only=True)
    irrigation_type_display = serializers.CharField(source='irrigation_type.get_name_display', read_only=True)
    farm_uid = serializers.CharField(source='farm.farm_uid_str', read_only=True)

    class Meta:
        model = FarmIrrigation
        fields = [
            'id',
            'farm',
            'farm_uid',
            'irrigation_type',
            'irrigation_type_name',
            'irrigation_type_display',
            'location',
            'status',
            # Technical specifications per irrigation type
            'motor_horsepower',
            'pipe_width_inches',
            'distance_motor_to_plot_m',
            'plants_per_acre',
            'flow_rate_lph',
            'emitters_count',
        ]
        read_only_fields = ['id', 'farm_uid', 'irrigation_type_name', 'irrigation_type_display']

    def validate(self, data):
        """Validate irrigation-specific fields based on irrigation type"""
        irrigation_type = data.get('irrigation_type')
        
        if irrigation_type:
            irrigation_type_name = irrigation_type.name if hasattr(irrigation_type, 'name') else str(irrigation_type)
            
            if irrigation_type_name == 'flood':
                # Flood irrigation requires: motor_horsepower, pipe_width_inches, distance_motor_to_plot_m
                if not data.get('motor_horsepower'):
                    raise serializers.ValidationError("Motor horsepower is required for flood irrigation.")
                if not data.get('pipe_width_inches'):
                    raise serializers.ValidationError("Pipe width is required for flood irrigation.")
                if not data.get('distance_motor_to_plot_m'):
                    raise serializers.ValidationError("Distance from motor to plot is required for flood irrigation.")
                    
            elif irrigation_type_name == 'drip':
                # Validation for drip irrigation fields is relaxed.
                # The service layer handles the calculation for plants_per_acre if not provided.
                pass
        
        return data


class FarmWithIrrigationSerializer(serializers.ModelSerializer):
    """Serializer for creating farms with irrigation in a single request"""

    farm_owner = UserSerializer(read_only=True)
    farm_owner_id = serializers.PrimaryKeyRelatedField(
        source='farm_owner',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    created_by = UserSerializer(read_only=True)

    soil_type = SoilTypeSerializer(read_only=True)
    soil_type_id = serializers.PrimaryKeyRelatedField(
        source='soil_type',
        queryset=SoilType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    crop_type = CropTypeSerializer(read_only=True)
    crop_type_name = serializers.CharField(
    write_only=True,
    required=False,
    allow_null=True,
    help_text="Provide the crop type name (e.g., 'grapes')"
)
    plot = PlotSerializer(read_only=True)
    plot_id = serializers.PrimaryKeyRelatedField(
        source='plot',
        queryset=Plot.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    # Sugarcane fields
    spacing_a = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    spacing_b = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    sugarcane_plantation_type = serializers.ChoiceField(choices=Farm.SUGARCANE_PLANTATION_CHOICES, required=False, allow_null=True)
    sugarcane_planting_method = serializers.ChoiceField(choices=Farm.SUGARCANE_PLANTING_METHOD_CHOICES, required=False, allow_null=True)

    # Grapes fields
    grapes_plantation_type = serializers.ChoiceField(choices=Farm.GRAPES_PLANTATION_CHOICES, required=False, allow_null=True)
    variety_type = serializers.ChoiceField(choices=Farm.VARIETY_TYPE_CHOICES, required=False, allow_null=True)
    variety_subtype = serializers.ChoiceField(choices=Farm.VARIETY_SUBTYPE_CHOICES, required=False, allow_null=True)
    variety_timing = serializers.ChoiceField(choices=Farm.VARIETY_TIMING_CHOICES, required=False, allow_null=True)
    plant_age = serializers.ChoiceField(choices=Farm.PLANT_AGE_CHOICES, required=False, allow_null=True)
    foundation_pruning_date = serializers.DateField(required=False, allow_null=True)
    fruit_pruning_date = serializers.DateField(required=False, allow_null=True)
    last_harvesting_date = serializers.DateField(required=False, allow_null=True)
    resting_period_days = serializers.IntegerField(required=False, allow_null=True)

    # Drip irrigation fields
    row_spacing = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    plant_spacing = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    flow_rate_liter_per_hour = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    emitters_per_plant = serializers.IntegerField(required=False, allow_null=True)

    # General irrigation fields (keep them NOT write_only so they show in response)
    irrigation_type = serializers.IntegerField(required=False, allow_null=True)
    motor_horsepower = serializers.FloatField(required=False, allow_null=True)
    pipe_width_inches = serializers.FloatField(required=False, allow_null=True)
    distance_motor_to_plot_m = serializers.FloatField(required=False, allow_null=True)
    plants_per_acre = serializers.IntegerField(required=False, allow_null=True)
    flow_rate_lph = serializers.FloatField(required=False, allow_null=True)
    emitters_count = serializers.IntegerField(required=False, allow_null=True)

    # Location fields
    location_lat = serializers.FloatField(required=False, allow_null=True)
    location_lng = serializers.FloatField(required=False, allow_null=True)
    boundary_geojson = serializers.CharField(required=False, allow_blank=True)

    # Calculated fields
    plants_in_field = serializers.ReadOnlyField()

    class Meta:
        model = Farm
        fields = [
            'id', 'farm_uid', 'farm_owner', 'farm_owner_id', 'created_by',
            'plot', 'plot_id', 'address', 'area_size',
            'soil_type', 'soil_type_id', 'crop_type', 'crop_type_name',
            'farm_document', 'plantation_date',
            # Sugarcane
            'spacing_a', 'spacing_b', 'sugarcane_plantation_type', 'sugarcane_planting_method',
            # Grapes
            'grapes_plantation_type', 'variety_type', 'variety_subtype', 'variety_timing', 'plant_age',
            'foundation_pruning_date', 'fruit_pruning_date', 'last_harvesting_date', 'resting_period_days',
            # Drip irrigation
            'row_spacing', 'plant_spacing', 'flow_rate_liter_per_hour', 'emitters_per_plant',
            # General irrigation
            'irrigation_type', 'motor_horsepower', 'pipe_width_inches', 'distance_motor_to_plot_m',
            'plants_per_acre', 'flow_rate_lph', 'emitters_count',
            # Location
            'location_lat', 'location_lng', 'boundary_geojson',
            # Calculated fields
            'plants_in_field',
            # timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = ['farm_uid', 'farm_owner', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user
        
        # 1. Setup metadata
        validated_data.setdefault('farm_owner', user)
        validated_data['created_by'] = user

        # 2. Separate Irrigation & Location data 
        # (Because these don't exist on the 'Farm' model)
        irrigation_type_id = validated_data.pop('irrigation_type', None)
        
        # We use a list to cleanly extract irrigation-only fields
        irrig_fields = ['motor_horsepower', 'pipe_width_inches', 'distance_motor_to_plot_m', 
                        'plants_per_acre', 'flow_rate_lph', 'emitters_count']
        irrigation_data = {f: validated_data.pop(f, None) for f in irrig_fields}

        location_lat = validated_data.pop('location_lat', None)
        location_lng = validated_data.pop('location_lng', None)
        boundary_geojson = validated_data.pop('boundary_geojson', None)
         # 3. Handle crop_type_name -> convert to CropType instance
        crop_type_name = validated_data.pop('crop_type_name', None)
        if crop_type_name:
            # Case-insensitive match
            crop_qs = CropType.objects.filter(crop_type__iexact=crop_type_name)
            if not crop_qs.exists():
                raise serializers.ValidationError({
                    'crop_type_name': f"CropType with name '{crop_type_name}' does not exist. "
                                    f"Available options: sugarcane, grapse."
                })
            crop_type_obj = crop_qs.first()  # pick the first match
            validated_data['crop_type'] = crop_type_obj



        with transaction.atomic():
            # 3. Create Farm
            # Now validated_data ONLY contains Farm model fields.
            # Grapes and Sugarcane data will save automatically here.
            farm = Farm.objects.create(**validated_data)

            # 4. Create Irrigation
            if irrigation_type_id:
                irrig_type_obj = IrrigationType.objects.get(id=irrigation_type_id)
                irrig_loc = Point(location_lng, location_lat, srid=4326) if location_lat else None
                
                FarmIrrigation.objects.create(
                    farm=farm,
                    irrigation_type=irrig_type_obj,
                    location=irrig_loc,
                    **irrigation_data
                )
        return farm

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # 1. Include nested relationships
        if instance.crop_type:
            representation['crop_type'] = CropTypeSerializer(instance.crop_type, context=self.context).data
        if instance.soil_type:
            representation['soil_type'] = SoilTypeSerializer(instance.soil_type, context=self.context).data
        if instance.plot:
            representation['plot'] = PlotSerializer(instance.plot, context=self.context).data

        # 2. Include Irrigation Data (Important!)
        # Your previous response was returning "irrigation: null"
        # We fetch the first irrigation record related to this farm
        irrigation = instance.irrigations.first()  # Uses the 'related_name' from your Model
        if irrigation:
            representation['irrigation'] = {
                'id': irrigation.id,
                'farm_uid': instance.farm_uid_str(),
                'irrigation_type': irrigation.irrigation_type.id if irrigation.irrigation_type else None,
                'irrigation_type_name': irrigation.irrigation_type.name if irrigation.irrigation_type else None,
                'irrigation_type_display': irrigation.irrigation_type.get_name_display() if irrigation.irrigation_type else None,
                'location': {
                    "type": "Point",
                    "coordinates": [irrigation.location.x, irrigation.location.y]
                } if irrigation.location else None,
                'status': irrigation.status,
                'motor_horsepower': irrigation.motor_horsepower,
                'pipe_width_inches': irrigation.pipe_width_inches,
                'distance_motor_to_plot_m': irrigation.distance_motor_to_plot_m,
                'plants_per_acre': irrigation.plants_per_acre,
                'flow_rate_lph': irrigation.flow_rate_lph,
                'emitters_count': irrigation.emitters_count,
            }
        else:
            representation['irrigation'] = None

        return representation


class FarmSerializer(serializers.ModelSerializer):
    farm_owner = UserSerializer(read_only=True)
    farm_owner_id = serializers.PrimaryKeyRelatedField(
        source='farm_owner',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    created_by = UserSerializer(read_only=True)

    soil_type = SoilTypeSerializer(read_only=True)
    soil_type_id = serializers.PrimaryKeyRelatedField(
        source='soil_type',
        queryset=SoilType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    crop_type = CropTypeSerializer(read_only=True)
    crop_type_name = serializers.CharField(
    write_only=True,
    required=False,
    allow_null=True,
    help_text="Provide the crop type name (e.g., 'grapes')"
)

    plot = PlotSerializer(read_only=True)
    plot_id = serializers.PrimaryKeyRelatedField(
        source='plot',
        queryset=Plot.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    
    plants_in_field = serializers.ReadOnlyField()

    # Sugarcane fields
    spacing_a = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    spacing_b = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    sugarcane_plantation_type = serializers.ChoiceField(choices=Farm.SUGARCANE_PLANTATION_CHOICES, required=False, allow_null=True)
    sugarcane_planting_method = serializers.ChoiceField(choices=Farm.SUGARCANE_PLANTING_METHOD_CHOICES, required=False, allow_null=True)

    # Grapes fields
    grapes_plantation_type = serializers.ChoiceField(choices=Farm.GRAPES_PLANTATION_CHOICES, required=False, allow_null=True)
    variety_type = serializers.ChoiceField(choices=Farm.VARIETY_TYPE_CHOICES, required=False, allow_null=True)
    variety_subtype = serializers.ChoiceField(choices=Farm.VARIETY_SUBTYPE_CHOICES, required=False, allow_null=True)
    variety_timing = serializers.ChoiceField(choices=Farm.VARIETY_TIMING_CHOICES, required=False, allow_null=True)
    plant_age = serializers.ChoiceField(choices=Farm.PLANT_AGE_CHOICES, required=False, allow_null=True)

    foundation_pruning_date = serializers.DateField(required=False, allow_null=True)
    fruit_pruning_date = serializers.DateField(required=False, allow_null=True)
    last_harvesting_date = serializers.DateField(required=False, allow_null=True)
    resting_period_days = serializers.IntegerField(required=False, allow_null=True)

    # Drip irrigation fields
    row_spacing = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    plant_spacing = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    flow_rate_liter_per_hour = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    emitters_per_plant = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
            model = Farm
            fields = [
                'id',
                'farm_uid',
                'farm_owner',
                'farm_owner_id',
                'created_by',
                'plot',
                'plot_id',
                'address',
                'area_size',
                'soil_type',
                'soil_type_id',
                'crop_type',
                'crop_type_name',
                'farm_document',
                'plantation_date',
                'spacing_a',
                'spacing_b',
                'sugarcane_plantation_type',   # added
                'sugarcane_planting_method',   # added
                'crop_variety',
                'grapes_plantation_type',
                'variety_type',
                'variety_subtype',
                'variety_timing',
                'plant_age',
                'plants_in_field',
                'foundation_pruning_date',
                'fruit_pruning_date',
                'last_harvesting_date',
                'resting_period_days',
                'row_spacing',
                'plant_spacing',
                'flow_rate_liter_per_hour',
                'emitters_per_plant',
                'created_at',
                'updated_at',
            ]
            read_only_fields = ['farm_uid', 'farm_owner', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user

        # Auto-assign farm_owner for field officers if not provided
        if user.has_role('fieldofficer') and not validated_data.get('farm_owner'):
            try:
                from .auto_assignment_service import AutoAssignmentService
                recent_farmer = AutoAssignmentService.get_most_recent_farmer_by_field_officer(user)
                if recent_farmer:
                    validated_data['farm_owner'] = recent_farmer
                else:
                    raise serializers.ValidationError({
                        'farm_owner_id': 'No recent farmer found. Please specify farm_owner_id.'
                    })
            except Exception as e:
                raise serializers.ValidationError({
                    'farm_owner_id': f'Auto-assignment failed: {str(e)}. Please specify farm_owner_id.'
                })

        # Default farm_owner if still not provided
        validated_data.setdefault('farm_owner', user)

        # Always set created_by to the current user
        validated_data['created_by'] = user

        # Default industry if not provided
        if 'industry' not in validated_data or validated_data['industry'] is None:
            from .utils import get_user_industry
            validated_data['industry'] = get_user_industry(user)
        # --- Handle crop_type_name ---
        crop_name = validated_data.pop('crop_type_name', None)
        if crop_name:
            try:
                validated_data['crop_type'] = CropType.objects.get(name__iexact=crop_name)
            except CropType.DoesNotExist:
                raise serializers.ValidationError({
                    'crop_type_name': f"CropType '{crop_name}' does not exist."
                })


        # --- Ensure grapes and sugarcane fields are present ---
        grapes_fields = [
            'grapes_plantation_type',
            'variety_type',
            'variety_subtype',
            'variety_timing',
            'plant_age',
            'foundation_pruning_date',
            'fruit_pruning_date',
            'last_harvesting_date',
            'resting_period_days',
            'row_spacing',
            'plant_spacing',
            'flow_rate_liter_per_hour',
            'emitters_per_plant',
            'crop_variety',
        ]

        sugarcane_fields = [
            'sugarcane_plantation_type',
            'sugarcane_planting_method',
        ]

        for field in grapes_fields + sugarcane_fields:
            validated_data.setdefault(field, None)  # Default to None if missing

        # Create farm with all validated data
        farm = Farm.objects.create(**validated_data)

        return farm

    def update(self, instance, validated_data):
        # Ensure update works for PATCH/PUT
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # --- Include related FarmIrrigation data if exists ---
        irrigation = getattr(instance, 'irrigation', None)
        if irrigation:
            representation['irrigation'] = {
                'id': irrigation.id,
                'farm_uid': irrigation.farm_uid,
                'irrigation_type': irrigation.irrigation_type.id if irrigation.irrigation_type else None,
                'irrigation_type_name': getattr(irrigation, 'irrigation_type_name', None),
                'irrigation_type_display': getattr(irrigation, 'irrigation_type_display', None),
                'motor_horsepower': irrigation.motor_horsepower,
                'pipe_width_inches': irrigation.pipe_width_inches,
                'distance_motor_to_plot_m': irrigation.distance_motor_to_plot_m,
                'plants_per_acre': irrigation.plants_per_acre,
                'flow_rate_lph': irrigation.flow_rate_lph,
                'emitters_count': irrigation.emitters_count,
                'location': {
                    'type': 'Point',
                    'coordinates': [irrigation.location.x, irrigation.location.y] if irrigation.location else [None, None]
                } if irrigation.location else None
            }
        else:
            # Always include irrigation key even if None
            representation['irrigation'] = None

        # --- Ensure grapes fields always exist ---
        grapes_fields = [
            'grapes_plantation_type',
            'variety_type',
            'variety_subtype',
            'variety_timing',
            'plant_age',
            'foundation_pruning_date',
            'fruit_pruning_date',
            'last_harvesting_date',
            'resting_period_days',
            'row_spacing',
            'plant_spacing',
            'flow_rate_liter_per_hour',
            'emitters_per_plant',
            'crop_variety',
        ]

        for field in grapes_fields:
            representation.setdefault(field, None)

        # --- Ensure sugarcane fields always exist ---
        sugarcane_fields = [
            'sugarcane_plantation_type',
            'sugarcane_planting_method',
        ]

        for field in sugarcane_fields:
            representation.setdefault(field, None)

        return representation


class FarmDetailSerializer(FarmSerializer):
    images      = FarmImageSerializer(many=True, read_only=True)
    sensors     = FarmSensorSerializer(many=True, read_only=True)
    irrigations = FarmIrrigationSerializer(source='farmirrigation_set',many=True, read_only=True)

    class Meta(FarmSerializer.Meta):
        fields = FarmSerializer.Meta.fields + [
            'images',
            'sensors',
            'irrigations',
        ]


class PlotGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Plot
        geo_field = 'boundary'
        fields = [
            'id',
            'gat_number',
            'plot_number',
            'village',
            'taluka',
            'district',
            'state',
            'country',
            'pin_code',
            'boundary',
        ]


class FarmGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Farm
        geo_field = 'plot__boundary'
        fields = [
            'id',
            'farm_uid',
            'address',
            'area_size',
            'soil_type',
            'crop_type',
            'created_at',
            'updated_at',
        ]

class GrapseReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrapseReport
        fields = '__all__'
