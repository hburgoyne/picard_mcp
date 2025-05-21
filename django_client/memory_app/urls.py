from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('oauth/authorize/', views.oauth_authorize, name='oauth_authorize'),
    path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
    path('oauth/refresh/', views.refresh_token, name='refresh_token'),
    path('memories/create/', views.create_memory, name='create_memory'),
    path('memories/edit/<uuid:memory_id>/', views.edit_memory, name='edit_memory'),
    path('memories/delete/<uuid:memory_id>/', views.delete_memory, name='delete_memory'),
    path('memories/search/', views.search_memories, name='search_memories'),
    path('memories/sync/', views.sync_memories, name='sync_memories'),
    path('query/user/', views.query_user, name='query_user'),
]
