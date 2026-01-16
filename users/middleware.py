import logging
import json
from django.http import JsonResponse, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import SuspiciousOperation
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, APIException

logger = logging.getLogger(__name__)

class JSONExceptionMiddleware(MiddlewareMixin):
    """
    Middleware to catch exceptions and return JSON responses instead of HTML
    This catches errors that occur before REST Framework can handle them
    """
    
    def process_exception(self, request, exception):
        """
        Process exceptions and return JSON response for API requests
        """
        # Only handle API requests
        if request.path.startswith('/api/'):
            # Let REST Framework handle its own exceptions (including JWT errors)
            # Return None to let REST Framework exception handler process it
            if isinstance(exception, (InvalidToken, TokenError, AuthenticationFailed, NotAuthenticated, APIException)):
                return None
            
            logger.error(f"Exception in API request {request.path}: {exception}", exc_info=True)
            
            # Handle ALLOWED_HOSTS errors specifically (400 errors)
            if isinstance(exception, SuspiciousOperation):
                return JsonResponse({
                    'detail': 'Invalid host header. Please check ALLOWED_HOSTS configuration.',
                    'error_code': 'INVALID_HOST',
                    'error_type': type(exception).__name__,
                    'path': request.path,
                    'host': request.get_host() if hasattr(request, 'get_host') else 'unknown',
                    'hint': f'Request came from host: {request.get_host() if hasattr(request, "get_host") else "unknown"}'
                }, status=400)
            
            # Return JSON error response for other exceptions
            return JsonResponse({
                'detail': 'An internal server error occurred. Please try again later.',
                'error_code': 'INTERNAL_SERVER_ERROR',
                'error_type': type(exception).__name__,
                'path': request.path
            }, status=500)
        
        # For non-API requests, let Django handle it normally
        return None
    
    def process_response(self, request, response):
        """
        Ensure API responses are JSON, even if they're HTML error pages
        """
        # Only handle API requests
        if request.path.startswith('/api/'):
            # If response is HTML and it's an error (400, 500, etc.), convert to JSON
            if hasattr(response, 'content') and response.status_code >= 400:
                content_type = response.get('Content-Type', '')
                if 'text/html' in content_type or 'text/plain' in content_type:
                    # Try to extract error message from HTML
                    try:
                        content = response.content.decode('utf-8')
                        # Check if it's an HTML error page
                        if '<html' in content.lower() or '<h1' in content.lower():
                            logger.warning(f"HTML error response detected for {request.path}, converting to JSON")
                            return JsonResponse({
                                'detail': f'Server error ({response.status_code}). Please check your request format.',
                                'error_code': 'HTTP_ERROR',
                                'status_code': response.status_code,
                                'path': request.path,
                                'hint': 'Ensure Content-Type is application/json and request body is valid JSON'
                            }, status=response.status_code)
                    except (UnicodeDecodeError, AttributeError):
                        pass
        
        return response

