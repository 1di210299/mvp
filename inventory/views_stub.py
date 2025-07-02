from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Category, Supplier, Location, Product, InventoryItem, Transaction


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.none()
    def list(self, request): return Response([])

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.none()
    def list(self, request): return Response([])

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.none()
    def list(self, request): return Response([])

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.none()
    def list(self, request): return Response([])

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.none()
    def list(self, request): return Response([])

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.none()
    def list(self, request): return Response([])

class DashboardView(APIView):
    def get(self, request): return Response({'message': 'En desarrollo'})

class FileUploadView(APIView):
    def post(self, request): return Response({'message': 'En desarrollo'})

class ProductStockView(APIView):
    def get(self, request, product_id): return Response({'message': 'En desarrollo'})

class LowStockView(APIView):
    def get(self, request): return Response({'message': 'En desarrollo'})

class StockMovementsView(APIView):
    def get(self, request): return Response({'message': 'En desarrollo'})
