from django.contrib import admin
from .models import Category, Product, Location, InventoryItem, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'is_active', 'created_at')
    list_filter = ('is_active', 'company', 'created_at')
    search_fields = ('name', 'description', 'company__name')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'company', 'sale_price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'company', 'created_at')
    search_fields = ('name', 'sku', 'description', 'company__name')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'is_active', 'created_at')
    list_filter = ('is_active', 'company', 'created_at')
    search_fields = ('name', 'address', 'company__name')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'location', 'quantity', 'reserved_quantity', 'unit_cost', 'updated_at')
    list_filter = ('location', 'product__company', 'updated_at')
    search_fields = ('product__name', 'product__sku', 'location__name')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'location', 'transaction_type', 'quantity', 'user', 'transaction_date')
    list_filter = ('transaction_type', 'location', 'product__company', 'transaction_date')
    search_fields = ('product__name', 'product__sku', 'reference_number', 'user__username')
