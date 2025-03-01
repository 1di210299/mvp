from django.db import models

class DataConnection(models.Model):
    CONNECTION_TYPES = [
        ('sql', 'SQL Database'),
        ('aws', 'AWS S3'),
        ('bigquery', 'Google BigQuery'),
    ]
    
    name = models.CharField(max_length=255)
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPES)
    connection_string = models.CharField(max_length=255)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    query = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.connection_type})"

    class Meta:
        app_label = 'api'

class Dataset(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    connection = models.ForeignKey(DataConnection, on_delete=models.CASCADE, related_name='datasets')
    columns = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

    class Meta:
        app_label = 'api'