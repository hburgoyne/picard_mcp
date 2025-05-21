from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError

def health_check(request):
    """Health check endpoint for the Django client."""
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except OperationalError:
        db_status = "unhealthy"
    
    # Return health status
    return JsonResponse({
        "status": "healthy",
        "database": db_status,
        "service": "django_client"
    })
