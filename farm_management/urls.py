from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

def health_check(request):
    return JsonResponse({"status": "healthy", "service": "farm-management-api"})

def root_view(request):
    """Root URL handler - redirects to API docs or returns API info"""
    return JsonResponse({
        "message": "Farm Management API",
        "version": "1.0",
        "endpoints": {
            "health": "/api/health/",
            "api_docs": "/swagger/",
            "admin": "/admin/",
            "users": "/api/users/",
            "messaging": "/api/conversations/",
            "farms": "/api/farms/",
        }
    })

schema_view = get_schema_view(
    openapi.Info(
        title="Farm Management API",
        default_version='v1',
        description="API for Farm Management System",
        terms_of_service="https://www.planeteyefarm.ai/terms/",
        contact=openapi.Contact(email="contact@planeteyefarm.ai"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    
    # Health check endpoint
    path('api/health/', health_check, name='health-check'),
    
    # API endpoints
    path('api/', include('users.urls')),
    path('api/', include('farms.urls')), 
    path('api/', include('equipment.urls')),
    path('api/', include('bookings.urls')),
    path('api/', include('inventory.urls')),
    path('api/', include('vendors.urls')),
    path('api/', include('farms.urls')),
    path('api/', include('messaging.urls')),  # Messaging system
    path('api/', include('chatbot.urls')),
    path('api/tasks/', include('tasks.urls')),

    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 