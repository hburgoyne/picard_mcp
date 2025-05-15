from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
import redis
from django.conf import settings

class HealthCheckView(APIView):
    """
    Health check endpoint that verifies database and cache connections.
    """
    permission_classes = []
    authentication_classes = []
    
    def get(self, request, *args, **kwargs):
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_ok = cursor.fetchone()
        except Exception as e:
            db_ok = False
            db_error = str(e)
        
        # Check Redis connection
        try:
            r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
            redis_ok = r.ping()
        except Exception as e:
            redis_ok = False
            redis_error = str(e)
        
        status_code = status.HTTP_200_OK if all([db_ok, redis_ok]) else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response({
            'status': 'ok' if status_code == 200 else 'error',
            'database': {
                'status': 'ok' if db_ok else 'error',
                'error': locals().get('db_error', None)
            },
            'cache': {
                'status': 'ok' if redis_ok else 'error',
                'error': locals().get('redis_error', None)
            }
        }, status=status_code)
