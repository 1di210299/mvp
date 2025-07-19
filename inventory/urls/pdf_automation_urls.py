"""
URLs para PDF Analysis y Status Update Automation
"""
from django.urls import path
from inventory.views.pdf_automation_views import (
    PDFAnalysisAPIView,
    StatusUpdateAutomationAPIView,
    PDFEmailProcessingAPIView,
    AutomationRulesAPIView,
    process_tracked_email_batch,
    automation_dashboard
)

urlpatterns = [
    # PDF Analysis endpoints
    path('analyze/', PDFAnalysisAPIView.as_view(), name='pdf-analyze'),
    
    # Status Update Automation endpoints
    path('automation/process/', StatusUpdateAutomationAPIView.as_view(), name='automation-process'),
    path('automation/stats/', StatusUpdateAutomationAPIView.as_view(), name='automation-stats'),
    path('automation/dashboard/', automation_dashboard, name='automation-dashboard'),
    
    # PDF Email Processing
    path('email-pdf/process/', PDFEmailProcessingAPIView.as_view(), name='pdf-email-process'),
    
    # Automation Rules
    path('automation/rules/', AutomationRulesAPIView.as_view(), name='automation-rules'),
    
    # Batch Processing
    path('automation/batch/', process_tracked_email_batch, name='automation-batch'),
]
