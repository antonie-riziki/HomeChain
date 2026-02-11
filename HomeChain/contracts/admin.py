from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Contract, ContractMilestone, ContractAmendment, ContractTemplate

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'job_link', 'employer_link', 'worker_link', 
        'payment_amount', 'status', 'is_signed_by_both', 'created_at'
    ]
    list_filter = ['status', 'payment_schedule', 'created_at']
    search_fields = ['job__title', 'employer__full_name', 'worker__full_name']
    readonly_fields = [
        'contract_hash', 'escrow_id', 'transaction_hash',
        'employer_signed_at', 'worker_signed_at',
        'activated_at', 'completed_at', 'terminated_at',
        'created_at', 'updated_at'
    ]
    list_editable = ['status']
    
    fieldsets = (
        ('Job Information', {
            'fields': ('job', 'employer', 'worker', 'title', 'description')
        }),
        ('Contract Terms', {
            'fields': ('terms', 'special_clauses')
        }),
        ('Payment', {
            'fields': ('payment_amount', 'payment_schedule', 'milestone_amounts')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'working_hours_per_day', 'working_days')
        }),
        ('Signatures', {
            'fields': ('employer_signed', 'worker_signed', 
                      'employer_signed_at', 'worker_signed_at',
                      'employer_signature_ip', 'worker_signature_ip')
        }),
        ('Blockchain', {
            'fields': ('contract_hash', 'escrow_id', 'transaction_hash'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'is_template', 'version', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'activated_at', 
                      'completed_at', 'terminated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def job_link(self, obj):
        url = reverse('admin:jobs_job_change', args=[obj.job.id])
        return format_html('<a href="{}">{}</a>', url, obj.job.title)
    job_link.short_description = 'Job'
    
    def employer_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.employer.id])
        return format_html('<a href="{}">{}</a>', url, obj.employer.full_name)
    employer_link.short_description = 'Employer'
    
    def worker_link(self, obj):
        if obj.worker:
            url = reverse('admin:accounts_user_change', args=[obj.worker.id])
            return format_html('<a href="{}">{}</a>', url, obj.worker.full_name)
        return '-'
    worker_link.short_description = 'Worker'
    
    def is_signed_by_both(self, obj):
        if obj.employer_signed and obj.worker_signed:
            return format_html('<span style="color: green;">✓ Both Signed</span>')
        elif obj.employer_signed:
            return format_html('<span style="color: orange;">Employer Only</span>')
        elif obj.worker_signed:
            return format_html('<span style="color: orange;">Worker Only</span>')
        else:
            return format_html('<span style="color: red;">Not Signed</span>')
    is_signed_by_both.short_description = 'Signatures'
    
    actions = ['activate_contracts', 'complete_contracts']
    
    def activate_contracts(self, request, queryset):
        for contract in queryset:
            if contract.employer_signed and contract.worker_signed and contract.status == 'PENDING':
                contract.status = 'ACTIVE'
                contract.activated_at = timezone.now()
                contract.save()
        self.message_user(request, f"{queryset.count()} contracts activated.")
    activate_contracts.short_description = "Activate selected contracts"
    
    def complete_contracts(self, request, queryset):
        queryset.update(status='COMPLETED', completed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} contracts completed.")
    complete_contracts.short_description = "Complete selected contracts"


@admin.register(ContractMilestone)
class ContractMilestoneAdmin(admin.ModelAdmin):
    list_display = ['contract_link', 'title', 'amount', 'due_date', 'status']
    list_filter = ['status', 'due_date']
    search_fields = ['contract__job__title', 'title']
    list_editable = ['status']
    
    def contract_link(self, obj):
        url = reverse('admin:contracts_contract_change', args=[obj.contract.id])
        return format_html('<a href="{}">{}</a>', url, obj.contract.job.title)
    contract_link.short_description = 'Contract'


@admin.register(ContractAmendment)
class ContractAmendmentAdmin(admin.ModelAdmin):
    list_display = ['contract_link', 'title', 'proposed_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['contract__job__title', 'title']
    
    def contract_link(self, obj):
        url = reverse('admin:contracts_contract_change', args=[obj.contract.id])
        return format_html('<a href="{}">{}</a>', url, obj.contract.job.title)
    contract_link.short_description = 'Contract'


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'version', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']