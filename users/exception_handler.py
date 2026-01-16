from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns JSON responses for all errors
    Ensures 500 errors return JSON instead of HTML
    Handles JWT authentication errors properly
    """
    # Handle JWT token errors specifically
    if isinstance(exc, (InvalidToken, TokenError, AuthenticationFailed)):
        logger.warning(f"Authentication error: {exc}")
        error_detail = 'Authentication failed. Token is invalid or expired.'
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                # Handle complex error structures
                if 'messages' in exc.detail:
                    error_detail = '; '.join(str(msg) for msg in exc.detail['messages'])
                elif 'detail' in exc.detail:
                    error_detail = str(exc.detail['detail'])
                else:
                    error_detail = str(exc.detail)
            else:
                error_detail = str(exc.detail)
        
        return Response({
            'detail': error_detail,
            'code': 'token_not_valid',
            'error_code': 'AUTHENTICATION_FAILED',
            'error_type': type(exc).__name__
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If response is None, it's an unhandled exception (500 error)
    if response is None:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        response = Response({
            'detail': 'An internal server error occurred. Please try again later.',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'error_type': type(exc).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        # Ensure all error responses have error_code
        if isinstance(response.data, dict):
            # Handle JWT errors that come through the default handler
            if 'code' in response.data and response.data.get('code') == 'token_not_valid':
                response.data['error_code'] = 'AUTHENTICATION_FAILED'
                # Ensure detail is a string, not a dict
                if isinstance(response.data.get('detail'), dict):
                    detail_dict = response.data.get('detail')
                    if 'messages' in detail_dict:
                        response.data['detail'] = '; '.join(str(msg) for msg in detail_dict['messages'])
                    else:
                        response.data['detail'] = str(detail_dict)
            elif 'error_code' not in response.data:
                response.data['error_code'] = 'API_ERROR'
    
    return response

