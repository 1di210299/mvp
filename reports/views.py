from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ReportTemplate, Report, KPIDefinition, KPIValue, ReportSchedule


# Stubs temporales para reports
class ReportTemplateViewSet(viewsets.ModelViewSet):
    queryset = ReportTemplate.objects.none()
    def list(self, request): return Response([])

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.none()
    def list(self, request): return Response([])

class KPIDefinitionViewSet(viewsets.ModelViewSet):
    queryset = KPIDefinition.objects.none()
    def list(self, request): return Response([])

class KPIValueViewSet(viewsets.ModelViewSet):
    queryset = KPIValue.objects.none()
    def list(self, request): return Response([])

class ReportScheduleViewSet(viewsets.ModelViewSet):
    queryset = ReportSchedule.objects.none()
    def list(self, request): return Response([])

class GenerateReportView(APIView):
    def post(self, request): return Response({'message': 'En desarrollo'})

class DownloadReportView(APIView):
    def get(self, request, report_id): return Response({'message': 'En desarrollo'})

class ReportsDashboardView(APIView):
    def get(self, request): return Response({'message': 'En desarrollo'})

class CalculateKPIsView(APIView):
    def post(self, request): return Response({'message': 'En desarrollo'})

class ExportDataView(APIView):
    def post(self, request): return Response({'message': 'En desarrollo'})
