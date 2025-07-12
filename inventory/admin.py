from django.contrib import admin
from .models import Category, Supplier, Product, Sale, Alert, InventoryHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_name', 'email', 'phone', 'city', 'is_active', 'created_at')
    list_filter = ('is_active', 'city', 'country', 'created_at')
    search_fields = ('name', 'contact_name', 'email', 'tax_id')
    ordering = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'supplier', 'stock', 'min_stock', 'max_stock', 'cost_price', 'sale_price', 'is_active')
    list_filter = ('is_active', 'category', 'supplier', 'created_at')
    search_fields = ('name', 'sku', 'description', 'barcode')
    ordering = ('name',)
    list_editable = ('stock', 'min_stock', 'max_stock')
    readonly_fields = ('current_stock', 'stock_value', 'created_at', 'updated_at')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'unit_price', 'total_amount', 'customer_name', 'date_sold')
    list_filter = ('date_sold', 'product')
    search_fields = ('product__name', 'customer_name')
    readonly_fields = ('total_amount',)
    ordering = ('-date_sold',)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('message', 'severity', 'is_active', 'product', 'created_at')
    list_filter = ('severity', 'is_active', 'created_at', 'product')
    search_fields = ('message', 'product__name')
    list_editable = ('is_active',)
    ordering = ('-created_at',)


@admin.register(InventoryHistory)
class InventoryHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'stock_before', 'stock_after', 'change_reason', 'user', 'date_changed')
    list_filter = ('change_reason', 'date_changed', 'product')
    search_fields = ('product__name', 'change_reason', 'user__username')
    readonly_fields = ('date_changed',)
    ordering = ('-date_changed',)
