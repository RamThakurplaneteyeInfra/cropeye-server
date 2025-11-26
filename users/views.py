from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
import string
from .models import Role, Industry
from .serializers import (
    UserSerializer, 
    UserCreateSerializer,
    FieldOfficerWithFarmersSerializer,
    FieldOfficerSerializer,
    OwnerHierarchySerializer,
    ManagerHierarchySerializer
)
from .permissions import IsManager, IsOwner
from .multi_tenant_utils import filter_by_industry, get_accessible_users, get_user_industry

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Enhanced create method to handle owner creation by managers.
        This creates a special relationship where:
        - Manager creates the owner
        - Owner can monitor the manager who created them
        - Owner gets elevated permissions to view all managers
        """
        # Log the incoming request data for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"=== USER CREATION REQUEST ===")
        logger.info(f"Creator: {request.user.username} (Role: {request.user.role.name if request.user.role else None})")
        logger.info(f"Request data type: {type(request.data)}")
        logger.info(f"role_id from request.data: {request.data.get('role_id')} (type: {type(request.data.get('role_id'))})")
        logger.info(f"All keys in request.data: {list(request.data.keys())}")
        if hasattr(request.data, 'get'):
            logger.info(f"Full request.data: {dict(request.data)}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Log validated_data after validation
        logger.info(f"After validation - role_id in validated_data: {serializer.validated_data.get('role_id')} (type: {type(serializer.validated_data.get('role_id'))})")
        logger.info(f"All keys in validated_data: {list(serializer.validated_data.keys())}")
        
        # Get user's industry for assignment
        # For superusers, check their industry directly (get_user_industry returns None for superusers)
        if request.user.is_superuser:
            user_industry = request.user.industry  # Check superuser's industry directly
        else:
            user_industry = get_user_industry(request.user)
        
        # Check if creating an owner
        role_id = serializer.validated_data.get('role_id')
        if role_id == 4:  # Owner role
            # Allow Superuser, Owner, or Manager to create Owners
            if not (request.user.is_superuser or request.user.has_role('owner') or request.user.has_role('manager')):
                return Response({
                    'error': 'Only Global Admin, Industry Admin, or Manager can create Owners'
                }, status=403)
            
            # Special logic for owner creation
            owner_data = serializer.validated_data.copy()
            owner_data['created_by'] = request.user  # Manager/Admin who creates owner
            
            # Handle industry assignment for owner
            # Remove any industry_id/industry from frontend to prevent override
            owner_data.pop('industry', None)
            owner_data.pop('industry_id', None)
            
            # Determine which industry to assign
            owner_industry = None
            
            if request.user.is_superuser:
                # Superuser can specify industry_id from frontend, or use their own industry
                industry_id_from_request = request.data.get('industry_id')
                if industry_id_from_request:
                    try:
                        owner_industry = Industry.objects.get(id=industry_id_from_request)
                    except Industry.DoesNotExist:
                        return Response({
                            'error': f'Industry with ID {industry_id_from_request} not found.'
                        }, status=400)
                elif user_industry:  # Now this will work if superuser has industry
                    # Use superuser's industry if they have one
                    owner_industry = user_industry
                else:
                    # Superuser with no industry - require industry_id
                    return Response({
                        'error': 'When creating an owner as superuser, you must specify industry_id in the request, or be assigned to an industry first.'
                    }, status=400)
            else:
                # Owner or manager creating owner - use their industry
                if not user_industry:
                    return Response({
                        'error': f'User "{request.user.username}" must be assigned to an industry before creating owners. Please contact administrator to assign an industry.',
                        'user_id': request.user.id,
                        'username': request.user.username,
                        'role': request.user.role.name if request.user.role else 'unknown'
                    }, status=400)
                owner_industry = user_industry
            
            # Assign industry to owner
            owner_data['industry'] = owner_industry
            
            # Create the owner
            owner = User.objects.create_user(**owner_data)
            
            # Return special response for owner creation
            return Response({
                'success': True,
                'message': 'Owner created successfully. Owner can now monitor all managers including the one who created them.',
                'id': owner.id,
                'username': owner.username,
                'email': owner.email,
                'role': {
                    'id': owner.role.id,
                    'name': owner.role.name,
                    'display_name': owner.role.display_name
                },
                'industry': {
                    'id': owner.industry.id,
                    'name': owner.industry.name
                } if owner.industry else None,
                'created_by': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'role': request.user.role.name if request.user.role else 'unknown'
                },
                'note': 'Owner has elevated permissions to monitor all managers'
            }, status=201)
        else:
            # Normal user creation - assign industry
            # Handle superuser case (can specify industry) vs manager case (must use their industry)
            if request.user.is_superuser:
                # Superuser can specify industry_id from frontend, or use their own industry
                industry_id_from_request = request.data.get('industry_id')
                if industry_id_from_request:
                    try:
                        specified_industry = Industry.objects.get(id=industry_id_from_request)
                        serializer.validated_data['industry'] = specified_industry
                    except Industry.DoesNotExist:
                        return Response({
                            'error': f'Industry with ID {industry_id_from_request} not found.'
                        }, status=400)
                elif user_industry:  # Now this will work if superuser has industry
                    # Use superuser's industry if they have one
                    serializer.validated_data['industry'] = user_industry
                else:
                    # Superuser with no industry - require industry_id
                    return Response({
                        'error': 'Superuser must specify industry_id when creating users, or be assigned to an industry first.'
                    }, status=400)
            else:
                # Manager case - remove any industry_id/industry from frontend to prevent override
                # Always use the manager's industry
                serializer.validated_data.pop('industry', None)
                serializer.validated_data.pop('industry_id', None)
                
                # Ensure manager has an industry
                if not user_industry:
                    return Response({
                        'error': f'Manager "{request.user.username}" must be assigned to an industry before creating users. Please contact administrator to assign an industry to this manager account.',
                        'user_id': request.user.id,
                        'username': request.user.username,
                        'role': request.user.role.name if request.user.role else 'unknown'
                    }, status=400)
                
                # Always assign manager's industry (cannot be overridden by frontend)
                serializer.validated_data['industry'] = user_industry
            
            # Override perform_create to ensure industry is passed correctly
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)
    
    def perform_create(self, serializer):
        """
        Override perform_create to ensure industry is explicitly saved.
        The industry is set in validated_data by the view, but we ensure it's saved.
        """
        # Get industry from validated_data (set by view) or from creator
        industry = serializer.validated_data.get('industry')
        creator = serializer.context['request'].user
        
        # If industry is not in validated_data, get it from creator
        if not industry and creator and creator.industry:
            industry = creator.industry
            # Also update validated_data so serializer.create() can use it
            serializer.validated_data['industry'] = industry
        
        # Ensure industry is set - this should never be None at this point
        if not industry:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"CRITICAL: Industry is None when creating user. "
                f"Creator: {creator.username if creator else 'None'}, "
                f"Creator Industry: {creator.industry.name if creator and creator.industry else 'None'}"
            )
            raise ValueError("Industry must be set before creating user. This should not happen.")
        
        # Save with explicit industry parameter to ensure it's saved
        instance = serializer.save(industry=industry)
        
        # Final safety check: verify both role and industry were saved
        instance.refresh_from_db()
        
        # Verify role was saved
        if not instance.role:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"CRITICAL: Role was missing after save for user {instance.username}. "
                f"This should not happen - role should be set in serializer.create()"
            )
            # Try to get role from validated_data if available
            role_id = serializer.validated_data.get('role_id')
            if role_id:
                try:
                    from .models import Role
                    role = Role.objects.get(id=role_id)
                    instance.role = role
                    instance.save(update_fields=['role'])
                    logger.warning(f"Fixed role for user {instance.username} - set to {role.name}")
                except Role.DoesNotExist:
                    logger.error(f"Could not fix role - Role with ID {role_id} does not exist")
        
        # Verify industry was saved
        if not instance.industry:
            # This should never happen, but if it does, set it from creator
            if creator and creator.industry:
                instance.industry = creator.industry
                instance.save(update_fields=['industry'])
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"CRITICAL: Industry was missing after save for user {instance.username}. "
                    f"Set it from creator {creator.username}'s industry: {creator.industry.name}"
                )
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"CRITICAL: Industry was missing after save for user {instance.username} "
                    f"and creator {creator.username if creator else 'None'} has no industry!"
                )
        
        # Final verification log
        if instance.role and instance.industry:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"✅ User {instance.username} (ID: {instance.id}) saved correctly: "
                f"Role={instance.role.name} (ID: {instance.role.id}), "
                f"Industry={instance.industry.name} (ID: {instance.industry.id})"
            )
        
        return instance
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsManager()]
        elif self.action == 'my_field_officers':
            return [permissions.IsAuthenticated()] # Logic is handled inside the view
        elif self.action == 'owner_hierarchy':
            return [IsOwner()]
        elif self.action in ['send_otp', 'verify_otp']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        # Global Admin can see all users
        if user.is_superuser:
            return User.objects.all()
        
        # Use multi-tenant utility to get accessible users
        return get_accessible_users(user)
    
    @action(detail=False, methods=['get'], url_path='my-field-officers')
    def my_field_officers(self, request):
        """
        Get field officers.
        - If logged in as a Manager, returns field officers created by that manager.
        - If logged in as an Owner, returns all managers and their field officers.
        """
        user = request.user

        if user.has_role('manager'):
            # Manager's view: their own field officers (filtered by industry)
            user_industry = get_user_industry(user)
            field_officers = user.created_users.filter(
                role__name='fieldofficer',
                industry=user_industry
            )
            
            total_farmers = 0
            total_plots = 0
            for fo in field_officers:
                farmers_under_fo = fo.created_users.filter(
                    role__name='farmer',
                    industry=user_industry
                )
                total_farmers += farmers_under_fo.count()
                for farmer in farmers_under_fo:
                    total_plots += farmer.plots.filter(industry=user_industry).count()

            serializer = FieldOfficerWithFarmersSerializer(field_officers, many=True, context={'request': request})
            
            return Response({
                "manager": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "summary": {
                    "total_field_officers": field_officers.count(),
                    "total_farmers": total_farmers,
                    "total_plots": total_plots,
                },
                "field_officers": serializer.data
            })

        elif user.has_role('owner'):
            # Owner's view: all managers and their hierarchies in their industry
            user_industry = get_user_industry(user)
            managers = User.objects.filter(
                role__name='manager',
                industry=user_industry
            )
            serializer = ManagerHierarchySerializer(managers, many=True)
            return Response({
                "owner_view": True,
                "industry": {
                    "id": user_industry.id,
                    "name": user_industry.name
                } if user_industry else None,
                "managers": serializer.data
            })

        else:
            return Response({"error": "You do not have permission to access this endpoint."}, status=status.HTTP_403_FORBIDDEN)
    
    
    @action(detail=False, methods=['get'], url_path='owner-hierarchy')
    def owner_hierarchy(self, request):
        """
        Get complete hierarchy for Owner:
        - All managers (including the one who created this owner)
        - Field officers under each manager
        - Farmers under each field officer
        - Total counts and statistics
        """
        # Get the current owner user
        owner = request.user
        
        # Serialize the owner with complete hierarchy
        serializer = OwnerHierarchySerializer(owner)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-creator')
    def my_creator(self, request):
        """
        Special endpoint for owners to see who created them (the manager).
        This handles the special case where managers create owners.
        """
        user = request.user
        
        if user.has_role('owner') and user.created_by:
            # Owner can see the manager who created them
            creator = user.created_by
            return Response({
                'success': True,
                'creator': {
                    'id': creator.id,
                    'username': creator.username,
                    'email': creator.email,
                    'role': creator.role.name if creator.role else 'unknown',
                    'first_name': creator.first_name,
                    'last_name': creator.last_name,
                    'note': 'This manager created you as an owner. You can now monitor them and all other managers.'
                }
            })
        elif user.has_role('owner'):
            return Response({
                'success': True,
                'creator': None,
                'note': 'You are a system owner with no specific creator. You can monitor all managers.'
            })
        else:
            return Response({
                'error': 'Only owners can access this endpoint'
            }, status=403)
    
    @action(detail=False, methods=['get'], url_path='contact-details')
    def contact_details(self, request):
        """
        Get contact details based on user role and hierarchy position.
        
        - Manager: Shows owner, field officers, and farmers contact details
        - Field Officer: Shows manager, owner, and farmers contact details  
        - Farmer: Shows field officer, manager, and owner contact details
        """
        user = request.user
        
        if user.has_role('manager'):
            return self._get_manager_contacts(user)
        elif user.has_role('fieldofficer'):
            return self._get_field_officer_contacts(user)
        elif user.has_role('farmer'):
            return self._get_farmer_contacts(user)
        elif user.has_role('owner'):
            return self._get_owner_contacts(user)
        else:
            return Response({
                'error': 'Invalid user role for contact details'
            }, status=403)
    
    def _get_manager_contacts(self, manager):
        """Get contact details for manager"""
        # Get owner (if manager was created by owner, or any owner in system)
        owners = User.objects.filter(role__name='owner')
        owner_contact = None
        if owners.exists():
            owner = owners.first()
            owner_contact = {
                'id': owner.id,
                'name': f"{owner.first_name} {owner.last_name}".strip() or owner.username,
                'role': 'Owner',
                'email': owner.email,
                'phone': owner.phone_number,
                'address': f"{owner.address}, {owner.village}, {owner.district}, {owner.state}".replace(', , ', ', ').strip(', ')
            }
        
        # Get field officers created by this manager
        field_officers = manager.created_users.filter(role__name='fieldofficer')
        field_officer_contacts = []
        for fo in field_officers:
            field_officer_contacts.append({
                'id': fo.id,
                'name': f"{fo.first_name} {fo.last_name}".strip() or fo.username,
                'role': 'Field Officer',
                'email': fo.email,
                'phone': fo.phone_number,
                'address': f"{fo.address}, {fo.village}, {fo.district}, {fo.state}".replace(', , ', ', ').strip(', '),
                'farmers_count': fo.created_users.filter(role__name='farmer').count()
            })
        
        # Get farmers created by field officers under this manager
        farmers = User.objects.filter(
            role__name='farmer',
            created_by__in=field_officers
        )
        farmer_contacts = []
        for farmer in farmers:
            farmer_contacts.append({
                'id': farmer.id,
                'name': f"{farmer.first_name} {farmer.last_name}".strip() or farmer.username,
                'role': 'Farmer',
                'email': farmer.email,
                'phone': farmer.phone_number,
                'address': f"{farmer.address}, {farmer.village}, {farmer.district}, {farmer.state}".replace(', , ', ', ').strip(', '),
                'field_officer': farmer.created_by.username if farmer.created_by else None
            })
        
        return Response({
            'user_role': 'Manager',
            'user_name': f"{manager.first_name} {manager.last_name}".strip() or manager.username,
            'contacts': {
                'owner': owner_contact,
                'field_officers': field_officer_contacts,
                'farmers': farmer_contacts
            },
            'summary': {
                'total_field_officers': len(field_officer_contacts),
                'total_farmers': len(farmer_contacts)
            }
        })
    
    def _get_field_officer_contacts(self, field_officer):
        """Get contact details for field officer"""
        # Get manager who created this field officer
        manager_contact = None
        if field_officer.created_by and field_officer.created_by.has_role('manager'):
            manager = field_officer.created_by
            manager_contact = {
                'id': manager.id,
                'name': f"{manager.first_name} {manager.last_name}".strip() or manager.username,
                'role': 'Manager',
                'email': manager.email,
                'phone': manager.phone_number,
                'address': f"{manager.address}, {manager.village}, {manager.district}, {manager.state}".replace(', , ', ', ').strip(', ')
            }
        
        # Get owner (any owner in system)
        owners = User.objects.filter(role__name='owner')
        owner_contact = None
        if owners.exists():
            owner = owners.first()
            owner_contact = {
                'id': owner.id,
                'name': f"{owner.first_name} {owner.last_name}".strip() or owner.username,
                'role': 'Owner',
                'email': owner.email,
                'phone': owner.phone_number,
                'address': f"{owner.address}, {owner.village}, {owner.district}, {owner.state}".replace(', , ', ', ').strip(', ')
            }
        
        # Get farmers created by this field officer
        farmers = field_officer.created_users.filter(role__name='farmer')
        farmer_contacts = []
        for farmer in farmers:
            farmer_contacts.append({
                'id': farmer.id,
                'name': f"{farmer.first_name} {farmer.last_name}".strip() or farmer.username,
                'role': 'Farmer',
                'email': farmer.email,
                'phone': farmer.phone_number,
                'address': f"{farmer.address}, {farmer.village}, {farmer.district}, {farmer.state}".replace(', , ', ', ').strip(', ')
            })
        
        return Response({
            'user_role': 'Field Officer',
            'user_name': f"{field_officer.first_name} {field_officer.last_name}".strip() or field_officer.username,
            'contacts': {
                'manager': manager_contact,
                'owner': owner_contact,
                'farmers': farmer_contacts
            },
            'summary': {
                'total_farmers': len(farmer_contacts)
            }
        })
    
    def _get_farmer_contacts(self, farmer):
        """Get contact details for farmer"""
        # Get field officer who created this farmer
        field_officer_contact = None
        if farmer.created_by and farmer.created_by.has_role('fieldofficer'):
            fo = farmer.created_by
            field_officer_contact = {
                'id': fo.id,
                'name': f"{fo.first_name} {fo.last_name}".strip() or fo.username,
                'role': 'Field Officer',
                'email': fo.email,
                'phone': fo.phone_number,
                'address': f"{fo.address}, {fo.village}, {fo.district}, {fo.state}".replace(', , ', ', ').strip(', ')
            }
        
        # Get manager (through field officer)
        manager_contact = None
        if farmer.created_by and farmer.created_by.created_by and farmer.created_by.created_by.has_role('manager'):
            manager = farmer.created_by.created_by
            manager_contact = {
                'id': manager.id,
                'name': f"{manager.first_name} {manager.last_name}".strip() or manager.username,
                'role': 'Manager',
                'email': manager.email,
                'phone': manager.phone_number,
                'address': f"{manager.address}, {manager.village}, {manager.district}, {manager.state}".replace(', , ', ', ').strip(', ')
            }
        
        # Get owner (any owner in system)
        owners = User.objects.filter(role__name='owner')
        owner_contact = None
        if owners.exists():
            owner = owners.first()
            owner_contact = {
                'id': owner.id,
                'name': f"{owner.first_name} {owner.last_name}".strip() or owner.username,
                'role': 'Owner',
                'email': owner.email,
                'phone': owner.phone_number,
                'address': f"{owner.address}, {owner.village}, {owner.district}, {owner.state}".replace(', , ', ', ').strip(', ')
            }
        
        return Response({
            'user_role': 'Farmer',
            'user_name': f"{farmer.first_name} {farmer.last_name}".strip() or farmer.username,
            'contacts': {
                'field_officer': field_officer_contact,
                'manager': manager_contact,
                'owner': owner_contact
            }
        })
    
    def _get_owner_contacts(self, owner):
        """Get contact details for owner"""
        # Get all managers
        managers = User.objects.filter(role__name='manager')
        manager_contacts = []
        for manager in managers:
            manager_contacts.append({
                'id': manager.id,
                'name': f"{manager.first_name} {manager.last_name}".strip() or manager.username,
                'role': 'Manager',
                'email': manager.email,
                'phone': manager.phone_number,
                'address': f"{manager.address}, {manager.village}, {manager.district}, {manager.state}".replace(', , ', ', ').strip(', '),
                'field_officers_count': manager.created_users.filter(role__name='fieldofficer').count()
            })
        
        # Get all field officers
        field_officers = User.objects.filter(role__name='fieldofficer')
        field_officer_contacts = []
        for fo in field_officers:
            field_officer_contacts.append({
                'id': fo.id,
                'name': f"{fo.first_name} {fo.last_name}".strip() or fo.username,
                'role': 'Field Officer',
                'email': fo.email,
                'phone': fo.phone_number,
                'address': f"{fo.address}, {fo.village}, {fo.district}, {fo.state}".replace(', , ', ', ').strip(', '),
                'manager': fo.created_by.username if fo.created_by else None,
                'farmers_count': fo.created_users.filter(role__name='farmer').count()
            })
        
        # Get all farmers
        farmers = User.objects.filter(role__name='farmer')
        farmer_contacts = []
        for farmer in farmers:
            farmer_contacts.append({
                'id': farmer.id,
                'name': f"{farmer.first_name} {farmer.last_name}".strip() or farmer.username,
                'role': 'Farmer',
                'email': farmer.email,
                'phone': farmer.phone_number,
                'address': f"{farmer.address}, {farmer.village}, {farmer.district}, {farmer.state}".replace(', , ', ', ').strip(', '),
                'field_officer': farmer.created_by.username if farmer.created_by else None
            })
        
        return Response({
            'user_role': 'Owner',
            'user_name': f"{owner.first_name} {owner.last_name}".strip() or owner.username,
            'contacts': {
                'managers': manager_contacts,
                'field_officers': field_officer_contacts,
                'farmers': farmer_contacts
            },
            'summary': {
                'total_managers': len(manager_contacts),
                'total_field_officers': len(field_officer_contacts),
                'total_farmers': len(farmer_contacts)
            }
        })
    
    @action(detail=False, methods=['get'], url_path='hierarchy-summary')
    def hierarchy_summary(self, request):
        """
        Get a summary of the hierarchy for any authenticated user
        """
        user = request.user
        
        if user.has_role('owner'):
            # Owner sees summary of all levels
            summary = {
                'role': 'owner',
                'total_managers': User.objects.filter(role__name='manager').count(),
                'total_field_officers': User.objects.filter(role__name='fieldofficer').count(),
                'total_farmers': User.objects.filter(role__name='farmer').count(),
                'message': 'Use /owner-hierarchy/ for complete details'
            }
        elif user.has_role('manager'):
            # Manager sees their field officers and farmers
            field_officers = user.created_users.filter(role__name='fieldofficer')
            total_farmers = 0
            for fo in field_officers:
                total_farmers += fo.created_users.filter(role__name='farmer').count()
            
            summary = {
                'role': 'manager',
                'field_officers_count': field_officers.count(),
                'total_farmers_count': total_farmers,
                'message': 'Use /my-field-officers/ for field officer details'
            }
        elif user.has_role('fieldofficer'):
            # Field officer sees their farmers
            farmers_count = user.created_users.filter(role__name='farmer').count()
            summary = {
                'role': 'fieldofficer',
                'farmers_count': farmers_count,
                'message': 'Use /my-farmers/ for farmer details'
            }
        elif user.has_role('farmer'):
            summary = {
                'role': 'farmer',
                'message': 'You are at the bottom level of the hierarchy'
            }
        else:
            summary = {
                'role': 'unknown',
                'message': 'No role assigned'
            }
        
        return Response(summary)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny], url_path='login')
    def login(self, request):
        """
        Login with phone_number and password
        """
        from django.contrib.auth import authenticate
        import re
        
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        
        if not phone_number or not password:
            return Response({
                'detail': 'Phone number and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Clean phone number (remove non-digit characters)
        cleaned_phone = re.sub(r'\D', '', phone_number)
        
        # If starts with 91 (country code), remove it to get 10 digits
        if cleaned_phone.startswith('91') and len(cleaned_phone) == 12:
            cleaned_phone = cleaned_phone[2:]
        
        # Validate phone number format (10 digits for India)
        if len(cleaned_phone) != 10:
            return Response({
                'detail': 'Phone number must be exactly 10 digits (or 12 digits with +91)'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Authenticate using phone_number
            user = authenticate(request, phone_number=cleaned_phone, password=password)
            
            if not user:
                return Response({
                    'detail': 'Invalid phone number or password'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if user is active
            if not user.is_active:
                return Response({
                    'detail': 'Account is deactivated'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'phone_number': user.phone_number,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': {
                        'id': user.role.id,
                        'name': user.role.name,
                        'display_name': user.role.display_name
                    } if user.role else None
                }
            })
            
        except Exception as e:
            return Response({
                'detail': f'Login error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request, pk=None):
        user_obj = self.get_object()
        from .serializers import ChangePasswordSerializer
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not user_obj.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': 'Wrong password.'}, status=status.HTTP_400_BAD_REQUEST)

        user_obj.set_password(serializer.validated_data['new_password'])
        user_obj.save()
        return Response({'status': 'password changed'})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user
        
        # Check if user is a farmer (role ID 1)
        if user.role and user.role.id == 1:  # farmer role
            from .serializers import FarmerDetailSerializer
            serializer = FarmerDetailSerializer(user)
        else:
            # Use default serializer for non-farmers
            serializer = self.get_serializer(user)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='verify-industry-separation', permission_classes=[permissions.IsAuthenticated])
    def verify_industry_separation(self, request):
        """
        API endpoint to verify industry data separation implementation.
        Returns status of industry filtering across all ViewSets.
        """
        from django.apps import apps
        import os
        from pathlib import Path
        
        results = {
            'status': 'checking',
            'viewsets': {},
            'models': {},
            'database': {},
            'summary': {
                'implemented': 0,
                'missing': 0,
                'total': 0
            }
        }
        
        # Check ViewSets
        viewsets_to_check = {
            'UserViewSet': ('users/views.py', 'UserViewSet'),
            'FarmViewSet': ('farms/views.py', 'FarmViewSet'),
            'PlotViewSet': ('farms/views.py', 'PlotViewSet'),
            'TaskViewSet': ('tasks/views.py', 'TaskViewSet'),
            'BookingViewSet': ('bookings/views.py', 'BookingViewSet'),
            'InventoryItemViewSet': ('inventory/views.py', 'InventoryItemViewSet'),
            'EquipmentViewSet': ('equipment/views.py', 'EquipmentViewSet'),
            'VendorViewSet': ('vendors/views.py', 'VendorViewSet'),
        }
        
        base_dir = Path(__file__).resolve().parent.parent.parent
        
        for viewset_name, (file_path, class_name) in viewsets_to_check.items():
            full_path = base_dir / file_path
            
            if not full_path.exists():
                results['viewsets'][viewset_name] = {
                    'status': 'file_not_found',
                    'has_filter': False,
                    'file': file_path
                }
                continue
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            has_import = 'filter_by_industry' in content or 'get_user_industry' in content
            has_filter = False
            line_number = None
            
            in_class = False
            in_get_queryset = False
            
            for i, line in enumerate(lines, 1):
                if f'class {class_name}' in line:
                    in_class = True
                elif in_class and 'class ' in line and class_name not in line:
                    in_class = False
                    in_get_queryset = False
                
                if in_class and 'def get_queryset' in line:
                    in_get_queryset = True
                elif in_get_queryset and ('def ' in line or 'class ' in line):
                    in_get_queryset = False
                
                if in_get_queryset and 'filter_by_industry' in line:
                    has_filter = True
                    line_number = i
                    break
            
            results['viewsets'][viewset_name] = {
                'status': 'implemented' if has_filter else 'missing',
                'has_filter': has_filter,
                'has_import': has_import,
                'line_number': line_number,
                'file': file_path
            }
            
            if has_filter:
                results['summary']['implemented'] += 1
            else:
                results['summary']['missing'] += 1
            results['summary']['total'] += 1
        
        # Check models with industry field
        models_with_industry = []
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                if hasattr(model, 'industry'):
                    models_with_industry.append(f"{app_config.name}.{model.__name__}")
        
        results['models'] = {
            'with_industry_field': models_with_industry,
            'count': len(models_with_industry)
        }
        
        # Check database data
        try:
            from users.models import Industry
            
            industries = Industry.objects.all()
            industry_data = {}
            
            for industry in industries:
                industry_data[industry.name] = {
                    'id': industry.id,
                    'users': User.objects.filter(industry=industry).count(),
                }
                
                try:
                    from farms.models import Farm, Plot
                    industry_data[industry.name]['farms'] = Farm.objects.filter(industry=industry).count()
                    industry_data[industry.name]['plots'] = Plot.objects.filter(industry=industry).count()
                except:
                    pass
                
                try:
                    from tasks.models import Task
                    industry_data[industry.name]['tasks'] = Task.objects.filter(industry=industry).count()
                except:
                    pass
                
                try:
                    from bookings.models import Booking
                    industry_data[industry.name]['bookings'] = Booking.objects.filter(industry=industry).count()
                except:
                    pass
                
                try:
                    from inventory.models import InventoryItem
                    industry_data[industry.name]['inventory'] = InventoryItem.objects.filter(industry=industry).count()
                except:
                    pass
            
            results['database'] = {
                'industries': industry_data,
                'total_industries': industries.count()
            }
        except Exception as e:
            results['database'] = {'error': str(e)}
        
        results['status'] = 'complete'
        
        return Response(results)
    
    @action(detail=False, methods=['get'], url_path='industries')
    def list_industries(self, request):
        """
        Get list of all industries.
        - Superuser: sees all industries
        - Industry Admin (Owner): sees only their industry
        - Others: 403 Forbidden
        """
        from .models import Industry
        from .serializers import IndustrySerializer
        
        user = request.user
        
        if user.is_superuser:
            industries = Industry.objects.all()
        elif user.has_role('owner') and user.industry:
            industries = Industry.objects.filter(id=user.industry.id)
        else:
            return Response({
                'error': 'Only Superuser or Industry Admin can access this endpoint'
            }, status=403)
        
        return Response({
            'industries': IndustrySerializer(industries, many=True).data,
            'count': industries.count()
        })
    
    @action(detail=False, methods=['get'], url_path='industry-data')
    def industry_data(self, request):
        """
        Get ALL data for a specific industry when user clicks on Industry A/B/C.
        
        Query Parameters:
        - industry_id (required): The ID of the industry to fetch data for
        
        Returns complete hierarchy:
        - Owners (in this industry)
        - Managers (in this industry)
        - Field Officers (in this industry)
        - Farmers (in this industry)
        - Plots (in this industry)
        - Farms/Crops (in this industry)
        - Tasks (in this industry)
        - Bookings (in this industry)
        - Inventory Items (in this industry)
        
        Access:
        - Superuser: Can access any industry
        - Industry Admin (Owner): Can only access their own industry
        - Others: Cannot access (403)
        """
        from .models import Industry
        
        # Get industry_id from query parameters
        industry_id = request.query_params.get('industry_id')
        if not industry_id:
            return Response({
                'error': 'industry_id query parameter is required'
            }, status=400)
        
        try:
            industry_id = int(industry_id)
        except (ValueError, TypeError):
            return Response({
                'error': 'industry_id must be a valid integer'
            }, status=400)
        
        try:
            industry = Industry.objects.get(id=industry_id)
        except Industry.DoesNotExist:
            return Response({
                'error': f'Industry with ID {industry_id} does not exist'
            }, status=404)
        
        # Permission check
        user = request.user
        if not user.is_superuser:
            # Industry Admin can only see their own industry
            if user.has_role('owner'):
                if not user.industry or user.industry.id != industry.id:
                    return Response({
                        'error': 'You can only access data for your own industry'
                    }, status=403)
            else:
                return Response({
                    'error': 'Only Superuser or Industry Admin can access this endpoint'
                }, status=403)
        
        # Get all users in this industry by role
        owners = User.objects.filter(industry=industry, role__name='owner').select_related('role', 'industry')
        managers = User.objects.filter(industry=industry, role__name='manager').select_related('role', 'industry')
        field_officers = User.objects.filter(industry=industry, role__name='fieldofficer').select_related('role', 'industry')
        farmers = User.objects.filter(industry=industry, role__name='farmer').select_related('role', 'industry')
        
        # Get all data in this industry
        try:
            from farms.models import Plot, Farm
            plots = Plot.objects.filter(industry=industry).select_related('farmer', 'created_by', 'industry')
            farms = Farm.objects.filter(industry=industry).select_related(
                'farm_owner', 'plot', 'crop_type', 'soil_type', 'industry'
            )
        except ImportError:
            plots = []
            farms = []
        
        try:
            from tasks.models import Task
            tasks = Task.objects.filter(industry=industry).select_related('assigned_to', 'created_by', 'industry')
        except ImportError:
            tasks = []
        
        try:
            from bookings.models import Booking
            bookings = Booking.objects.filter(industry=industry).select_related('created_by', 'approved_by', 'industry')
        except ImportError:
            bookings = []
        
        try:
            from inventory.models import InventoryItem
            inventory_items = InventoryItem.objects.filter(industry=industry).select_related('industry')
        except ImportError:
            inventory_items = []
        
        # Serialize data
        from .serializers import IndustrySerializer
        
        try:
            from farms.serializers import PlotSerializer, FarmSerializer
            plots_data = PlotSerializer(plots, many=True).data
            farms_data = FarmSerializer(farms, many=True).data
        except ImportError:
            plots_data = []
            farms_data = []
        
        try:
            from tasks.serializers import TaskSerializer
            tasks_data = TaskSerializer(tasks, many=True).data
        except ImportError:
            tasks_data = []
        
        try:
            from bookings.serializers import BookingSerializer
            bookings_data = BookingSerializer(bookings, many=True).data
        except ImportError:
            bookings_data = []
        
        try:
            from inventory.serializers import InventoryItemSerializer
            inventory_data = InventoryItemSerializer(inventory_items, many=True).data
        except ImportError:
            inventory_data = []
        
        return Response({
            'industry': IndustrySerializer(industry).data,
            'hierarchy': {
                'owners': UserSerializer(owners, many=True).data,
                'managers': UserSerializer(managers, many=True).data,
                'field_officers': UserSerializer(field_officers, many=True).data,
                'farmers': UserSerializer(farmers, many=True).data,
            },
            'counts': {
                'owners_count': owners.count(),
                'managers_count': managers.count(),
                'field_officers_count': field_officers.count(),
                'farmers_count': farmers.count(),
                'plots_count': len(plots_data) if isinstance(plots, list) else plots.count(),
                'farms_count': len(farms_data) if isinstance(farms, list) else farms.count(),
                'tasks_count': len(tasks_data) if isinstance(tasks, list) else tasks.count(),
                'bookings_count': len(bookings_data) if isinstance(bookings, list) else bookings.count(),
                'inventory_items_count': len(inventory_data) if isinstance(inventory_items, list) else inventory_items.count(),
            },
            'data': {
                'plots': plots_data,
                'farms': farms_data,
                'tasks': tasks_data,
                'bookings': bookings_data,
                'inventory_items': inventory_data,
            }
        })
