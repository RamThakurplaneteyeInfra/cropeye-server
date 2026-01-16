"""
Custom middleware to filter health check requests from access logs.
"""
import logging
import re

logger = logging.getLogger(__name__)

class HealthCheckLogFilter:
    """
    Middleware to suppress logging for health check requests.
    This prevents /api/health/ requests from cluttering the logs.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Pattern to match health check endpoints
        self.health_check_patterns = [
            r'/api/health/',
            r'/health/',
        ]
    
    def __call__(self, request):
        # Check if this is a health check request
        is_health_check = any(
            re.search(pattern, request.path, re.IGNORECASE)
            for pattern in self.health_check_patterns
        )
        
        # Store flag in request for use in logging
        request._suppress_access_log = is_health_check
        
        # Process the request
        response = self.get_response(request)
        
        return response
    
    def process_exception(self, request, exception):
        # Don't suppress error logs, even for health checks
        return None

