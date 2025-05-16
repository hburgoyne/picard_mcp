from django.urls import path
from . import views

urlpatterns = [
    path('', views.memory_list, name='memory_list'),
    path('create/', views.create_memory, name='create_memory'),
    path('update/<str:memory_id>/', views.update_memory, name='update_memory'),
    path('query/', views.query_user, name='query_user'),
]
