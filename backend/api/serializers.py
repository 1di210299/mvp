from rest_framework import serializers
from .models import DataConnection, Dataset

class DataConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataConnection
        fields = '__all__'
        
class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = '__all__'