from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    PaymentTransaction, PaymentWallet, PaymentEscrow, 
    PlatformFee, WithdrawalRequest
)

from django.utils import timezone

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'transaction_type', 'contract_link', 'amount', 
        'status', 'stellar_transaction_id_short', 'created_at'
    ]
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['stellar_transaction_id', 'description', 'contract__job__title']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('contract', 'employer', 'worker', 'transaction_type')
        }),
        ('Amounts', {
            'fields': ('amount', 'platform_fee', 'worker_amount')
        }),
        ('Blockchain', {
            'fields': ('stellar_transaction_id', 'stellar_escrow_id', 
                      'stellar_source_account', 'stellar_destination_account')
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'description', 'milestone_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def contract_link(self, obj):
        if obj.contract:
            url = reverse('admin:contracts_contract_change', args=[obj.contract.id])
            return format_html('<a href="{}">{}</a>', url, obj.contract.job.title)
        return '-'
    contract_link.short_description = 'Contract'
    
    def stellar_transaction_id_short(self, obj):
        if obj.stellar_transaction_id:
            return obj.stellar_transaction_id[:8] + '...'
        return '-'
    stellar_transaction_id_short.short_description = 'Transaction ID'
    
    actions = ['mark_as_success', 'mark_as_failed']
    
    def mark_as_success(self, request, queryset):
        queryset.update(status='SUCCESS', completed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} transactions marked as success.")
    mark_as_success.short_description = "Mark selected as Success"
    
    def mark_as_failed(self, request, queryset):
        queryset.update(status='FAILED')
        self.message_user(request, f"{queryset.count()} transactions marked as failed.")
    mark_as_failed.short_description = "Mark selected as Failed"


@admin.register(PaymentWallet)
class PaymentWalletAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'stellar_public_key_short', 'available_balance', 
                   'pending_balance', 'total_earned', 'last_synced_at']
    search_fields = ['user__full_name', 'user__email', 'stellar_public_key']
    readonly_fields = ['created_at', 'updated_at', 'last_synced_at']
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.full_name)
    user_link.short_description = 'User'
    
    def stellar_public_key_short(self, obj):
        return obj.stellar_public_key[:8] + '...'
    stellar_public_key_short.short_description = 'Stellar Public Key'


@admin.register(PaymentEscrow)
class PaymentEscrowAdmin(admin.ModelAdmin):
    list_display = ['id', 'contract_link', 'total_amount', 'status', 
                   'employer_approved', 'worker_approved', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['stellar_escrow_id', 'contract__job__title']
    readonly_fields = ['created_at', 'funded_at', 'completed_at', 'disputed_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Contract', {
            'fields': ('contract',)
        }),
        ('Blockchain', {
            'fields': ('stellar_escrow_id', 'stellar_contract_id', 'stellar_transaction_hash')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'platform_fee', 'worker_amount', 'released_amount')
        }),
        ('Status', {
            'fields': ('status', 'employer_approved', 'worker_approved',
                      'employer_approved_at', 'worker_approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'funded_at', 'completed_at', 'disputed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def contract_link(self, obj):
        url = reverse('admin:contracts_contract_change', args=[obj.contract.id])
        return format_html('<a href="{}">{}</a>', url, obj.contract.job.title)
    contract_link.short_description = 'Contract'
    
    actions = ['mark_as_funded', 'mark_as_completed']
    
    def mark_as_funded(self, request, queryset):
        queryset.update(status='FUNDED', funded_at=timezone.now())
        self.message_user(request, f"{queryset.count()} escrows marked as funded.")
    mark_as_funded.short_description = "Mark selected as Funded"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='COMPLETED', completed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} escrows marked as completed.")
    mark_as_completed.short_description = "Mark selected as Completed"


@admin.register(PlatformFee)
class PlatformFeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'fee_type', 'fee_value', 'min_fee', 'max_fee', 
                   'is_active', 'effective_from', 'effective_to']
    list_filter = ['fee_type', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active']


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ['worker_link', 'amount', 'stellar_destination_short', 
                   'status', 'created_at', 'processed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['worker__full_name', 'stellar_transaction_id']
    readonly_fields = ['created_at', 'updated_at', 'processed_at']
    
    def worker_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.worker.id])
        return format_html('<a href="{}">{}</a>', url, obj.worker.full_name)
    worker_link.short_description = 'Worker'
    
    def stellar_destination_short(self, obj):
        return obj.stellar_destination[:8] + '...'
    stellar_destination_short.short_description = 'Destination'
    
    actions = ['approve_withdrawals', 'reject_withdrawals']
    
    def approve_withdrawals(self, request, queryset):
        queryset.update(status='COMPLETED', processed_by=request.user, 
                       processed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} withdrawals approved.")
    approve_withdrawals.short_description = "Approve selected withdrawals"
    
    def reject_withdrawals(self, request, queryset):
        queryset.update(status='CANCELLED')
        self.message_user(request, f"{queryset.count()} withdrawals rejected.")
    reject_withdrawals.short_description = "Reject selected withdrawals"
