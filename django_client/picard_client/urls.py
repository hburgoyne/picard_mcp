from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('oauth_client.urls')),
    path('memories/', include('memory_manager.urls')),
]
