from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework_gis.fields import GeometryField
from django.contrib.auth import get_user_model
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
    
    class Meta:
        model = CropType
        fields = ['id', 'crop_type', 'plantation_type', 'plantation_type_display', 'planting_method', 'planting_method_display', 'plantation_date']
    
    def get_plantation_date(self, obj):
        # Get plantation_date from the parent Farm instance passed through context
        farm = self.context.get('farm')
        if farm and hasattr(farm, 'plantation_date'):
            return farm.plantation_date.isoformat() if farm.plantation_date else None
        return None


class PlotSerializer(serializers.ModelSerializer):
    # Replace read-only method fields with writeable GeometryFields
    location = GeometryField(required=False, allow_null=True)
    boundary = GeometryField(required=False, allow_null=True)
    
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
    crop_type_id = serializers.PrimaryKeyRelatedField(
        source='crop_type',
        queryset=CropType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    plot = PlotSerializer(read_only=True)
    plot_id = serializers.PrimaryKeyRelatedField(
        source='plot',
        queryset=Plot.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    
    # Irrigation fields
    irrigation_type = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
    )
    motor_horsepower = serializers.FloatField(write_only=True, required=False, allow_null=True)
    pipe_width_inches = serializers.FloatField(write_only=True, required=False, allow_null=True)
    distance_motor_to_plot_m = serializers.FloatField(write_only=True, required=False, allow_null=True)
    plants_per_acre = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    flow_rate_lph = serializers.FloatField(write_only=True, required=False, allow_null=True)
    emitters_count = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    # Location fields
    location_lat = serializers.FloatField(write_only=True, required=False, allow_null=True)
    location_lng = serializers.FloatField(write_only=True, required=False, allow_null=True)
    boundary_geojson = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Spacing fields and calculated plants
    plants_in_field = serializers.ReadOnlyField()

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
            'crop_type_id',
            'farm_document',
            'plantation_date',
            'created_at',
            'updated_at',
            'spacing_a',
            'spacing_b',
            'plants_in_field',
            # Irrigation fields
            'irrigation_type',
            'motor_horsepower',
            'pipe_width_inches',
            'distance_motor_to_plot_m',
            'plants_per_acre',
            'flow_rate_lph',
            'emitters_count',
            # Location fields
            'location_lat',
            'location_lng',
            'boundary_geojson',
        ]
        read_only_fields = ['farm_uid', 'farm_owner', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create farm and irrigation in a single transaction"""
        from django.db import transaction
        from django.contrib.gis.geos import Point, GEOSGeometry
        
        # Extract irrigation data
        irrigation_type_id = validated_data.pop('irrigation_type', None)
        irrigation_type = None
        if irrigation_type_id:
            try:
                irrigation_type = IrrigationType.objects.get(id=irrigation_type_id)
            except IrrigationType.DoesNotExist:
                raise serializers.ValidationError(f"Irrigation type with ID {irrigation_type_id} does not exist")
        
        irrigation_data = {
            'irrigation_type': irrigation_type,
            'motor_horsepower': validated_data.pop('motor_horsepower', None),
            'pipe_width_inches': validated_data.pop('pipe_width_inches', None),
            'distance_motor_to_plot_m': validated_data.pop('distance_motor_to_plot_m', None),
            'plants_per_acre': validated_data.pop('plants_per_acre', None),
            'flow_rate_lph': validated_data.pop('flow_rate_lph', None),
            'emitters_count': validated_data.pop('emitters_count', None),
        }
        
        # Extract location data
        location_lat = validated_data.pop('location_lat', None)
        location_lng = validated_data.pop('location_lng', None)
        boundary_geojson = validated_data.pop('boundary_geojson', None)
        
        with transaction.atomic():
            # Create the farm
            farm = super().create(validated_data)
            
            # Create irrigation if irrigation type is provided
            if irrigation_data['irrigation_type']:
                irrigation_location = None
                
                # Set irrigation location
                if location_lat and location_lng:
                    irrigation_location = Point(location_lng, location_lat, srid=4326)
                elif boundary_geojson:
                    try:
                        boundary_data = json.loads(boundary_geojson)
                        irrigation_location = GEOSGeometry(json.dumps(boundary_data))
                    except (json.JSONDecodeError, Exception):
                        irrigation_location = Point(0, 0, srid=4326)
                else:
                    irrigation_location = Point(0, 0, srid=4326)
                
                # Create irrigation
                FarmIrrigation.objects.create(
                    farm=farm,
                    irrigation_type=irrigation_data['irrigation_type'],
                    location=irrigation_location,
                    motor_horsepower=irrigation_data['motor_horsepower'],
                    pipe_width_inches=irrigation_data['pipe_width_inches'],
                    distance_motor_to_plot_m=irrigation_data['distance_motor_to_plot_m'],
                    plants_per_acre=irrigation_data['plants_per_acre'],
                    flow_rate_lph=irrigation_data['flow_rate_lph'],
                    emitters_count=irrigation_data['emitters_count'],
                )
        
        return farm
    
    def to_representation(self, instance):
        # Override to pass farm instance to CropTypeSerializer
        representation = super().to_representation(instance)
        if 'crop_type' in representation and instance.crop_type:
            # Pass farm instance to crop_type serializer context
            crop_type_serializer = CropTypeSerializer(
                instance.crop_type,
                context={'farm': instance, **self.context}
            )
            representation['crop_type'] = crop_type_serializer.data
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
    crop_type_id = serializers.PrimaryKeyRelatedField(
        source='crop_type',
        queryset=CropType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    plot = PlotSerializer(read_only=True)
    plot_id = serializers.PrimaryKeyRelatedField(
        source='plot',
        queryset=Plot.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    
    # Spacing fields and calculated plants
    plants_in_field = serializers.ReadOnlyField()

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
            'crop_type_id',
            'farm_document',
            'plantation_date',
            'spacing_a',
            'spacing_b',
            'plants_in_field',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['farm_uid', 'farm_owner', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user

        # Auto-assign logic for field officers
        if user.has_role('fieldofficer'):
            if 'farm_owner' not in validated_data:
                # Try to auto-assign the most recent farmer
                try:
                    from .auto_assignment_service import AutoAssignmentService
                    recent_farmer = AutoAssignmentService.get_most_recent_farmer_by_field_officer(user)
                    
                    if recent_farmer:
                        validated_data['farm_owner'] = recent_farmer
                        validated_data['created_by'] = user
                    else:
                        raise serializers.ValidationError({
                            'farm_owner_id': 'No recent farmer found. Please specify farm_owner_id or create a farmer first.'
                        })
                except Exception as e:
                    raise serializers.ValidationError({
                        'farm_owner_id': f'Auto-assignment failed: {str(e)}. Please specify farm_owner_id.'
                    })

        # Default to the request user if farm_owner is not specified and not a field officer
        validated_data.setdefault('farm_owner', user)
        # created_by will be set in the view perform_create
        return super().create(validated_data)
    
    def to_representation(self, instance):
        # Override to pass farm instance to CropTypeSerializer
        representation = super().to_representation(instance)
        if 'crop_type' in representation and instance.crop_type:
            # Pass farm instance to crop_type serializer context
            crop_type_serializer = CropTypeSerializer(
                instance.crop_type,
                context={'farm': instance, **self.context}
            )
            representation['crop_type'] = crop_type_serializer.data
        return representation


class FarmDetailSerializer(FarmSerializer):
    images      = FarmImageSerializer(many=True, read_only=True)
    sensors     = FarmSensorSerializer(many=True, read_only=True)
    irrigations = FarmIrrigationSerializer(many=True, read_only=True)

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
