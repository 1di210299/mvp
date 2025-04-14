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

# api/serializers.py
from rest_framework import serializers
from .models import BusinessRule, MonitoringLog, AgentAction, BusinessContext, AgentLearningLog

class BusinessRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessRule
        fields = '__all__'
        read_only_fields = ['owner', 'created_at', 'updated_at']

class MonitoringLogSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    
    class Meta:
        model = MonitoringLog
        fields = '__all__'
        read_only_fields = ['created_at']

class AgentActionSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    
    class Meta:
        model = AgentAction
        fields = '__all__'
        read_only_fields = ['created_at', 'executed_at']

class BusinessContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessContext
        fields = '__all__'
        read_only_fields = ['owner', 'created_at', 'updated_at']

class AgentLearningLogSerializer(serializers.ModelSerializer):
    action_description = serializers.CharField(source='action.description', read_only=True)
    
    class Meta:
        model = AgentLearningLog
        fields = '__all__'
        read_only_fields = ['created_at']