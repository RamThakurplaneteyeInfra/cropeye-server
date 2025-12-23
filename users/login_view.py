from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import timedelta
import secrets
import string
import re
import logging
import json

logger = logging.getLogger(__name__)

User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """
    Login with phone_number and password
    CSRF exempt for frontend API access
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def post(self, request):
        # Log request for debugging (without sensitive data) - with safe error handling
        try:
            logger.info(f"Login attempt from {request.META.get('REMOTE_ADDR', 'unknown')}")
            logger.info(f"Content-Type: {getattr(request, 'content_type', 'unknown')}")
            logger.info(f"Request method: {request.method}")
            logger.info(f"Has request.data: {hasattr(request, 'data')}")
        except Exception as log_error:
            # Don't let logging errors break the request
            logger.warning(f"Error in logging: {log_error}")
        
        # Try to get data from request.data (REST Framework parsed) FIRST
        # This is the preferred method and doesn't require accessing request.body
        body_content = None
        body_length = 0
        
        try:
            # First try REST Framework's parsed data (this is the primary method)
            if hasattr(request, 'data') and request.data:
                logger.info(f"Using request.data: {list(request.data.keys())}")
                # Support both snake_case and camelCase for phone_number
                phone_number = request.data.get('phone_number') or request.data.get('phoneNumber')
                password = request.data.get('password')
            else:
                # Only if request.data is not available, try to read body
                # But be very careful - only read once
                try:
                    # Check if we can access body without reading it
                    if hasattr(request, '_body'):
                        # Body already read, use it
                        body_content = request._body
                    elif hasattr(request, 'body'):
                        # Try to read body once
                        try:
                            body_content = request.body
                            body_length = len(body_content) if body_content else 0
                        except Exception:
                            # Body already consumed, can't read again
                            body_content = None
                    
                    if body_content:
                        body_data = json.loads(body_content.decode('utf-8'))
                        logger.info(f"Parsed JSON body: {list(body_data.keys()) if isinstance(body_data, dict) else 'not a dict'}")
                        # Support both snake_case and camelCase
                        phone_number = body_data.get('phone_number') or body_data.get('phoneNumber')
                        password = body_data.get('password')
                    else:
                        logger.warning("Request body is empty or already consumed")
                        phone_number = None
                        password = None
                except (json.JSONDecodeError, UnicodeDecodeError, AttributeError, TypeError) as e:
                    logger.warning(f"JSON parsing failed: {str(e)}")
                    # If JSON parsing fails, try form data
                    phone_number = request.POST.get('phone_number') or request.POST.get('phoneNumber') if hasattr(request, 'POST') else None
                    password = request.POST.get('password') if hasattr(request, 'POST') else None
        except Exception as e:
            logger.error(f"Error parsing request data: {str(e)}", exc_info=True)
            return Response({
                'detail': 'Invalid request format. Please send JSON with phone_number and password.',
                'error_code': 'INVALID_FORMAT',
                'hint': 'Ensure Content-Type header is set to application/json and body is valid JSON. Send: {"phone_number": "1234567890", "password": "your_password"}',
                'received_content_type': getattr(request, 'content_type', 'unknown'),
                'has_data': hasattr(request, 'data') and bool(request.data)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if data is being sent
        if not phone_number and not password:
            logger.warning("Login request with empty or missing data")
            
            # Safe body preview for response (only if we have it)
            response_body_preview = None
            if body_content:
                try:
                    response_body_preview = body_content.decode('utf-8')[:100]
                except (UnicodeDecodeError, AttributeError, TypeError):
                    pass
            
            return Response({
                'detail': 'Request body is required. Please send JSON with phone_number and password.',
                'error_code': 'EMPTY_BODY',
                'hint': 'Send: {"phone_number": "1234567890", "password": "your_password"}',
                'content_type': getattr(request, 'content_type', 'unknown'),
                'body_preview': response_body_preview
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not phone_number or not password:
            logger.warning(f"Login attempt with missing fields - phone_number: {bool(phone_number)}, password: {bool(password)}")
            return Response({
                'detail': 'Phone number and password are required',
                'error_code': 'MISSING_FIELDS',
                'received': {
                    'has_phone_number': bool(phone_number),
                    'has_password': bool(password)
                },
                'hint': 'Make sure you send: {"phone_number": "1234567890", "password": "your_password"}'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Clean phone number (remove non-digit characters)
            # Convert to string first in case it's an integer from JSON
            phone_str = str(phone_number) if phone_number is not None else ''
            cleaned_phone = re.sub(r'\D', '', phone_str)
            
            # If starts with 91 (country code), remove it to get 10 digits
            if cleaned_phone.startswith('91') and len(cleaned_phone) == 12:
                cleaned_phone = cleaned_phone[2:]
            
            # Validate phone number format (10 digits for India)
            if len(cleaned_phone) != 10:
                logger.warning(f"Invalid phone number format: {phone_number} (cleaned: {cleaned_phone}, length: {len(cleaned_phone)})")
                return Response({
                    'detail': f'Phone number must be exactly 10 digits (or 12 digits with +91). Received: {len(cleaned_phone)} digits after cleaning.',
                    'error_code': 'INVALID_PHONE_FORMAT',
                    'original': phone_number,
                    'cleaned': cleaned_phone,
                    'length': len(cleaned_phone)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Authenticate using phone_number
            user = authenticate(request, phone_number=cleaned_phone, password=password)
            
            if not user:
                logger.warning(f"Failed login attempt for phone: {cleaned_phone}")
                return Response({
                    'detail': 'Invalid phone number or password',
                    'error_code': 'INVALID_CREDENTIALS'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login attempt for deactivated account: {cleaned_phone}")
                return Response({
                    'detail': 'Account is deactivated. Please contact administrator.',
                    'error_code': 'ACCOUNT_DEACTIVATED'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Prepare industry information
            industry_data = None
            if user.industry:
                industry_data = {
                    'id': user.industry.id,
                    'name': user.industry.name,
                    'description': user.industry.description
                }
            
            logger.info(f"Successful login for user: {user.username} (ID: {user.id})")
            
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
                    } if user.role else None,
                    'industry': industry_data
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Login error for phone {cleaned_phone}: {str(e)}", exc_info=True)
            return Response({
                'detail': 'An error occurred during login. Please try again later.',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetRequestView(APIView):
    """
    Request password reset - sends reset token to user's email
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'detail': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find user by email
            user = User.objects.filter(email=email).first()
            if not user:
                # For security, don't reveal if email exists or not
                return Response({
                    'detail': 'If the email exists, a password reset link has been sent.'
                }, status=status.HTTP_200_OK)
            
            # Check if user is active
            if not user.is_active:
                return Response({
                    'detail': 'Account is deactivated'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate secure reset token
            reset_token = self._generate_reset_token()
            
            # Save token and timestamp
            user.password_reset_token = reset_token
            user.password_reset_token_created_at = timezone.now()
            user.save(update_fields=['password_reset_token', 'password_reset_token_created_at'])
            
            # Send email with reset link
            self._send_password_reset_email(user, reset_token)
            
            return Response({
                'detail': 'If the email exists, a password reset link has been sent.',
                'message': 'Check your email for password reset instructions.'
            })
            
        except Exception as e:
            return Response({
                'detail': f'Password reset request error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_reset_token(self):
        """Generate a secure random token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    def _send_password_reset_email(self, user, reset_token):
        """Send password reset email"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = 'Password Reset Request - Farm Management System'
        message = f"""
Hello {user.first_name or user.username},

You have requested to reset your password for the Farm Management System.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you did not request this password reset, please ignore this email.

Best regards,
Farm Management System Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send password reset email: {e}")


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token and new password
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not token or not new_password:
            return Response({
                'detail': 'Token and new password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 8:
            return Response({
                'detail': 'Password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find user with valid token
            user = User.objects.filter(
                password_reset_token=token,
                password_reset_token_created_at__isnull=False
            ).first()
            
            if not user:
                return Response({
                    'detail': 'Invalid or expired reset token'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if token is expired (1 hour)
            token_age = timezone.now() - user.password_reset_token_created_at
            if token_age > timedelta(hours=1):
                # Clear expired token
                user.password_reset_token = None
                user.password_reset_token_created_at = None
                user.save(update_fields=['password_reset_token', 'password_reset_token_created_at'])
                
                return Response({
                    'detail': 'Reset token has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user is active
            if not user.is_active:
                return Response({
                    'detail': 'Account is deactivated'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(new_password)
            
            # Clear reset token
            user.password_reset_token = None
            user.password_reset_token_created_at = None
            
            user.save(update_fields=['password', 'password_reset_token', 'password_reset_token_created_at'])
            
            return Response({
                'detail': 'Password has been reset successfully',
                'message': 'You can now login with your new password.'
            })
            
        except Exception as e:
            return Response({
                'detail': f'Password reset error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
