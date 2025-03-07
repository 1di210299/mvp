# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('test-connection/', views.test_connection, name='test_connection'),
    path('datasets/', views.create_dataset, name='create_dataset'),
    path('upload-dataset/', views.upload_dataset, name='upload_dataset'),
    path('generate-chart/', views.generate_chart, name='generate_chart'),
    path('predict-sales/', views.predict_sales_view, name='predict_sales'),
]
