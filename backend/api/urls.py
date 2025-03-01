# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('test-connection/', views.test_connection, name='test_connection'),
    path('datasets/', views.create_dataset, name='create_dataset'),
]