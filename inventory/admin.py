from django.contrib import admin
from inventory.models import Category, Supplier, Product, Sale, Alert, InventoryHistory
from inventory.models import EmailCampaign, TrackedEmail, EmailClick, EmailPattern, EmailInsight, GmailWebhookLog


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


# ==============================================
# EMAIL TRACKING SERVICE ADMIN
# ==============================================

@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'total_sent', 'total_opened', 'total_clicked', 'open_rate_display', 'is_active', 'created_at')
    list_filter = ('is_active', 'track_opens', 'track_clicks', 'created_at', 'company')
    search_fields = ('name', 'description', 'company__name')
    readonly_fields = ('id', 'total_sent', 'total_delivered', 'total_opened', 'total_clicked', 'total_bounced', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def open_rate_display(self, obj):
        return f"{obj.open_rate:.1f}%"
    open_rate_display.short_description = "Open Rate"


@admin.register(TrackedEmail)
class TrackedEmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'recipient_email', 'status', 'campaign', 'sent_at', 'first_opened_at', 'open_count', 'click_count')
    list_filter = ('status', 'campaign', 'sent_at', 'company')
    search_fields = ('subject', 'recipient_email', 'recipient_name', 'tracking_id', 'email_id')
    readonly_fields = ('tracking_id', 'email_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('email_id', 'tracking_id', 'campaign', 'company')
        }),
        ('Destinatario', {
            'fields': ('recipient_email', 'recipient_name')
        }),
        ('Contenido', {
            'fields': ('subject', 'content_preview')
        }),
        ('Estado y Tracking', {
            'fields': ('status', 'sent_at', 'delivered_at', 'first_opened_at', 'last_opened_at', 
                      'first_clicked_at', 'last_clicked_at', 'replied_at', 'bounced_at')
        }),
        ('Contadores', {
            'fields': ('open_count', 'click_count')
        }),
        ('Datos Técnicos', {
            'fields': ('user_agent', 'ip_address', 'location_data', 'device_info'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(EmailClick)
class EmailClickAdmin(admin.ModelAdmin):
    list_display = ('tracked_email_subject', 'url', 'clicked_at', 'device_type', 'browser')
    list_filter = ('clicked_at', 'device_type', 'browser')
    search_fields = ('url', 'link_text', 'tracked_email__subject', 'tracked_email__recipient_email')
    readonly_fields = ('clicked_at',)
    ordering = ('-clicked_at',)
    
    def tracked_email_subject(self, obj):
        return obj.tracked_email.subject[:50] + "..." if len(obj.tracked_email.subject) > 50 else obj.tracked_email.subject
    tracked_email_subject.short_description = "Email Subject"


@admin.register(EmailPattern)
class EmailPatternAdmin(admin.ModelAdmin):
    list_display = ('name', 'pattern_type', 'company', 'confidence', 'frequency', 'impact_score', 'is_active', 'detected_at')
    list_filter = ('pattern_type', 'is_active', 'detected_at', 'company')
    search_fields = ('name', 'description', 'company__name')
    readonly_fields = ('detected_at',)
    ordering = ('-confidence', '-impact_score', '-detected_at')
    
    fieldsets = (
        ('Información del Patrón', {
            'fields': ('company', 'pattern_type', 'name', 'description')
        }),
        ('Métricas', {
            'fields': ('frequency', 'confidence', 'impact_score')
        }),
        ('Datos del Patrón', {
            'fields': ('pattern_data', 'examples'),
            'classes': ('collapse',)
        }),
        ('Recomendaciones', {
            'fields': ('recommendation', 'action_items')
        }),
        ('Período y Estado', {
            'fields': ('period_start', 'period_end', 'is_active', 'detected_at')
        })
    )


@admin.register(EmailInsight)
class EmailInsightAdmin(admin.ModelAdmin):
    list_display = ('title', 'insight_type', 'priority', 'company', 'confidence_score', 'is_implemented', 'generated_at')
    list_filter = ('insight_type', 'priority', 'is_implemented', 'generated_by_ai', 'generated_at', 'company')
    search_fields = ('title', 'description', 'company__name')
    readonly_fields = ('generated_at', 'implemented_at')
    ordering = ('-priority', '-confidence_score', '-generated_at')
    
    fieldsets = (
        ('Información del Insight', {
            'fields': ('company', 'insight_type', 'priority', 'title', 'description')
        }),
        ('Análisis', {
            'fields': ('confidence_score', 'impact_potential', 'generated_by_ai', 'source_data_period')
        }),
        ('Acciones', {
            'fields': ('action_items', 'expected_outcome')
        }),
        ('Implementación', {
            'fields': ('is_implemented', 'implemented_at', 'implementation_notes')
        }),
        ('Relaciones', {
            'fields': ('related_patterns',)
        }),
        ('Metadatos', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(GmailWebhookLog)
class GmailWebhookLogAdmin(admin.ModelAdmin):
    list_display = ('company', 'email_address', 'history_id', 'processing_success', 'processed_at')
    list_filter = ('processing_success', 'processed_at', 'company')
    search_fields = ('email_address', 'history_id', 'company__name')
    readonly_fields = ('processed_at',)
    ordering = ('-processed_at',)
    
    fieldsets = (
        ('Información del Webhook', {
            'fields': ('company', 'email_address', 'history_id')
        }),
        ('Procesamiento', {
            'fields': ('processing_success', 'error_message', 'processed_at')
        }),
        ('Datos', {
            'fields': ('raw_payload', 'processed_changes'),
            'classes': ('collapse',)
        })
    )
