from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from .models import Farm, Plot, SoilType, CropType, IrrigationType
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class CompleteFarmerRegistrationService:
    """
    Unified service for complete farmer registration including:
    - Farmer (User) creation
    - Plot creation with geometry
    - Farm creation linking plot and farmer
    - Soil type, crop type, and irrigation setup
    """
    
    @staticmethod
    @transaction.atomic
    def register_complete_farmer(data, field_officer):
        """
        Complete farmer registration in a single atomic transaction
        
        Args:
            data: Dictionary containing all registration data
            field_officer: Field officer creating the registration
            
        Returns:
            Dictionary with created objects and their IDs
        """
        try:
            # Step 1: Create Farmer (User)
            farmer = CompleteFarmerRegistrationService._create_farmer(data.get('farmer', {}), field_officer)

            # Handle multiple plots, farms, and irrigations
            created_entities = []
            plots_data = data.get('plots', [])

            # Support single plot registration for backward compatibility
            if 'plot' in data and not plots_data:
                plots_data.append({
                    'plot': data.get('plot'),
                    'farm': data.get('farm'),
                    'irrigation': data.get('irrigation')
                })

            for entity_data in plots_data:
                plot = None
                if entity_data.get('plot'):
                    plot = CompleteFarmerRegistrationService._create_plot(
                        entity_data['plot'], farmer, field_officer
                    )

                farm = None
                farm_data = {}
                if entity_data.get('farm') and plot:
                    # Merge top-level farm data (like plantation_date) if not in individual farm data
                    farm_data = entity_data['farm'].copy() if entity_data.get('farm') else {}
                    
                    # If plantation_date is not in individual farm data, check top level
                    if not farm_data.get('plantation_date') and data.get('farm', {}).get('plantation_date'):
                        farm_data['plantation_date'] = data['farm']['plantation_date']
                    
                    # If other farm fields are missing, use top-level as fallback
                    if not farm_data.get('address') and data.get('farm', {}).get('address'):
                        farm_data['address'] = data['farm']['address']
                    if not farm_data.get('area_size') and data.get('farm', {}).get('area_size'):
                        farm_data['area_size'] = data['farm']['area_size']
                    if not farm_data.get('soil_type_name') and data.get('farm', {}).get('soil_type_name'):
                        farm_data['soil_type_name'] = data['farm']['soil_type_name']
                    if not farm_data.get('crop_type_name') and data.get('farm', {}).get('crop_type_name'):
                        farm_data['crop_type_name'] = data['farm']['crop_type_name']
                    # Handle plantation_type - check individual farm data first, then fallback to top-level
                    # Only merge from top-level if NOT present in individual farm data
                    if 'plantation_type_id' not in farm_data and 'plantation_type' not in farm_data:
                        # Not in individual farm data, check top-level
                        if data.get('farm', {}).get('plantation_type_id'):
                            farm_data['plantation_type_id'] = data['farm']['plantation_type_id']
                        elif data.get('farm', {}).get('plantation_type'):
                            plantation_type_str = data['farm']['plantation_type']
                            if isinstance(plantation_type_str, str) and plantation_type_str.isdigit():
                                farm_data['plantation_type_id'] = int(plantation_type_str)
                            else:
                                farm_data['plantation_type'] = plantation_type_str
                    # Handle planting_method - check individual farm data first, then fallback to top-level
                    # Only merge from top-level if NOT present in individual farm data
                    if 'planting_method_id' not in farm_data and 'planting_method' not in farm_data:
                        # Not in individual farm data, check top-level
                        if data.get('farm', {}).get('planting_method_id'):
                            farm_data['planting_method_id'] = data['farm']['planting_method_id']
                        elif data.get('farm', {}).get('planting_method'):
                            planting_method_str = data['farm']['planting_method']
                            if isinstance(planting_method_str, str) and planting_method_str.isdigit():
                                farm_data['planting_method_id'] = int(planting_method_str)
                            else:
                                farm_data['planting_method'] = planting_method_str
                    if not farm_data.get('spacing_a') and data.get('farm', {}).get('spacing_a'):
                        farm_data['spacing_a'] = data['farm']['spacing_a']
                    if not farm_data.get('spacing_b') and data.get('farm', {}).get('spacing_b'):
                        farm_data['spacing_b'] = data['farm']['spacing_b']
                    
                    farm = CompleteFarmerRegistrationService._create_farm(
                        farm_data, farmer, field_officer, plot
                    )

                irrigation = None
                if entity_data.get('irrigation') and farm:
                    irrigation = CompleteFarmerRegistrationService._create_farm_irrigation(
                        entity_data['irrigation'], farm, field_officer, farm_data
                    )
                created_entities.append({'plot': plot, 'farm': farm, 'irrigation': irrigation})

                # Manually sync each plot to all FastAPI services after unified registration
                if plot:
                    CompleteFarmerRegistrationService._sync_plot_to_fastapi_services(plot)

            return {
                'success': True,
                'farmer': farmer,
                'created_entities': created_entities,
                'message': 'Farmer registration completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Farmer registration failed: {str(e)}")
            raise serializers.ValidationError(f"Registration failed: {str(e)}")
    
    @staticmethod
    def _create_farmer(farmer_data, field_officer=None):
        """Create farmer user"""
        if not farmer_data:
            raise serializers.ValidationError("Farmer data is required")
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not farmer_data.get(field):
                raise serializers.ValidationError(f"Farmer {field} is required")
        
        # Check if username already exists
        if User.objects.filter(username=farmer_data['username']).exists():
            raise serializers.ValidationError(f"Username '{farmer_data['username']}' already exists")
        
        # Check if email already exists
        if User.objects.filter(email=farmer_data['email']).exists():
            raise serializers.ValidationError(f"Email '{farmer_data['email']}' already exists")
        
        # Check if phone_number already exists (if provided)
        phone_number = farmer_data.get('phone_number', '').strip() if farmer_data.get('phone_number') else ''
        if phone_number:
            # Clean phone number (remove non-digits, handle country code)
            import re
            cleaned_phone = re.sub(r'\D', '', phone_number)
            # If starts with 91 (country code), remove it to get 10 digits
            if cleaned_phone.startswith('91') and len(cleaned_phone) == 12:
                cleaned_phone = cleaned_phone[2:]
            
            # Validate it's exactly 10 digits after cleaning
            if len(cleaned_phone) != 10:
                raise serializers.ValidationError(f"Phone number must be 10 digits (provided: {phone_number})")
            
            # Check for duplicate with cleaned phone number
            if User.objects.filter(phone_number=cleaned_phone).exists():
                raise serializers.ValidationError(f"User with phone number '{phone_number}' already exists")
            
            # Use cleaned phone number for creation
            farmer_data['phone_number'] = cleaned_phone
        else:
            # Set to None if not provided (since phone_number is nullable)
            farmer_data['phone_number'] = None
        
        # Validate field officer has industry
        if field_officer and not field_officer.industry:
            raise serializers.ValidationError(
                f'Field officer "{field_officer.username}" must be assigned to an industry before creating farmers. '
                'Please contact administrator to assign an industry to this field officer account.'
            )
        
        # Get farmer role
        try:
            from users.models import Role
            farmer_role = Role.objects.get(name='farmer')
        except Role.DoesNotExist:
            raise serializers.ValidationError("Farmer role not found in system")
        
        # Create farmer with industry assignment from field officer
        farmer = User.objects.create_user(
            username=farmer_data['username'],
            email=farmer_data['email'],
            password=farmer_data['password'],
            first_name=farmer_data['first_name'],
            last_name=farmer_data['last_name'],
            phone_number=farmer_data.get('phone_number'),
            address=farmer_data.get('address', ''),
            village=farmer_data.get('village', ''),
            state=farmer_data.get('state', ''),
            district=farmer_data.get('district', ''),
            taluka=farmer_data.get('taluka', ''),
            role=farmer_role,
            created_by=field_officer,  # Set the field officer as creator
            industry=field_officer.industry if field_officer else None  # Assign industry from field officer
        )
        
        logger.info(
            f"Created farmer: {farmer.username} (ID: {farmer.id}) "
            f"by {field_officer.email if field_officer else 'system'} "
            f"in industry: {farmer.industry.name if farmer.industry else 'None'}"
        )
        return farmer
    
    @staticmethod
    def _create_plot(plot_data, farmer, field_officer):
        """Create plot and assign to farmer"""
        if not plot_data:
            return None
        
        # Validate required fields
        required_fields = ['gat_number', 'village', 'district', 'state']
        for field in required_fields:
            if not plot_data.get(field):
                raise serializers.ValidationError(f"Plot {field} is required")
        
        # Check for duplicate plot
        existing_plot = Plot.objects.filter(
            gat_number=plot_data['gat_number'],
            plot_number=plot_data.get('plot_number', ''),
            village=plot_data['village'],
            district=plot_data['district']
        ).first()
        
        if existing_plot:
            raise serializers.ValidationError(
                f"Plot GAT {plot_data['gat_number']} in {plot_data['village']} already exists"
            )
        
        # Create plot (skip FastAPI sync during unified registration)
        plot = Plot(
            gat_number=plot_data['gat_number'],
            plot_number=plot_data.get('plot_number', ''),
            village=plot_data['village'],
            taluka=plot_data.get('taluka', ''),
            district=plot_data['district'],
            state=plot_data['state'],
            country=plot_data.get('country', 'India'),
            pin_code=plot_data.get('pin_code', ''),
            farmer=farmer,  # Auto-assign to farmer
            created_by=field_officer
        )
        
        # Skip FastAPI sync during unified registration
        plot._skip_fastapi_sync = True
        
        # Handle geometry if provided
        if plot_data.get('location'):
            plot.location = CompleteFarmerRegistrationService._convert_geojson_to_geometry(
                plot_data['location']
            )
        
        if plot_data.get('boundary'):
            plot.boundary = CompleteFarmerRegistrationService._convert_geojson_to_geometry(
                plot_data['boundary']
            )
        
        plot.save()
        
        logger.info(f"Created plot: GAT {plot.gat_number} (ID: {plot.id}) for farmer {farmer.username}")
        return plot
    
    @staticmethod
    def _create_farm(farm_data, farmer, field_officer, plot=None):
        """Create farm and assign to farmer"""
        if not farm_data:
            return None
        
        # Validate required fields
        if not farm_data.get('address'):
            raise serializers.ValidationError("Farm address is required")
        
        if not farm_data.get('area_size'):
            raise serializers.ValidationError("Farm area_size is required")
        
        # Get soil type if provided
        soil_type = None
        if farm_data.get('soil_type_id'):
            try:
                soil_type = SoilType.objects.get(id=farm_data['soil_type_id'])
            except SoilType.DoesNotExist:
                raise serializers.ValidationError(f"Soil type ID {farm_data['soil_type_id']} not found")
        elif farm_data.get('soil_type_name'):
            soil_type, _ = SoilType.objects.get_or_create(
                name=farm_data['soil_type_name'],
                defaults={'description': f"Auto-created: {farm_data['soil_type_name']}"}
            )
        
        # Get crop type if provided
        crop_type = None
        if farm_data.get('crop_type_id'):
            try:
                crop_type = CropType.objects.get(id=farm_data['crop_type_id'])
            except CropType.DoesNotExist:
                raise serializers.ValidationError(f"Crop type ID {farm_data['crop_type_id']} not found")
        elif farm_data.get('crop_type_name'):
            # Get industry from field_officer for PlantationType/PlantingMethod creation
            industry = None
            if field_officer and hasattr(field_officer, 'industry') and field_officer.industry:
                industry = field_officer.industry
            
            # Get plantation_type if provided (can be ID, object, or string code/name for backward compatibility)
            plantation_type = None
            if farm_data.get('plantation_type_id'):
                try:
                    from .models import PlantationType
                    plantation_type = PlantationType.objects.get(id=farm_data['plantation_type_id'])
                except PlantationType.DoesNotExist:
                    raise serializers.ValidationError(f"Plantation type ID {farm_data['plantation_type_id']} not found")
            elif farm_data.get('plantation_type'):
                from .models import PlantationType
                pt_value = farm_data['plantation_type']
                # If it's already an object, use it directly
                if isinstance(pt_value, PlantationType):
                    plantation_type = pt_value
                # If it's a string, try to find by code or name, or create if not found
                elif isinstance(pt_value, str):
                    try:
                        # Try to find by code first, then by name
                        plantation_type = PlantationType.objects.filter(code=pt_value, industry=industry).first()
                        if not plantation_type:
                            plantation_type = PlantationType.objects.filter(name=pt_value, industry=industry).first()
                        # If still not found, try without industry filter (for backward compatibility)
                        if not plantation_type:
                            plantation_type = PlantationType.objects.filter(code=pt_value).first()
                        if not plantation_type:
                            plantation_type = PlantationType.objects.filter(name=pt_value).first()
                        
                        # If still not found, auto-create it
                        if not plantation_type:
                            # Capitalize first letter for name
                            pt_name = pt_value.replace('_', ' ').title()
                            # Use get_or_create with unique constraint fields (industry, code)
                            plantation_type, created = PlantationType.objects.get_or_create(
                                industry=industry,
                                code=pt_value,
                                defaults={
                                    'name': pt_name,
                                    'is_active': True,
                                    'description': f'Auto-created plantation type: {pt_name}'
                                }
                            )
                            if created:
                                logger.info(f"Auto-created PlantationType '{pt_name}' (code: {pt_value}) for industry '{industry.name if industry else 'None'}'")
                    except Exception as e:
                        logger.warning(f"Error looking up/creating plantation type '{pt_value}': {str(e)}")
            
            # Get planting_method if provided (can be ID, object, or string code/name for backward compatibility)
            planting_method = None
            if farm_data.get('planting_method_id'):
                try:
                    from .models import PlantingMethod
                    planting_method = PlantingMethod.objects.get(id=farm_data['planting_method_id'])
                except PlantingMethod.DoesNotExist:
                    raise serializers.ValidationError(f"Planting method ID {farm_data['planting_method_id']} not found")
            elif farm_data.get('planting_method'):
                from .models import PlantingMethod
                pm_value = farm_data['planting_method']
                # If it's already an object, use it directly
                if isinstance(pm_value, PlantingMethod):
                    planting_method = pm_value
                # If it's a string, try to find by code or name, or create if not found
                elif isinstance(pm_value, str):
                    try:
                        # Try to find by code first, then by name (filtered by plantation_type if available)
                        if plantation_type:
                            planting_method = PlantingMethod.objects.filter(
                                code=pm_value,
                                plantation_type=plantation_type
                            ).first()
                            if not planting_method:
                                planting_method = PlantingMethod.objects.filter(
                                    name=pm_value,
                                    plantation_type=plantation_type
                                ).first()
                        
                        # If still not found, try without plantation_type filter
                        if not planting_method:
                            planting_method = PlantingMethod.objects.filter(code=pm_value).first()
                        if not planting_method:
                            planting_method = PlantingMethod.objects.filter(name=pm_value).first()
                        
                        # If still not found, auto-create it
                        if not planting_method:
                            # Capitalize first letter for name
                            pm_name = pm_value.replace('_', ' ').title()
                            # Use get_or_create with unique constraint fields (plantation_type, industry, code)
                            planting_method, created = PlantingMethod.objects.get_or_create(
                                plantation_type=plantation_type,
                                industry=industry,
                                code=pm_value,
                                defaults={
                                    'name': pm_name,
                                    'is_active': True,
                                    'description': f'Auto-created planting method: {pm_name}'
                                }
                            )
                            if created:
                                logger.info(f"Auto-created PlantingMethod '{pm_name}' (code: {pm_value}) for industry '{industry.name if industry else 'None'}'")
                    except Exception as e:
                        logger.warning(f"Error looking up/creating planting method '{pm_value}': {str(e)}")
            
            # CRITICAL FIX: Find or create CropType that matches BOTH crop name AND plantation data
            # This prevents multiple farms with same crop but different plantation data from overwriting each other
            crop_type_name = farm_data['crop_type_name']
            
            if plantation_type or planting_method:
                # Look for existing CropType with same name AND plantation data
                crop_type = CropType.objects.filter(
                    crop_type=crop_type_name,
                    plantation_type=plantation_type,
                    planting_method=planting_method
                ).first()
                
                if not crop_type:
                    # Create new CropType with plantation data
                    crop_type = CropType.objects.create(
                        crop_type=crop_type_name,
                        plantation_type=plantation_type,
                        planting_method=planting_method
                    )
                    logger.info(f"Created CropType '{crop_type_name}' with plantation_type={plantation_type}, planting_method={planting_method}")
                else:
                    # Ensure plantation data is set (in case it was None before)
                    if crop_type.plantation_type != plantation_type or crop_type.planting_method != planting_method:
                        crop_type.plantation_type = plantation_type
                        crop_type.planting_method = planting_method
                        crop_type.save()
                        logger.info(f"Updated CropType '{crop_type_name}' with plantation data")
            else:
                # No plantation data, use simple get_or_create
                crop_type, _ = CropType.objects.get_or_create(
                    crop_type=crop_type_name,
                    defaults={}
                )
        
        # Parse plantation_date if provided
        plantation_date = None
        if farm_data.get('plantation_date'):
            try:
                from datetime import datetime
                # Handle string date format (YYYY-MM-DD)
                if isinstance(farm_data['plantation_date'], str):
                    plantation_date = datetime.strptime(farm_data['plantation_date'], '%Y-%m-%d').date()
                else:
                    # Already a date object
                    plantation_date = farm_data['plantation_date']
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid plantation_date format: {farm_data.get('plantation_date')}. Error: {str(e)}")
                plantation_date = None
        
        # Create farm
        farm = Farm.objects.create(
            address=farm_data['address'],
            area_size=farm_data['area_size'],
            farm_owner=farmer,  # Auto-assign to farmer
            created_by=field_officer,
            plot=plot,
            soil_type=soil_type,
            crop_type=crop_type,
            plantation_date=plantation_date,
            spacing_a=farm_data.get('spacing_a'),
            spacing_b=farm_data.get('spacing_b')
        )
        
        logger.info(f"Created farm: {farm.farm_uid} (ID: {farm.id}) for farmer {farmer.username} with plantation_date: {plantation_date}")
        return farm
    
    @staticmethod
    def _create_farm_irrigation(irrigation_data, farm, field_officer, farm_data=None):
        """Create farm irrigation system"""
        if not irrigation_data:
            return None
        
        from .models import FarmIrrigation
        
        # Get irrigation type
        irrigation_type = None
        if irrigation_data.get('irrigation_type_id'):
            try:
                irrigation_type = IrrigationType.objects.get(id=irrigation_data['irrigation_type_id'])
            except IrrigationType.DoesNotExist:
                raise serializers.ValidationError(f"Irrigation type ID {irrigation_data['irrigation_type_id']} not found")
        elif irrigation_data.get('irrigation_type_name'):
            irrigation_type, _ = IrrigationType.objects.get_or_create(
                name=irrigation_data['irrigation_type_name'],
                defaults={'description': f"Auto-created: {irrigation_data['irrigation_type_name']}"}
            )

        # Calculate plants_per_acre for drip irrigation if spacing is available
        plants_per_acre_val = irrigation_data.get('plants_per_acre')
        if irrigation_type and irrigation_type.name.lower() == 'drip' and not plants_per_acre_val:
            if farm_data and farm_data.get('spacing_a') and farm_data.get('spacing_b'):
                try:
                    spacing_a = float(farm_data['spacing_a'])
                    spacing_b = float(farm_data['spacing_b'])
                    # Assuming spacing is in feet. 1 acre = 43560 sq ft.
                    # If spacing is in meters, conversion is needed: 1 meter = 3.28084 feet
                    # For now, assuming feet as per standard agricultural practice in some regions.
                    if spacing_a > 0 and spacing_b > 0:
                        plants_per_acre_val = 43560 / (spacing_a * spacing_b)
                        logger.info(f"Calculated plants_per_acre: {plants_per_acre_val} for farm {farm.id}")
                except (ValueError, TypeError):
                    logger.warning(f"Could not calculate plants_per_acre for farm {farm.id} due to invalid spacing values.")
                    pass
        
        # Create irrigation with location (use farm plot location as default)
        irrigation_location = None
        if irrigation_data.get('location'):
            irrigation_location = CompleteFarmerRegistrationService._convert_geojson_to_geometry(
                irrigation_data['location']
            )
        elif farm.plot and farm.plot.location:
            # Use plot location as default for irrigation
            irrigation_location = farm.plot.location
        else:
            # Default location (center of farm area or a generic point)
            from django.contrib.gis.geos import Point
            irrigation_location = Point(0, 0)  # Default to 0,0 if no location available
        
        irrigation = FarmIrrigation.objects.create(
            farm=farm,
            irrigation_type=irrigation_type,
            location=irrigation_location,
            status=irrigation_data.get('status', True),
            # Irrigation-specific fields
            motor_horsepower=irrigation_data.get('motor_horsepower'),
            pipe_width_inches=irrigation_data.get('pipe_width_inches'),
            distance_motor_to_plot_m=irrigation_data.get('distance_motor_to_plot_m'),
            plants_per_acre=plants_per_acre_val,
            flow_rate_lph=irrigation_data.get('flow_rate_lph'),
            emitters_count=irrigation_data.get('emitters_count')
        )
        
        logger.info(f"Created irrigation: {irrigation.id} for farm {farm.farm_uid}")
        return irrigation
    
    @staticmethod
    def get_registration_summary(farmer, plot, farm, irrigation):
        """Get a summary of the complete registration"""
        from users.serializers import UserSerializer # Keep this import
        from .serializers import PlotSerializer, FarmSerializer, FarmIrrigationSerializer
        
        summary = {
            'plot': PlotSerializer(plot).data if plot else None,
            'farm': FarmSerializer(farm).data if farm else None,
            'irrigation': FarmIrrigationSerializer(irrigation).data if irrigation else None,
        }
        
        return summary
    
    @staticmethod
    def _convert_geojson_to_geometry(geojson_data):
        """
        Convert GeoJSON dictionary to Django GIS geometry object
        
        Args:
            geojson_data: Dictionary with GeoJSON format
            
        Returns:
            Django GIS geometry object
        """
        try:
            from django.contrib.gis.geos import GEOSGeometry
            import json
            
            if isinstance(geojson_data, dict):
                # Validate basic GeoJSON structure
                if 'type' not in geojson_data:
                    raise ValueError("GeoJSON must have 'type' field")
                if 'coordinates' not in geojson_data:
                    raise ValueError("GeoJSON must have 'coordinates' field")
                
                # Convert dict to JSON string, then to geometry
                geojson_string = json.dumps(geojson_data)
                return GEOSGeometry(geojson_string)
            elif isinstance(geojson_data, str):
                # Already a JSON string
                return GEOSGeometry(geojson_data)
            else:
                raise ValueError(f"Invalid geometry data type: {type(geojson_data)}")
                
        except Exception as e:
            logger.error(f"Error converting GeoJSON to geometry: {str(e)}")
            raise serializers.ValidationError(f"Invalid geometry data: {str(e)}")
    
    @staticmethod
    def _sync_plot_to_fastapi_services(plot):
        """
        Manually sync a plot to all FastAPI services after unified registration
        
        Args:
            plot: Plot instance to sync
        """
        logger.info(f"Starting manual sync of plot {plot.id} to all FastAPI services")
        
        # List of all sync services
        sync_services = [
            ('events.py', 'services', 'EventsSyncService', 'sync_plot_to_events'),
            ('soil.py/main.py', 'soil_services', 'SoilSyncService', 'sync_plot_to_soil'),
            ('Admin.py', 'admin_services', 'AdminSyncService', 'sync_plot_to_admin'),
            ('ET.py', 'et_services', 'ETSyncService', 'sync_plot_to_et'),
            ('field.py', 'field_services', 'FieldSyncService', 'sync_plot_to_field'),
        ]
        
        sync_results = {
            'successful': [],
            'failed': []
        }
        
        for service_name, module_name, class_name, method_name in sync_services:
            try:
                # Dynamically import and call the sync service
                module = __import__(f'farms.{module_name}', fromlist=[class_name])
                service_class = getattr(module, class_name)
                service_instance = service_class()
                sync_method = getattr(service_instance, method_name)
                
                # Call the sync method
                result = sync_method(plot)
                
                if result:
                    sync_results['successful'].append(service_name)
                    logger.info(f"✅ Successfully synced plot {plot.id} to {service_name}")
                else:
                    sync_results['failed'].append(f"{service_name} (returned False)")
                    logger.warning(f"⚠️ Sync to {service_name} returned False for plot {plot.id}")
                    
            except Exception as e:
                sync_results['failed'].append(f"{service_name} ({str(e)})")
                logger.error(f"❌ Failed to sync plot {plot.id} to {service_name}: {str(e)}")
        
        # Log summary
        logger.info(f"Plot {plot.id} sync summary: {len(sync_results['successful'])} successful, {len(sync_results['failed'])} failed")
        
        if sync_results['successful']:
            logger.info(f"✅ Successful syncs: {', '.join(sync_results['successful'])}")
        
        if sync_results['failed']:
            logger.warning(f"❌ Failed syncs: {', '.join(sync_results['failed'])}")
        
        return sync_results
