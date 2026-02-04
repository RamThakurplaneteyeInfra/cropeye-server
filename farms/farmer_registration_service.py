from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from .models import Farm, Plot, SoilType, CropType, IrrigationType
from users.multi_tenant_utils import get_user_industry
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
            # Debug: Log incoming data structure
            logger.info(f"register_complete_farmer called with data keys: {list(data.keys())}")
            if 'plot' in data:
                logger.info(f"Single plot format - plot keys: {list(data.get('plot', {}).keys())}")
                logger.info(f"Boundary in data['plot']: {'boundary' in data.get('plot', {})}, value: {data.get('plot', {}).get('boundary')}")
            if 'plots' in data:
                logger.info(f"Multiple plots format - {len(data.get('plots', []))} plots")
            
            # Step 1: Create Farmer (User)
            farmer = CompleteFarmerRegistrationService._create_farmer(data.get('farmer', {}), field_officer)

            # Handle multiple plots, farms, and irrigations
            created_entities = []
            plots_data = data.get('plots', [])

            # Support single plot registration for backward compatibility
            if 'plot' in data and not plots_data:
                plot_data_dict = data.get('plot', {})
                logger.info(f"Converting single plot format - plot_data keys: {list(plot_data_dict.keys())}")
                logger.info(f"Boundary in single plot data: {'boundary' in plot_data_dict}, value: {plot_data_dict.get('boundary')}")
                plots_data.append({
                    'plot': plot_data_dict,
                    'farm': data.get('farm'),
                    'irrigation': data.get('irrigation')
                })

            for idx, entity_data in enumerate(plots_data):
                plot = None
                if entity_data.get('plot'):
                    plot_data_to_create = entity_data['plot']
                    logger.info(f"Processing plot {idx+1} - plot_data keys: {list(plot_data_to_create.keys())}")
                    logger.info(f"Boundary in entity_data['plot']: {'boundary' in plot_data_to_create}, value type: {type(plot_data_to_create.get('boundary'))}, value: {plot_data_to_create.get('boundary')}")
                    plot = CompleteFarmerRegistrationService._create_plot(
                        plot_data_to_create, farmer, field_officer
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
        
        # Debug: Log what plot_data contains at the start of _create_plot
        logger.info(f"_create_plot called - plot_data keys: {list(plot_data.keys())}")
        logger.info(f"Boundary in plot_data: {'boundary' in plot_data}, value type: {type(plot_data.get('boundary'))}, value: {plot_data.get('boundary')}")
        
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
        
        # Get industry from field officer
        industry = get_user_industry(field_officer) if field_officer else None
        
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
            created_by=field_officer,
            industry=industry  # Assign industry from field officer
        )
        
        # Skip FastAPI sync during unified registration
        plot._skip_fastapi_sync = True
        
        # Handle geometry if provided
        # Location (Point)
        if plot_data.get('location'):
            try:
                location_geom = CompleteFarmerRegistrationService._convert_geojson_to_geometry(
                plot_data['location']
            )
                if location_geom:
                    plot.location = location_geom
                    logger.info(f"Set plot location: {location_geom}")
            except Exception as e:
                logger.error(f"Error setting plot location: {str(e)}")
                raise serializers.ValidationError(f"Invalid location geometry: {str(e)}")
        
        # Boundary (Polygon) - IMPORTANT: Only set if explicitly provided
        if 'boundary' in plot_data and plot_data.get('boundary') is not None:
            try:
                logger.info(f"Processing boundary data: {type(plot_data['boundary'])}")
                boundary_geom = CompleteFarmerRegistrationService._convert_geojson_to_geometry(
                plot_data['boundary']
            )
                if boundary_geom:
                    # Validate it's actually a polygon
                    if boundary_geom.geom_type != 'Polygon':
                        raise ValueError(f"Boundary must be a Polygon, got {boundary_geom.geom_type}")
                    
                    plot.boundary = boundary_geom
                    logger.info(f"Set plot boundary: {boundary_geom.geom_type} with {len(boundary_geom.coords[0])} points")
                else:
                    # Explicitly set to None if conversion returned None
                    plot.boundary = None
                    logger.warning("Boundary conversion returned None, setting boundary to None")
            except Exception as e:
                logger.error(f"Error setting plot boundary: {str(e)}", exc_info=True)
                # Don't fail the entire registration if boundary is invalid, just log it
                # But still raise the error so user knows about it
                raise serializers.ValidationError(f"Invalid boundary geometry: {str(e)}")
        else:
            logger.info(f"Boundary not provided in plot_data (boundary key present: {'boundary' in plot_data}, value: {plot_data.get('boundary')})")
        # If boundary is not in plot_data at all, leave it as None (don't create default)
        
        plot.save()
        
        # Log the saved geometry for debugging
        if plot.boundary:
            logger.info(f"Saved plot boundary: {plot.boundary.geom_type}, area: {plot.boundary.area if hasattr(plot.boundary, 'area') else 'N/A'}")
        else:
            logger.info("Plot saved without boundary (boundary is None)")
        
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
            # Get plantation_type and planting_method as strings (choice values)
            # Support both direct string values and backward compatibility with IDs
            plantation_type_str = farm_data.get('plantation_type') or ''
            planting_method_str = farm_data.get('planting_method') or ''
            
            # Debug logging
            logger.info(f"Received plantation_type: {farm_data.get('plantation_type')}, planting_method: {farm_data.get('planting_method')}")
            logger.info(f"Initial values - plantation_type_str: '{plantation_type_str}', planting_method_str: '{planting_method_str}'")
            
            # If IDs are provided (backward compatibility), try to get the code/name
            if farm_data.get('plantation_type_id'):
                try:
                    from .models import PlantationType
                    pt_obj = PlantationType.objects.get(id=farm_data['plantation_type_id'])
                    plantation_type_str = pt_obj.code if pt_obj.code else pt_obj.name
                    logger.info(f"Resolved plantation_type from ID: '{plantation_type_str}'")
                except PlantationType.DoesNotExist:
                    logger.warning(f"Plantation type ID {farm_data['plantation_type_id']} not found")
                    plantation_type_str = ''
            
            if farm_data.get('planting_method_id'):
                try:
                    from .models import PlantingMethod
                    pm_obj = PlantingMethod.objects.get(id=farm_data['planting_method_id'])
                    planting_method_str = pm_obj.code if pm_obj.code else pm_obj.name
                    logger.info(f"Resolved planting_method from ID: '{planting_method_str}'")
                except PlantingMethod.DoesNotExist:
                    logger.warning(f"Planting method ID {farm_data['planting_method_id']} not found")
                    planting_method_str = ''
            
            # Normalize choice values
            # Map common variations to standard choice values
            plantation_type_mapping = {
                'adsali': 'adsali',
                'suru': 'suru',
                'ratoon': 'ratoon',
                'pre-seasonal': 'pre-seasonal',
                'pre_seasonal': 'pre_seasonal',
                'post-seasonal': 'post-seasonal',
                'post_seasonal': 'post-seasonal',
            }
            
            planting_method_mapping = {
                '3_bud': '3_bud',
                '2_bud': '2_bud',
                '1_bud': '1_bud',
                '1_bud_stip_method': '1_bud_stip_Method',
                '1_bud_stip_Method': '1_bud_stip_Method',
                'other': 'other',
            }
            
            # Normalize plantation_type
            if plantation_type_str:
                plantation_type_str = str(plantation_type_str).lower().strip()
                plantation_type_str = plantation_type_mapping.get(plantation_type_str, plantation_type_str)
                # Validate against choices
                valid_plantation_types = ['adsali', 'suru', 'ratoon', 'pre-seasonal', 'pre_seasonal', 'post-seasonal', 'other']
                if plantation_type_str not in valid_plantation_types:
                    logger.warning(f"Invalid plantation_type '{plantation_type_str}', defaulting to 'other'")
                    plantation_type_str = 'other'
            else:
                plantation_type_str = ''  # Empty string for blank=True CharField
            
            # Normalize planting_method
            if planting_method_str:
                planting_method_str = str(planting_method_str).lower().strip()
                planting_method_str = planting_method_mapping.get(planting_method_str, planting_method_str)
                # Validate against choices
                valid_planting_methods = ['3_bud', '2_bud', '1_bud', '1_bud_stip_Method', 'other']
                if planting_method_str not in valid_planting_methods:
                    logger.warning(f"Invalid planting_method '{planting_method_str}', defaulting to 'other'")
                    planting_method_str = 'other'
            else:
                planting_method_str = ''  # Empty string for blank=True CharField
            
            logger.info(f"Final normalized values - plantation_type: '{plantation_type_str}', planting_method: '{planting_method_str}'")
            
            # Find or create CropType that matches BOTH crop name AND plantation data
            crop_type_name = farm_data['crop_type_name']
            
            # Get industry from field officer
            industry = get_user_industry(field_officer) if field_officer else None
            
            # Use get_or_create with all fields to ensure uniqueness (including industry)
            crop_type, created = CropType.objects.get_or_create(
                crop_type=crop_type_name,
                plantation_type=plantation_type_str if plantation_type_str else '',
                planting_method=planting_method_str if planting_method_str else '',
                industry=industry,
                defaults={}
            )
            
            if created:
                logger.info(f"Created CropType '{crop_type_name}' with plantation_type={plantation_type_str}, planting_method={planting_method_str}, industry={industry}")
            else:
                # Ensure plantation data and industry are set (in case they were None before)
                needs_update = False
                if crop_type.plantation_type != plantation_type_str or crop_type.planting_method != planting_method_str:
                    crop_type.plantation_type = plantation_type_str if plantation_type_str else ''
                    crop_type.planting_method = planting_method_str if planting_method_str else ''
                    needs_update = True
                if crop_type.industry != industry:
                    crop_type.industry = industry
                    needs_update = True
                if needs_update:
                    crop_type.save()
                    logger.info(f"Updated CropType '{crop_type_name}' with plantation data and industry")
        
        # Parse plantation_date if provided
        plantation_date = None
        plantation_date_input = farm_data.get('plantation_date')
        logger.info(f"Received plantation_date: {plantation_date_input} (type: {type(plantation_date_input)})")
        
        if plantation_date_input:
            try:
                from datetime import datetime
                # Handle string date format (YYYY-MM-DD)
                if isinstance(plantation_date_input, str):
                    # Try multiple date formats
                    date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%m-%d-%Y', '%m/%d/%Y']
                    plantation_date = None
                    for date_format in date_formats:
                        try:
                            plantation_date = datetime.strptime(plantation_date_input.strip(), date_format).date()
                            logger.info(f"Successfully parsed plantation_date '{plantation_date_input}' using format '{date_format}'")
                            break
                        except ValueError:
                            continue
                    
                    if plantation_date is None:
                        raise ValueError(f"Could not parse date '{plantation_date_input}' with any known format")
                elif hasattr(plantation_date_input, 'date'):  # datetime object
                    plantation_date = plantation_date_input.date() if hasattr(plantation_date_input, 'date') else plantation_date_input
                elif isinstance(plantation_date_input, type(None)):
                    plantation_date = None
                else:
                    # Already a date object
                    plantation_date = plantation_date_input
                    logger.info(f"Using plantation_date as date object: {plantation_date}")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid plantation_date format: {plantation_date_input}. Error: {str(e)}", exc_info=True)
                plantation_date = None
        else:
            logger.info("No plantation_date provided in farm_data")
        
        # Get crop_variety if provided
        crop_variety = farm_data.get('crop_variety', '').strip() if farm_data.get('crop_variety') else None
        if crop_variety == '':
            crop_variety = None
        
        # Get industry from field officer
        industry = get_user_industry(field_officer) if field_officer else None
        
        # Create farm
        farm = Farm.objects.create(
        address=farm_data['address'],
        area_size=farm_data['area_size'],
        farm_owner=farmer,
        created_by=field_officer,
        plot=plot,
        soil_type=soil_type,
        crop_type=crop_type,
        plantation_date=plantation_date,
        spacing_a=farm_data.get('spacing_a'),
        spacing_b=farm_data.get('spacing_b'),
        crop_variety=crop_variety,
        industry=industry,
        
        # Add the rest of your fields
        sugarcane_plantation_type=farm_data.get('sugarcane_plantation_type'),
        sugarcane_planting_method=farm_data.get('sugarcane_planting_method'),
        grapes_plantation_type=farm_data.get('grapes_plantation_type'),
        variety_type=farm_data.get('variety_type'),
        variety_subtype=farm_data.get('variety_subtype'),
        variety_timing=farm_data.get('variety_timing'),
        plant_age=farm_data.get('plant_age'),
        foundation_pruning_date=farm_data.get('foundation_pruning_date'),
        fruit_pruning_date=farm_data.get('fruit_pruning_date'),
        last_harvesting_date=farm_data.get('last_harvesting_date'),
        resting_period_days=farm_data.get('resting_period_days'),
        row_spacing=farm_data.get('row_spacing'),
        plant_spacing=farm_data.get('plant_spacing'),
        flow_rate_liter_per_hour=farm_data.get('flow_rate_liter_per_hour'),
        emitters_per_plant=farm_data.get('emitters_per_plant'),
    )

        
        logger.info(f"Created farm: {farm.farm_uid} (ID: {farm.id}) for farmer {farmer.username} with plantation_date: {plantation_date}, crop_variety: {crop_variety}")
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
            geojson_data: Dictionary with GeoJSON format or string
            
        Returns:
            Django GIS geometry object (Point, Polygon, etc.)
        """
        try:
            from django.contrib.gis.geos import GEOSGeometry, Point, Polygon
            import json
            
            if geojson_data is None:
                return None
            
            # Handle string input (JSON string)
            if isinstance(geojson_data, str):
                try:
                    # Try to parse as JSON first
                    geojson_data = json.loads(geojson_data)
                except json.JSONDecodeError:
                    # If not valid JSON, try direct GEOSGeometry creation
                    return GEOSGeometry(geojson_data)
            
            # Handle dict input (GeoJSON format)
            if isinstance(geojson_data, dict):
                # Validate basic GeoJSON structure
                if 'type' not in geojson_data:
                    raise ValueError("GeoJSON must have 'type' field")
                if 'coordinates' not in geojson_data:
                    raise ValueError("GeoJSON must have 'coordinates' field")
                
                geom_type = geojson_data.get('type', '').lower()
                coordinates = geojson_data.get('coordinates')
                
                # Validate coordinates based on type
                if geom_type == 'point':
                    if not isinstance(coordinates, list) or len(coordinates) < 2:
                        raise ValueError("Point coordinates must be [longitude, latitude] or [lng, lat, elevation]")
                    # Ensure coordinates are in correct order: [longitude, latitude]
                    lng, lat = float(coordinates[0]), float(coordinates[1])
                    return Point(lng, lat, srid=4326)
                
                elif geom_type == 'polygon':
                    if not isinstance(coordinates, list) or len(coordinates) == 0:
                        raise ValueError("Polygon coordinates must be a list of rings")
                    
                    # Validate polygon ring structure
                    # Polygon coordinates should be: [[[lng, lat], [lng, lat], ...]]
                    if not isinstance(coordinates[0], list) or len(coordinates[0]) < 3:
                        raise ValueError("Polygon must have at least 3 points")
                    
                    # Create a copy of the coordinates to avoid modifying the original
                    coordinates_copy = json.loads(json.dumps(coordinates))
                    
                    # Ensure first and last points are the same (closed ring)
                    first_ring = coordinates_copy[0]
                    if len(first_ring) > 0:
                        # Compare coordinate values (lists), not references
                        first_point = first_ring[0]
                        last_point = first_ring[-1]
                        # Check if first and last points are different
                        if (isinstance(first_point, list) and isinstance(last_point, list) and
                            len(first_point) >= 2 and len(last_point) >= 2 and
                            (first_point[0] != last_point[0] or first_point[1] != last_point[1])):
                            # Auto-close the polygon by adding a copy of the first point at the end
                            first_ring.append(first_point[:])  # Create a copy of the first point
                            logger.info("Auto-closed polygon ring (first and last points were different)")
                    
                    # Create a new GeoJSON dict with the modified coordinates
                    polygon_geojson = {
                        'type': 'Polygon',
                        'coordinates': coordinates_copy
                    }
                    
                    # Convert to GEOSGeometry
                    geojson_string = json.dumps(polygon_geojson)
                    geometry = GEOSGeometry(geojson_string, srid=4326)
                    
                    # Validate the geometry
                    if not geometry.valid:
                        logger.warning(f"Invalid geometry detected, attempting to fix: {geometry.valid_reason}")
                        # Try to fix invalid geometry
                        try:
                            geometry = geometry.buffer(0)  # Buffer(0) can fix some invalid geometries
                        except Exception as fix_error:
                            logger.error(f"Could not fix invalid geometry: {str(fix_error)}")
                            raise ValueError(f"Invalid polygon geometry: {geometry.valid_reason}")
                    
                    return geometry
                
                else:
                    # For other geometry types (LineString, MultiPoint, etc.), use generic conversion
                    geojson_string = json.dumps(geojson_data)
                    return GEOSGeometry(geojson_string, srid=4326)
            
            else:
                raise ValueError(f"Invalid geometry data type: {type(geojson_data)}. Expected dict or str.")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error converting GeoJSON: {str(e)}")
            raise serializers.ValidationError(f"Invalid JSON format in geometry data: {str(e)}")
        except ValueError as e:
            logger.error(f"Validation error converting GeoJSON: {str(e)}")
            raise serializers.ValidationError(f"Invalid geometry data: {str(e)}")
        except Exception as e:
            logger.error(f"Error converting GeoJSON to geometry: {str(e)}")
            raise serializers.ValidationError(f"Error processing geometry data: {str(e)}")
    
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
