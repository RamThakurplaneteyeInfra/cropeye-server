import json
import logging
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response

from .chatbot_service import generate_chatbot_response

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def chatbot_api(request):
    """
    API endpoint for chatbot interactions.
    
    Accepts POST requests with JSON body:
    {
        "message": "user's message here"
    }
    
    Returns:
    {
        "reply": "AI generated response"
    }
    """
    try:
        if request.content_type != 'application/json':
            return Response(
                {"error": "Content-Type must be application/json"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
        except (json.JSONDecodeError, AttributeError):
            data = request.data
        
        message = data.get('message')
        
        if not message:
            return Response(
                {"error": "Missing required field: 'message'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(message, str):
            return Response(
                {"error": "Field 'message' must be a string"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message = message.strip()
        
        if not message:
            return Response(
                {"error": "Message cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(message) > 5000:
            return Response(
                {"error": "Message is too long. Maximum length is 5000 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reply = generate_chatbot_response(message)
        
        return Response(
            {"reply": reply},
            status=status.HTTP_200_OK
        )
    
    except ValueError as e:
        logger.warning(f"Validation error in chatbot_api: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in chatbot_api: {e}")
        return Response(
            {"error": "An error occurred while processing your request. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

