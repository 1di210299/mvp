from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ForecastModel, DemandForecast, ReorderRecommendation


# Stubs temporales para forecasting
class ForecastModelViewSet(viewsets.ModelViewSet):
    queryset = ForecastModel.objects.none()
    def list(self, request): return Response([])

class DemandForecastViewSet(viewsets.ModelViewSet):
    queryset = DemandForecast.objects.none()
    def list(self, request): return Response([])

class ReorderRecommendationViewSet(viewsets.ModelViewSet):
    queryset = ReorderRecommendation.objects.none()
    def list(self, request): return Response([])

class PredictDemandView(APIView):
    def post(self, request): return Response({'message': 'En desarrollo'})

class TrainModelView(APIView):
    def post(self, request): return Response({'message': 'En desarrollo'})

class ModelAccuracyView(APIView):
    def get(self, request, model_id): return Response({'message': 'En desarrollo'})

class ProductForecastView(APIView):
    def get(self, request, product_id): return Response({'message': 'En desarrollo'})

class GenerateRecommendationsView(APIView):
    def post(self, request): return Response({'message': 'En desarrollo'})
