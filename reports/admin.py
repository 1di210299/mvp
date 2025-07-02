from django.contrib import admin
from .models import (
    ReportTemplate, Report, KPIDefinition, KPIValue, 
    ReportSchedule, ReportDistribution
)


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'report_type', 'default_format', 'frequency', 'auto_send', 'is_active')
    list_filter = ('report_type', 'default_format', 'frequency', 'is_active', 'is_system_template')
    search_fields = ('name', 'description', 'company__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'template', 'status', 'date_from', 'date_to', 'file_format', 'generated_at')
    list_filter = ('status', 'file_format')
    search_fields = ('title', 'template__name')
    readonly_fields = ('created_at', 'updated_at', 'generated_at', 'sent_at')
    date_hierarchy = 'created_at'


@admin.register(KPIDefinition)
class KPIDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'company', 'calculation_type', 'data_source', 'is_active')
    list_filter = ('calculation_type', 'data_source', 'is_active', 'is_system_kpi')
    search_fields = ('name', 'description', 'code', 'company__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(KPIValue)
class KPIValueAdmin(admin.ModelAdmin):
    list_display = ('kpi_definition', 'period_start', 'period_end', 'period_type', 'value', 'calculated_at')
    list_filter = ('period_type',)
    search_fields = ('kpi_definition__name', 'kpi_definition__code')
    date_hierarchy = 'period_end'


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'schedule_type', 'hour', 'minute', 'is_active', 'next_run_at')
    list_filter = ('schedule_type', 'is_active')
    search_fields = ('name', 'template__name')
    readonly_fields = ('last_run_at', 'next_run_at', 'created_at', 'updated_at')


@admin.register(ReportDistribution)
class ReportDistributionAdmin(admin.ModelAdmin):
    list_display = ('report', 'distribution_type', 'status', 'sent_at', 'created_at')
    list_filter = ('distribution_type', 'status')
    search_fields = ('report__title',)
    readonly_fields = ('sent_at', 'delivered_at', 'created_at')
