from django.contrib.gis.geos import Point
from django.db.models import Q
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db import models
from datetime import date, timedelta
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from users.multi_tenant_utils import filter_by_industry, get_user_industry
from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser
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
    GrapseReport,
)
from .serializers import (
    SoilTypeSerializer,
    CropTypeSerializer,
    PlantationTypeSerializer,
    PlantingMethodSerializer,
    FarmSerializer,
    FarmWithIrrigationSerializer,
    FarmDetailSerializer,
    FarmGeoSerializer,
    PlotSerializer,
    PlotGeoSerializer,
    FarmImageSerializer,
    FarmSensorSerializer,
    FarmIrrigationSerializer,
    GrapseReportSerializer
)


class IsOwnerOrAdminOrManager(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        # Farm object
        if isinstance(obj, Farm):
            return (
                obj.farm_owner == user
                or user.is_superuser
                or user.has_any_role(['admin', 'manager'])
                or (user.has_role('fieldofficer') and obj.created_by == user)
            )
        # Anything linked to Farm
        if hasattr(obj, 'farm'):
            farm = obj.farm
            return (
                farm.farm_owner == user
                or user.is_superuser
                or user.has_any_role(['admin', 'manager'])
                or (user.has_role('fieldofficer') and farm.created_by == user)
            )
        return False


class SoilTypeViewSet(viewsets.ModelViewSet):
    queryset = SoilType.objects.all()
    serializer_class = SoilTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class PlantationTypeViewSet(viewsets.ModelViewSet):
    queryset = PlantationType.objects.all()
    serializer_class = PlantationTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Apply multi-tenant filtering
        qs = filter_by_industry(qs, user)
        # Filter by plantation_type if provided
        plantation_type_id = self.request.query_params.get('plantation_type_id')
        if plantation_type_id:
            qs = qs.filter(plantation_type_id=plantation_type_id)
        # Filter by active status if requested
        if self.request.query_params.get('active_only') == 'true':
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        user_industry = get_user_industry(user)
        serializer.save(industry=user_industry)


class PlantingMethodViewSet(viewsets.ModelViewSet):
    queryset = PlantingMethod.objects.all()
    serializer_class = PlantingMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Apply multi-tenant filtering
        qs = filter_by_industry(qs, user)
        # Filter by plantation_type if provided
        plantation_type_id = self.request.query_params.get('plantation_type_id')
        if plantation_type_id:
            qs = qs.filter(plantation_type_id=plantation_type_id)
        # Filter by active status if requested
        if self.request.query_params.get('active_only') == 'true':
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        user_industry = get_user_industry(user)
        serializer.save(industry=user_industry)


class CropTypeViewSet(viewsets.ModelViewSet):
    queryset = CropType.objects.all()
    serializer_class = CropTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['industry', 'plantation_type', 'planting_method']
    search_fields = ['crop_type']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Apply multi-tenant filtering
        qs = filter_by_industry(qs, user)
        return qs

    def perform_create(self, serializer):
        """Auto-assign industry when creating crop type"""
        user = self.request.user
        user_industry = get_user_industry(user)
        serializer.save(industry=user_industry)


class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['soil_type', 'crop_type', 'farm_owner']
    search_fields = ['address', 'farm_owner__username']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FarmDetailSerializer
        if self.action == 'geojson':
            return FarmGeoSerializer
        if self.action == 'create':
            return FarmWithIrrigationSerializer
        return FarmSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrAdminOrManager()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Apply multi-tenant filtering
        qs = filter_by_industry(qs, user)

        # filter by owner id
        if owner_id := self.request.query_params.get('owner'):
            if owner_id.isdigit():
                qs = qs.filter(farm_owner_id=owner_id)

        # only my farms
        if self.request.query_params.get('my_farms') == 'true':
            qs = qs.filter(farm_owner=user)

        # geographic search
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        radius = self.request.query_params.get('radius')
        if lat and lng and radius:
            try:
                lat, lng, km = float(lat), float(lng), float(radius)
                user_loc = Point(lng, lat, srid=4326)
                qs = (
                    qs.filter(plot__location__distance_lte=(user_loc, D(km=km)))
                    .annotate(distance=Distance('plot__location', user_loc))
                    .order_by('distance')
                )
            except ValueError:
                pass

        # text search
        if search := self.request.query_params.get('search'):
            qs = qs.filter(
                Q(address__icontains=search) | Q(farm_owner__username__icontains=search)
            )

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        data = self.request.data

        # field officer must assign farm_owner
        farm_owner = None
        if user.has_role('fieldofficer'):
            farm_owner_id = data.get('farm_owner_id')
            if not farm_owner_id:
                raise ValidationError("Field Officer must assign a farm_owner.")
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                farm_owner = User.objects.get(pk=farm_owner_id)
            except User.DoesNotExist:
                raise ValidationError("Invalid farm_owner_id.")
        
        # Assign industry from user
        user_industry = get_user_industry(user)
        
        # Save the farm
        serializer.save(created_by=user, industry=user_industry, farm_owner=farm_owner)

    def perform_update(self, serializer):
        user = self.request.user
        if user.has_role('fieldofficer') and not self.request.data.get('farm_owner'):
            raise ValidationError("Field Officer must specify farm_owner.")
        serializer.save()

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer_class()(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='recent-farmers')
    def recent_farmers(self, request):
        """Get all farmers created by the field officer with their plot details"""
        user = request.user
        if not user.has_role('fieldofficer'):
            return Response({'error': 'Only field officers can access this endpoint'}, status=403)

        try:
            from django.contrib.auth import get_user_model
            from django.contrib.auth.models import User as AuthUser
            User = get_user_model()

            # Get all farmers created by this field officer
            farmers = User.objects.filter(
                created_by=user,
                role__name='farmer'
            ).select_related('role').order_by('-date_joined')

            def serialize_farmer_with_plots(farmer):
                """Serialize farmer with their plot details"""
                if not farmer:
                    return None

                # Get all plots for this farmer
                plots = Plot.objects.filter(farmer=farmer).select_related('farmer', 'created_by')
                plot_data = []

                for plot in plots:
                    # Generate the same plot ID format used by FastAPI services
                    def generate_fastapi_plot_id(plot_instance):
                        """Generate plot ID in the same format as FastAPI services"""
                        if plot_instance.gat_number and plot_instance.plot_number:
                            return f"{plot_instance.gat_number}_{plot_instance.plot_number}"
                        elif plot_instance.gat_number:
                            return plot_instance.gat_number
                        else:
                            return f"plot_{plot_instance.id}"

                    fastapi_plot_id = generate_fastapi_plot_id(plot)

                    # Get farm details for this plot
                    # Use select_related to fetch ForeignKey relationships efficiently
                    farms = plot.farms.all().select_related(
                        'crop_type', 
                        'soil_type'
                    ).prefetch_related('irrigations__irrigation_type')
                    
                    farm_details = []

                    for farm in farms:
                        # Get irrigation details
                        irrigation_details = []
                        for irrigation in farm.irrigations.all():
                            irrigation_info = {
                                'irrigation_type': irrigation.irrigation_type.get_name_display() if irrigation.irrigation_type else None,
                                'status': irrigation.status,
                                'motor_horsepower': irrigation.motor_horsepower,
                                'pipe_width_inches': irrigation.pipe_width_inches,
                                'flow_rate_lph': irrigation.flow_rate_lph,
                                'plants_per_acre': irrigation.plants_per_acre,
                                'emitters_count': irrigation.emitters_count,
                                'distance_motor_to_plot_m': irrigation.distance_motor_to_plot_m
                            }
                            irrigation_details.append(irrigation_info)

                        # Get plantation_type and planting_method display names from choice fields
                        plantation_type_name = None
                        planting_method_name = None
                        
                        if farm.crop_type:
                            if farm.crop_type.plantation_type:
                                plantation_type_name = farm.crop_type.get_plantation_type_display()
                            if farm.crop_type.planting_method:
                                planting_method_name = farm.crop_type.get_planting_method_display()

                        farm_info = {
                            'farm_uid': str(farm.farm_uid),
                            'address': farm.address,
                            'area_size': str(farm.area_size),
                            'soil_type': farm.soil_type.name if farm.soil_type else None,
                            'crop_type': farm.crop_type.crop_type if farm.crop_type else None,
                            'plantation_type': plantation_type_name,
                            'planting_method': planting_method_name,
                            'plantation_date': farm.plantation_date.isoformat() if farm.plantation_date else None,
                            'spacing_a': float(farm.spacing_a) if farm.spacing_a else None,
                            'spacing_b': float(farm.spacing_b) if farm.spacing_b else None,
                            'plants_in_field': farm.plants_in_field,
                            'created_at': farm.created_at.isoformat() if farm.created_at else None,
                            'irrigations': irrigation_details,
                            'irrigations_count': len(irrigation_details)
                        }
                        farm_details.append(farm_info)

                    plot_info = {
                        'id': plot.id,
                        'fastapi_plot_id': fastapi_plot_id,
                        'gat_number': plot.gat_number,
                        'plot_number': plot.plot_number,
                        'village': plot.village,
                        'taluka': plot.taluka,
                        'district': plot.district,
                        'state': plot.state,
                        'country': plot.country,
                        'pin_code': plot.pin_code,
                        'location': {
                            'type': 'Point',
                            'coordinates': [plot.location.x, plot.location.y] if plot.location else None
                        } if plot.location else None,
                        'boundary': {
                            'type': 'Polygon',
                            'coordinates': list(plot.boundary.coords) if plot.boundary else None
                        } if plot.boundary else None,
                        'created_at': plot.created_at.isoformat() if plot.created_at else None,
                        'updated_at': plot.updated_at.isoformat() if plot.updated_at else None,
                        'farms': farm_details,
                        'farms_count': len(farm_details)
                    }
                    plot_data.append(plot_info)

                # Farmer basic info
                farmer_data = {
                    'id': farmer.id,
                    'username': farmer.username,
                    'email': farmer.email,
                    'first_name': farmer.first_name,
                    'last_name': farmer.last_name,
                    'phone_number': farmer.phone_number,
                    'address': farmer.address,
                    'village': farmer.village,
                    'district': farmer.district,
                    'state': farmer.state,
                    'taluka': farmer.taluka,
                    'date_joined': farmer.date_joined.isoformat() if farmer.date_joined else None,
                    'role': {
                        'id': farmer.role.id,
                        'name': farmer.role.name,
                        'display_name': farmer.role.display_name
                    } if farmer.role else None,
                    'plots': plot_data,
                    'plots_count': len(plot_data)
                }

                return farmer_data

            # Serialize farmers with plot details
            farmers_data = [serialize_farmer_with_plots(farmer) for farmer in farmers]

            return Response({
                'farmers': farmers_data,
                'count': farmers.count()
            })

        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['post'], url_path='register-farmer')
    def register_farmer(self, request):
    
        """
        Complete farmer registration endpoint - creates farmer, plot, farm, and irrigation in one call
        Supports both single plot and multiple plots registration.
        
        Expected JSON structure (multiple plots):
        {
            "farmer": {
                "username": "testmulti",
                "email": "testmulti@example.com",
                "password": "farm@123",
                "first_name": "testmulti",
                "last_name": "Patil",
                "phone_number": "9870543211",
                "address": "Main Street",
                "village": "Test Village",
                "district": "Test District",
                "state": "Maharashtra",
                "taluka": "Test Taluka"
            },
            "plots": [
                {
                    "plot": {
                        "gat_number": "866",
                        "plot_number": "07",
                        "village": "Test Village",
                        "taluka": "Test Taluka",
                        "district": "Test District",
                        "state": "Maharashtra",
                        "country": "India",
                        "pin_code": "422605",
                        "location": {"type": "Point", "coordinates": [74.215, 19.567]}
                    },
                    "farm": {
                        "address": "Farm at GAT 866",
                        "area_size": "2.5",
                        "spacing_a": "3.0",
                        "spacing_b": "1.5",
                        "soil_type_name": "Black Soil",
                        "crop_type_name": "Sugarcane",
                        "plantation_type": "adsali"
                    },
                    "irrigation": {
                        "irrigation_type_name": "drip",
                        "status": true,
                        "flow_rate_lph": 2.0,
                        "emitters_count": 120
                    }
                },
                {
                    "plot": {
                        "gat_number": "904",
                        "plot_number": "05",
                        "village": "Test Village",
                        "taluka": "Test Taluka",
                        "district": "Test District",
                        "state": "Maharashtra",
                        "country": "India",
                        "pin_code": "422605",
                        "location": {"type": "Point", "coordinates": [74.218, 19.569]}
                    },
                    "farm": {
                        "address": "Farm at GAT 907",
                        "area_size": "3.0",
                        "spacing_a": "2.0",
                        "spacing_b": "1.0",
                        "soil_type_name": "Red Soil",
                        "crop_type_name": "sugarcane",
                        "plantation_type": "pre_seasonal"
                    },
                    "irrigation": {
                        "irrigation_type_name": "flood",
                        "motor_horsepower": 7.5,
                        "pipe_width_inches": 4.0,
                        "distance_motor_to_plot_m": 50.0
                    }
                }
            ]
        }
        
        For backward compatibility, single plot format is also supported:
        {
            "farmer": {...},
            "plot": {...},
            "farm": {...},
            "irrigation": {...}
        }
        
        Note: Irrigation type names should be lowercase: "drip", "flood", "sprinkler", etc.
        """
        user = request.user

        # Check if user is field officer
        if not user.has_role('fieldofficer'):
            return Response(
                {'error': 'Only field officers can register farmers'},
                status=403
            )

        try:
            from .farmer_registration_service import CompleteFarmerRegistrationService

            # Perform complete registration
            result = CompleteFarmerRegistrationService.register_complete_farmer(
                request.data,
                user
            )

            # Get detailed summary for all created entities
            registration_summary = []
            all_ids = {'farmer_id': result['farmer'].id, 'plots': []}

            for entities in result.get('created_entities', []):
                summary = CompleteFarmerRegistrationService.get_registration_summary(
                    result['farmer'],
                    entities.get('plot'),
                    entities.get('farm'),
                    entities.get('irrigation')
                )
                registration_summary.append(summary)
                all_ids['plots'].append({
                    'plot_id': entities['plot'].id if entities.get('plot') else None,
                    'farm_id': entities['farm'].id if entities.get('farm') else None,
                    'irrigation_id': entities['irrigation'].id if entities.get('irrigation') else None,
                })

            return Response({
                'success': True,
                'message': result['message'],
                'registration_summary': registration_summary,
                'ids': all_ids
            }, status=201)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)

    @action(detail=False, methods=['post'], url_path='quick-farmer-registration')
    def quick_farmer_registration(self, request):
        """
        Quick farmer registration - creates only farmer (simplified version)
        Expected JSON structure:
        {
            "username": "farmer123",
            "email": "farmer@example.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "9876543210",
            "address": "Village Address",
            "village": "Village Name",
            "district": "District Name",
            "state": "State Name",
            "taluka": "Taluka Name"
        }
        """
        user = request.user

        # Check if user is field officer
        if not user.has_role('fieldofficer'):
            return Response(
                {'error': 'Only field officers can register farmers'},
                status=403
            )

        try:
            from .farmer_registration_service import CompleteFarmerRegistrationService

            # Create farmer only
            farmer_data = request.data
            farmer = CompleteFarmerRegistrationService._create_farmer(farmer_data)

            from users.serializers import UserSerializer

            return Response({
                'success': True,
                'message': 'Farmer registered successfully',
                'farmer': UserSerializer(farmer).data,
                'farmer_id': farmer.id
            }, status=201)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)

    @action(detail=False, methods=['post'], url_path='sync-plots-to-apis')
    def sync_plots_to_apis(self, request):
        """
        Manually sync plots to all FastAPI services
        Expected JSON:
        {
            "plot_ids": [1, 2, 3],  // Optional: specific plot IDs
            "sync_all": true        // Optional: sync all plots
        }
        """
        user = request.user

        # Check if user is field officer or admin
        if not user.has_any_role(['fieldofficer', 'admin', 'manager']):
            return Response(
                {'error': 'Only field officers, admins, or managers can sync plots'},
                status=403
            )

        try:
            from .farmer_registration_service import CompleteFarmerRegistrationService
            from .models import Plot

            data = request.data
            plots_to_sync = []

            if data.get('plot_ids'):
                # Sync specific plots
                plot_ids = data['plot_ids']
                plots_to_sync = Plot.objects.filter(id__in=plot_ids)

                if len(plots_to_sync) != len(plot_ids):
                    found_ids = list(plots_to_sync.values_list('id', flat=True))
                    missing_ids = [pid for pid in plot_ids if pid not in found_ids]
                    return Response({
                        'success': False,
                        'error': f'Plots not found: {missing_ids}'
                    }, status=400)

            elif data.get('sync_all'):
                # Sync all plots
                plots_to_sync = Plot.objects.all()
            else:
                return Response({
                    'success': False,
                    'error': 'Either provide plot_ids or set sync_all=true'
                }, status=400)

            # Perform sync
            sync_summary = {
                'total_plots': len(plots_to_sync),
                'successful_syncs': 0,
                'failed_syncs': 0,
                'plot_results': []
            }

            for plot in plots_to_sync:
                try:
                    sync_results = CompleteFarmerRegistrationService._sync_plot_to_fastapi_services(plot)

                    plot_result = {
                        'plot_id': plot.id,
                        'gat_number': plot.gat_number,
                        'successful_services': sync_results['successful'],
                        'failed_services': sync_results['failed'],
                        'success_count': len(sync_results['successful']),
                        'failure_count': len(sync_results['failed'])
                    }

                    sync_summary['successful_syncs'] += len(sync_results['successful'])
                    sync_summary['failed_syncs'] += len(sync_results['failed'])
                    sync_summary['plot_results'].append(plot_result)

                except Exception as e:
                    plot_result = {
                        'plot_id': plot.id,
                        'gat_number': plot.gat_number,
                        'error': str(e),
                        'success_count': 0,
                        'failure_count': 5  # Assume all 5 services failed
                    }
                    sync_summary['failed_syncs'] += 5
                    sync_summary['plot_results'].append(plot_result)

            return Response({
                'success': True,
                'message': f'Sync completed for {len(plots_to_sync)} plots',
                'sync_summary': sync_summary
            }, status=200)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)

    @action(detail=False, methods=['get'], url_path='my-farmers')
    def my_farmers(self, request):
        """
        Get all farmers registered by the currently logged-in field officer
        Returns farmers with their associated plots, farms, and irrigation data
        """
        user = request.user

        # Check if user is field officer
        if not user.has_role('fieldofficer'):
            return Response(
                {'error': 'Only field officers can access this endpoint'},
                status=403
            )

        try:
            from .models import Plot, Farm
            from users.serializers import UserSerializer
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # Find all farmers who have plots or farms created by this field officer
            farmers_via_plots = User.objects.filter(
                plots__created_by=user
            ).distinct()

            farmers_via_farms = User.objects.filter(
                farms__created_by=user
            ).distinct()

            # Combine and get unique farmers
            farmer_ids = set()
            for farmer in farmers_via_plots:
                farmer_ids.add(farmer.id)
            for farmer in farmers_via_farms:
                farmer_ids.add(farmer.id)

            farmers = User.objects.filter(
                id__in=farmer_ids,
                role__name='farmer'
            ).order_by('-date_joined')

            # Prepare detailed response with related data
            farmers_data = []

            for farmer in farmers:
                # Get plots created by this field officer for this farmer
                plots = Plot.objects.filter(
                    farmer=farmer,
                    created_by=user
                ).order_by('-created_at')

                # Get farms created by this field officer for this farmer
                farms = Farm.objects.filter(
                    farm_owner=farmer,
                    created_by=user
                ).order_by('-created_at')

                # Count total irrigations across all farms
                total_irrigations = 0
                for farm in farms:
                    total_irrigations += farm.irrigations.count()

                farmer_data = {
                    'farmer': UserSerializer(farmer).data,
                    'registration_summary': {
                        'plots_count': plots.count(),
                        'farms_count': farms.count(),
                        'irrigations_count': total_irrigations,
                        'registration_date': farmer.date_joined.strftime('%Y-%m-%d %H:%M:%S') if farmer.date_joined else None,
                    },
                    'plots': [
                        {
                            'id': plot.id,
                            'gat_number': plot.gat_number,
                            'plot_number': plot.plot_number,
                            'village': plot.village,
                            'district': plot.district,
                            'state': plot.state,
                            'created_at': plot.created_at.strftime('%Y-%m-%d %H:%M:%S') if plot.created_at else None,
                            'has_location': bool(plot.location),
                            'has_boundary': bool(plot.boundary),
                        }
                        for plot in plots
                    ],
                    'farms': [
                        {
                            'id': farm.id,
                            'farm_uid': farm.farm_uid,
                            'address': farm.address,
                            'area_size': str(farm.area_size) if farm.area_size else None,
                            'soil_type': farm.soil_type.name if farm.soil_type else None,
                            'crop_type': farm.crop_type.crop_type if farm.crop_type else None,
                            'plantation_type': farm.crop_type.get_plantation_type_display() if farm.crop_type and farm.crop_type.plantation_type else None,
                            'planting_method': farm.crop_type.get_planting_method_display() if farm.crop_type and farm.crop_type.planting_method else None,
                            'created_at': farm.created_at.strftime('%Y-%m-%d %H:%M:%S') if farm.created_at else None,
                            'irrigations_count': farm.irrigations.count(),
                        }
                        for farm in farms
                    ]
                }
                farmers_data.append(farmer_data)

            # Summary statistics
            total_plots = sum(farmer['registration_summary']['plots_count'] for farmer in farmers_data)
            total_farms = sum(farmer['registration_summary']['farms_count'] for farmer in farmers_data)
            total_irrigations = sum(farmer['registration_summary']['irrigations_count'] for farmer in farmers_data)

            return Response({
                'success': True,
                'field_officer': {
                    'id': user.id,
                    'username': user.username,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                },
                'summary': {
                    'total_farmers': len(farmers_data),
                    'total_plots': total_plots,
                    'total_farms': total_farms,
                    'total_irrigations': total_irrigations,
                },
                'farmers': farmers_data
            }, status=200)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)

    @action(detail=False, methods=['get'], url_path='my-profile')
    def my_profile(self, request):
        """
        Get complete farmer profile with all agricultural data
        This endpoint is for farmers to fetch their complete profile including:
        - Personal details
        - All their plots with FastAPI plot IDs
        - Farm details (crop type, plantation type, planting method)
        - Irrigation systems details
        - GPS coordinates and boundaries
        """
        user = request.user

        # Check if user is a farmer
        if not user.has_role('farmer'):
            return Response({
                'error': 'Only farmers can access this endpoint'
            }, status=403)

        try:
            from .models import Plot, Farm
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # Generate the same plot ID format used by FastAPI services
            def generate_fastapi_plot_id(plot_instance):
                """Generate plot ID in the same format as FastAPI services"""
                if plot_instance.gat_number and plot_instance.plot_number:
                    return f"{plot_instance.gat_number}_{plot_instance.plot_number}"
                elif plot_instance.gat_number:
                    return plot_instance.gat_number
                else:
                    return f"plot_{plot_instance.id}"

            # Get all plots owned by this farmer
            plots = Plot.objects.filter(farmer=user).select_related('farmer', 'created_by')
            plot_data = []

            total_farms = 0
            total_irrigations = 0
            crop_types = set()
            plantation_types = set()
            irrigation_types = set()

            for plot in plots:
                fastapi_plot_id = generate_fastapi_plot_id(plot)

                # Get farm details for this plot
                farms = plot.farms.all().select_related('crop_type', 'soil_type').prefetch_related('irrigations__irrigation_type')
                farm_details = []

                for farm in farms:
                    total_farms += 1

                    # Collect statistics
                    if farm.crop_type and farm.crop_type.crop_type:
                        crop_types.add(farm.crop_type.crop_type)
                    if farm.crop_type and farm.crop_type.plantation_type:
                        plantation_types.add(farm.crop_type.get_plantation_type_display())

                    # Get irrigation details
                    irrigation_details = []
                    for irrigation in farm.irrigations.all():
                        total_irrigations += 1

                        if irrigation.irrigation_type:
                            irrigation_types.add(irrigation.irrigation_type.get_name_display())

                        irrigation_info = {
                            'id': irrigation.id,
                            'irrigation_type': irrigation.irrigation_type.get_name_display() if irrigation.irrigation_type else None,
                            'irrigation_type_code': irrigation.irrigation_type.name if irrigation.irrigation_type else None,
                            'location': {
                                'type': 'Point',
                                'coordinates': [irrigation.location.x, irrigation.location.y] if irrigation.location else None
                            } if irrigation.location else None,
                            'status': irrigation.status,
                            'status_display': 'Active' if irrigation.status else 'Inactive',
                            'motor_horsepower': irrigation.motor_horsepower,
                            'pipe_width_inches': irrigation.pipe_width_inches,
                            'distance_motor_to_plot_m': irrigation.distance_motor_to_plot_m,
                            'plants_per_acre': irrigation.plants_per_acre,
                            'flow_rate_lph': irrigation.flow_rate_lph,
                            'emitters_count': irrigation.emitters_count
                        }
                        irrigation_details.append(irrigation_info)

                    farm_info = {
                        'id': farm.id,
                        'farm_uid': str(farm.farm_uid),
                        'farm_owner': {
                            'id': farm.farm_owner.id,
                            'username': farm.farm_owner.username,
                            'full_name': f"{farm.farm_owner.first_name} {farm.farm_owner.last_name}".strip() or farm.farm_owner.username,
                            'email': farm.farm_owner.email,
                            'phone_number': farm.farm_owner.phone_number
                        } if farm.farm_owner else None,
                        'address': farm.address,
                        'area_size': str(farm.area_size),
                        'area_size_numeric': float(farm.area_size),
                        'plantation_date': farm.plantation_date.isoformat() if farm.plantation_date else None,
                        'spacing_a': float(farm.spacing_a) if farm.spacing_a else None,
                        'spacing_b': float(farm.spacing_b) if farm.spacing_b else None,
                        'plants_in_field': farm.plants_in_field,
                        'soil_type': {
                            'id': farm.soil_type.id,
                            'name': farm.soil_type.name
                        } if farm.soil_type else None,
                        'crop_type': {
                            'id': farm.crop_type.id,
                            'crop_type': farm.crop_type.crop_type,
                            'plantation_type': farm.crop_type.plantation_type,
                            'plantation_type_display': farm.crop_type.get_plantation_type_display() if farm.crop_type.plantation_type else None,
                            'planting_method': farm.crop_type.planting_method,
                            'planting_method_display': farm.crop_type.get_planting_method_display() if farm.crop_type.planting_method else None
                        } if farm.crop_type else None,
                        'farm_document': {
                            'name': farm.farm_document.name,
                            'url': farm.farm_document.url,
                            'size': farm.farm_document.size
                        } if farm.farm_document else None,
                        'created_at': farm.created_at.isoformat() if farm.created_at else None,
                        'updated_at': farm.updated_at.isoformat() if farm.updated_at else None,
                        'created_by': {
                            'id': farm.created_by.id,
                            'username': farm.created_by.username,
                            'full_name': f"{farm.created_by.first_name} {farm.created_by.last_name}".strip() or farm.created_by.username,
                            'email': farm.created_by.email,
                            'phone_number': farm.created_by.phone_number
                        } if farm.created_by else None,
                        'irrigations': irrigation_details,
                        'irrigations_count': len(irrigation_details)
                    }
                    farm_details.append(farm_info)

                plot_info = {
                    'id': plot.id,
                    'fastapi_plot_id': fastapi_plot_id,
                    'gat_number': plot.gat_number,
                    'plot_number': plot.plot_number,
                    'address': {
                        'village': plot.village,
                        'taluka': plot.taluka,
                        'district': plot.district,
                        'state': plot.state,
                        'country': plot.country,
                        'pin_code': plot.pin_code,
                        'full_address': f"{plot.village}, {plot.taluka}, {plot.district}, {plot.state}, {plot.country} - {plot.pin_code}".replace(', , ', ', ').replace('  ', ' ').strip(', ')
                    },
                    'coordinates': {
                        'location': {
                            'type': 'Point',
                            'coordinates': [plot.location.x, plot.location.y] if plot.location else None,
                            'latitude': plot.location.y if plot.location else None,
                            'longitude': plot.location.x if plot.location else None
                        } if plot.location else None,
                        'boundary': {
                            'type': 'Polygon',
                            'coordinates': list(plot.boundary.coords) if plot.boundary else None,
                            'has_boundary': bool(plot.boundary)
                        } if plot.boundary else {'type': 'Polygon', 'coordinates': None, 'has_boundary': False}
                    },
                    'timestamps': {
                        'created_at': plot.created_at.isoformat() if plot.created_at else None,
                        'updated_at': plot.updated_at.isoformat() if plot.updated_at else None
                    },
                    'ownership': {
                        'farmer': {
                            'id': plot.farmer.id,
                            'username': plot.farmer.username,
                            'full_name': f"{plot.farmer.first_name} {plot.farmer.last_name}".strip() or plot.farmer.username,
                            'email': plot.farmer.email,
                            'phone_number': plot.farmer.phone_number
                        } if plot.farmer else None,
                        'created_by': {
                            'id': plot.created_by.id,
                            'username': plot.created_by.username,
                            'full_name': f"{plot.created_by.first_name} {plot.created_by.last_name}".strip() or plot.created_by.username,
                            'email': plot.created_by.email,
                            'phone_number': plot.created_by.phone_number,
                            'role': plot.created_by.role.display_name if plot.created_by and plot.created_by.role else None
                        } if plot.created_by else None
                    },
                    'farms': farm_details,
                    'farms_count': len(farm_details)
                }
                plot_data.append(plot_info)

            # Farmer profile data
            farmer_profile = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'personal_info': {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'phone_number': user.phone_number,
                    'profile_picture': {
                        'url': user.profile_picture.url,
                        'name': user.profile_picture.name
                    } if user.profile_picture else None
                },
                'address_info': {
                    'address': user.address,
                    'village': user.village,
                    'district': user.district,
                    'state': user.state,
                    'taluka': user.taluka,
                    'full_address': f"{user.address}, {user.village}, {user.taluka}, {user.district}, {user.state}".replace(', , ', ', ').strip(', ')
                },
                'account_info': {
                    'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                    'updated_at': user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None
                },
                'role': {
                    'id': user.role.id,
                    'name': user.role.name,
                    'display_name': user.role.display_name
                } if user.role else None
            }

            # Agricultural summary
            agricultural_summary = {
                'total_plots': len(plot_data),
                'total_farms': total_farms,
                'total_irrigations': total_irrigations,
                'crop_types': list(crop_types),
                'plantation_types': list(plantation_types),
                'irrigation_types': list(irrigation_types),
                'total_farm_area': sum(float(farm['area_size']) for plot in plot_data for farm in plot['farms'] if farm['area_size'])
            }

            return Response({
                'success': True,
                'farmer_profile': farmer_profile,
                'agricultural_summary': agricultural_summary,
                'plots': plot_data,
                'fastapi_integration': {
                    'plot_ids_format': 'GAT_NUMBER_PLOT_NUMBER',
                    'compatible_services': ['Admin.py', 'ET.py', 'field.py', 'main.py', 'events.py'],
                    'note': 'Use fastapi_plot_id for calling FastAPI analysis services'
                }
            }, status=200)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)


class PlotViewSet(viewsets.ModelViewSet):
    queryset = Plot.objects.all()
    serializer_class = PlotSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOrManager]
    filterset_fields = ['gat_number', 'plot_number', 'village', 'taluka', 'state']
    search_fields = ['gat_number', 'plot_number', 'village', 'district']

    def get_serializer_class(self):
        if self.action == 'geojson':
            return PlotGeoSerializer
        return PlotSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Apply multi-tenant filtering
        qs = filter_by_industry(qs, user)

        if self.request.query_params.get('my_farms') == 'true':
            qs = qs.filter(farms__farm_owner=user)

        if farm_id := self.request.query_params.get('farm'):
            if farm_id.isdigit():
                qs = qs.filter(farms__id=farm_id)

        if self.request.query_params.get('has_boundary') == 'true':
            qs = qs.filter(boundary__isnull=False)

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        # Get user's industry
        user_industry = get_user_industry(user)
        # Set created_by for field officers or admin
        if user.has_any_role(['fieldofficer', 'admin', 'manager']):
            serializer.save(created_by=user, industry=user_industry)
        else:
            serializer.save(industry=user_industry)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer_class()(queryset, many=True)
        return Response(serializer.data)

    

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def public(self, request):
        """Public endpoint for plots with farm information - no authentication required"""
        
        # Get all plots with related data
        queryset = Plot.objects.all().select_related(
            'farmer', 
            'created_by'
        ).prefetch_related(
            'farms__crop_type',
            'farms__soil_type',
            'farms__irrigations__irrigation_type',
            'farms__farm_owner'
        )
        
        # Apply optional filters
        if gat_number := request.query_params.get('gat_number'):
            queryset = queryset.filter(gat_number=gat_number)
        
        if village := request.query_params.get('village'):
            queryset = queryset.filter(village__icontains=village)
        
        if district := request.query_params.get('district'):
            queryset = queryset.filter(district__icontains=district)
        
        if state := request.query_params.get('state'):
            queryset = queryset.filter(state__icontains=state)
        
        # Build response with farm information
        plots_data = []
        
        for plot in queryset:
            # Generate FastAPI plot ID
            if plot.gat_number and plot.plot_number:
                fastapi_plot_id = f"{plot.gat_number}_{plot.plot_number}"
            elif plot.gat_number:
                fastapi_plot_id = plot.gat_number
            else:
                fastapi_plot_id = f"plot_{plot.id}"
            
            # Get farms for this plot
            farms = plot.farms.all()
            farm_details = []
            
            for farm in farms:
                farm_info = {
                    'id': farm.id,
                    'plantation_date': farm.plantation_date.isoformat() if farm.plantation_date else None,
                    'plantation_type': farm.crop_type.get_plantation_type_display() if farm.crop_type and farm.crop_type.plantation_type else None,
                    'plantation_type_code': farm.crop_type.plantation_type if farm.crop_type and farm.crop_type.plantation_type else None,
                    'planting_method': farm.crop_type.get_planting_method_display() if farm.crop_type and farm.crop_type.planting_method else None,
                    'planting_method_code': farm.crop_type.planting_method if farm.crop_type and farm.crop_type.planting_method else None,

                    # IDs
                    'soil_type_id': farm.soil_type.id if farm.soil_type else None,
                    'crop_type_name': farm.crop_type.crop_type if farm.crop_type else None,  # <-- Added this line
                    # Crop/variety info
                    'crop_variety': getattr(farm, 'crop_variety', None),
                    'sugarcane_plantation_type': getattr(farm, 'sugarcane_plantation_type', None),
                    'sugarcane_planting_method': getattr(farm, 'sugarcane_planting_method', None),
                    'spacing_a': getattr(farm, 'spacing_a', None),
                    'spacing_b': getattr(farm, 'spacing_b', None),
                    'grapes_plantation_type': getattr(farm, 'grapes_plantation_type', None),
                    'variety_type': getattr(farm, 'variety_type', None),
                    'variety_subtype': getattr(farm, 'variety_subtype', None),
                    'variety_timing': getattr(farm, 'variety_timing', None),
                    'plant_age': getattr(farm, 'plant_age', None),

                    # Important farm dates
                    'foundation_pruning_date': farm.foundation_pruning_date.isoformat() if farm.foundation_pruning_date else None,
                    'fruit_pruning_date': farm.fruit_pruning_date.isoformat() if farm.fruit_pruning_date else None,
                    'last_harvesting_date': farm.last_harvesting_date.isoformat() if farm.last_harvesting_date else None,

                    # Irrigation info
                    'irrigations': [
                        {
                            'id': irrigation.id,
                            'type': irrigation.irrigation_type.name if irrigation.irrigation_type else None,
                          
                        } for irrigation in farm.irrigations.all()
                    ],

                    # Farm owner
                    'farm_owner': {
                        'id': farm.farm_owner.id,
                        'username': farm.farm_owner.username,
                        'full_name': f"{farm.farm_owner.first_name} {farm.farm_owner.last_name}".strip() or farm.farm_owner.username
                    } if farm.farm_owner else None
                }
                farm_details.append(farm_info)
            
            plot_data = {
                'id': plot.id,
                'fastapi_plot_id': fastapi_plot_id,
                'gat_number': plot.gat_number,
                'plot_number': plot.plot_number,
                'address': {
                    'village': plot.village,
                    'taluka': plot.taluka,
                    'district': plot.district,
                    'state': plot.state,
                    'country': plot.country,
                    'pin_code': plot.pin_code
                },
                'location': {
                    'type': 'Point',
                    'coordinates': [plot.location.x, plot.location.y] if plot.location else None,
                    'latitude': plot.location.y if plot.location else None,
                    'longitude': plot.location.x if plot.location else None
                } if plot.location else None,
                'boundary': {
                    'type': 'Polygon',
                    'coordinates': list(plot.boundary.coords) if plot.boundary else None,
                    'has_boundary': bool(plot.boundary)
                },
                'farmer': {
                    'id': plot.farmer.id,
                    'username': plot.farmer.username,
                    'full_name': f"{plot.farmer.first_name} {plot.farmer.last_name}".strip() or plot.farmer.username
                } if plot.farmer else None,
                'created_at': plot.created_at.isoformat() if plot.created_at else None,
                'updated_at': plot.updated_at.isoformat() if plot.updated_at else None,
                'farms': farm_details,
                'farms_count': len(farm_details)
            }
            plots_data.append(plot_data)
        
        return Response({
            'count': len(plots_data),
            'results': plots_data
        })


class FarmImageViewSet(viewsets.ModelViewSet):
    queryset = FarmImage.objects.all()
    serializer_class = FarmImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOrManager]
    filterset_fields = ['farm']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if farm_id := self.request.query_params.get('farm'):
            if farm_id.isdigit():
                qs = qs.filter(farm_id=farm_id)

        if self.request.query_params.get('my_farms') == 'true':
            qs = qs.filter(farm__farm_owner=user)

        if sd := self.request.query_params.get('start_date'):
            qs = qs.filter(uploaded_at__date__gte=sd)

        if ed := self.request.query_params.get('end_date'):
            qs = qs.filter(uploaded_at__date__lte=ed)

        if user.has_role('fieldofficer'):
            qs = qs.filter(farm__created_by=user)

        return qs


class FarmSensorViewSet(viewsets.ModelViewSet):
    queryset = FarmSensor.objects.all()
    serializer_class = FarmSensorSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOrManager]
    filterset_fields = ['farm', 'sensor_type', 'status']
    search_fields = ['name']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if farm_id := self.request.query_params.get('farm'):
            if farm_id.isdigit():
                qs = qs.filter(farm_id=farm_id)

        if self.request.query_params.get('my_farms') == 'true':
            qs = qs.filter(farm__farm_owner=user)

        if t := self.request.query_params.get('type'):
            qs = qs.filter(sensor_type__name=t)

        if st := self.request.query_params.get('status'):
            qs = qs.filter(status=(st.lower() == 'true'))

        if user.has_role('fieldofficer'):
            qs = qs.filter(farm__created_by=user)

        return qs


class FarmIrrigationViewSet(viewsets.ModelViewSet):
    queryset = FarmIrrigation.objects.select_related('farm', 'irrigation_type').all()
    serializer_class = FarmIrrigationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOrManager]
    filterset_fields = ['farm', 'irrigation_type', 'status']
    search_fields = ['irrigation_type__name']
    ordering_fields = ['status']
    ordering = ['-id']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Filter by farm ID if provided and valid
        farm_id = self.request.query_params.get('farm')
        if farm_id and farm_id.isdigit():
            qs = qs.filter(farm_id=int(farm_id))

        # Filter only the farms owned by current user if requested
        if self.request.query_params.get('my_farms') == 'true':
            qs = qs.filter(farm__farm_owner=user)

        # Filter by irrigation type name if provided
        irrigation_type_name = self.request.query_params.get('type')
        if irrigation_type_name:
            qs = qs.filter(irrigation_type__name__iexact=irrigation_type_name)

        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status is not None:
            if status.lower() in ['true', '1']:
                qs = qs.filter(status=True)
            elif status.lower() in ['false', '0']:
                qs = qs.filter(status=False)

        # Field officers can only see farms they created
        if hasattr(user, 'has_role') and user.has_role('fieldofficer'):
            qs = qs.filter(farm__created_by=user)

        return qs.select_related('farm', 'irrigation_type')

    def perform_create(self, serializer):
        # FarmIrrigation model doesn't have created_by field
        # The relationship is through farm.created_by
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get irrigation systems grouped by type"""
        from .models import IrrigationType
        irrigation_types = IrrigationType.objects.all()
        result = {}

        for irrigation_type in irrigation_types:
            count = self.get_queryset().filter(irrigation_type=irrigation_type).count()
            result[irrigation_type.name] = {
                'display_name': irrigation_type.get_name_display(),
                'count': count,
                'description': irrigation_type.description
            }

        return Response(result)
    
class GrapseReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Grapse Reports.
    Supports listing, creating, retrieving, updating, and deleting reports.
    """
    queryset = GrapseReport.objects.all().order_by('-uploaded_at')
    serializer_class = GrapseReportSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only logged-in users can access
    parser_classes = [MultiPartParser, FormParser]  # Handle file uploads

    def perform_create(self, serializer):
        # Automatically set the uploaded_by field to the logged-in user
        serializer.save(uploaded_by=self.request.user)
