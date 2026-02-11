from rest_framework import serializers
from django.utils import timezone
from .models import (
    PaymentTransaction, PaymentWallet, PaymentEscrow, 
    PlatformFee, WithdrawalRequest
)
from accounts.serializers import UserSerializer
from contracts.serializers import ContractSerializer

class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Payment transaction serializer"""
    
    employer_name = serializers.ReadOnlyField(source='employer.full_name', default=None)
    worker_name = serializers.ReadOnlyField(source='worker.full_name', default=None)
    contract_title = serializers.ReadOnlyField(source='contract.job.title', default=None)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'contract', 'contract_title', 'employer', 'employer_name',
            'worker', 'worker_name', 'transaction_type', 'amount', 'platform_fee',
            'worker_amount', 'stellar_transaction_id', 'stellar_escrow_id',
            'status', 'error_message', 'description', 'milestone_id',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['stellar_transaction_id', 'status', 'created_at', 
                           'updated_at', 'completed_at']


class PaymentWalletSerializer(serializers.ModelSerializer):
    """Payment wallet serializer"""
    
    user_name = serializers.ReadOnlyField(source='user.full_name')
    
    class Meta:
        model = PaymentWallet
        fields = [
            'id', 'user', 'user_name', 'stellar_public_key',
            'available_balance', 'pending_balance', 'total_earned',
            'total_withdrawn', 'created_at', 'updated_at', 'last_synced_at'
        ]
        read_only_fields = ['stellar_public_key', 'stellar_secret_key', 
                           'available_balance', 'pending_balance', 
                           'total_earned', 'total_withdrawn', 'created_at']


class PaymentEscrowSerializer(serializers.ModelSerializer):
    """Payment escrow serializer"""
    
    contract_title = serializers.ReadOnlyField(source='contract.job.title')
    employer_name = serializers.ReadOnlyField(source='contract.employer.full_name')
    worker_name = serializers.ReadOnlyField(source='contract.worker.full_name')
    
    class Meta:
        model = PaymentEscrow
        fields = [
            'id', 'contract', 'contract_title', 'employer_name', 'worker_name',
            'stellar_escrow_id', 'stellar_contract_id', 'stellar_transaction_hash',
            'total_amount', 'platform_fee', 'worker_amount', 'released_amount',
            'status', 'employer_approved', 'worker_approved',
            'employer_approved_at', 'worker_approved_at',
            'created_at', 'funded_at', 'completed_at', 'disputed_at'
        ]
        read_only_fields = [
            'stellar_escrow_id', 'stellar_contract_id', 'stellar_transaction_hash',
            'status', 'employer_approved', 'worker_approved', 'created_at'
        ]


class PaymentEscrowActionSerializer(serializers.Serializer):
    """Serializer for escrow actions"""
    
    action = serializers.ChoiceField(
        choices=['approve', 'dispute', 'release'],
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        escrow = self.context['escrow']
        user = self.context['request'].user
        
        if data['action'] == 'approve':
            # Check if user is party to contract
            if user not in [escrow.contract.employer, escrow.contract.worker]:
                raise serializers.ValidationError(
                    'Only the employer or worker can approve'
                )
            
            # Check if already approved
            if user == escrow.contract.employer and escrow.employer_approved:
                raise serializers.ValidationError('You have already approved')
            if user == escrow.contract.worker and escrow.worker_approved:
                raise serializers.ValidationError('You have already approved')
        
        elif data['action'] == 'dispute':
            if user not in [escrow.contract.employer, escrow.contract.worker]:
                raise serializers.ValidationError(
                    'Only the employer or worker can raise a dispute'
                )
        
        return data


class PlatformFeeSerializer(serializers.ModelSerializer):
    """Platform fee serializer"""
    
    class Meta:
        model = PlatformFee
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    """Withdrawal request serializer"""
    
    worker_name = serializers.ReadOnlyField(source='worker.full_name')
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'worker', 'worker_name', 'amount', 'stellar_destination',
            'status', 'stellar_transaction_id', 'processed_by', 'processed_at',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'worker', 'status', 'stellar_transaction_id', 'processed_by',
            'processed_at', 'created_at', 'updated_at'
        ]
    
    def validate_amount(self, amount):
        user = self.context['request'].user
        
        # Check wallet balance
        try:
            wallet = user.wallet
            if wallet.available_balance < Decimal(str(amount)):
                raise serializers.ValidationError(
                    f'Insufficient balance. Available: ${wallet.available_balance}'
                )
        except PaymentWallet.DoesNotExist:
            raise serializers.ValidationError('Wallet not found')
        
        # Minimum withdrawal
        if amount < 10:
            raise serializers.ValidationError('Minimum withdrawal amount is $10')
        
        return amount
    
    def create(self, validated_data):
        validated_data['worker'] = self.context['request'].user
        return super().create(validated_data)


class WithdrawalProcessSerializer(serializers.Serializer):
    """Serializer for processing withdrawals (admin)"""
    
    action = serializers.ChoiceField(
        choices=['approve', 'reject'],
        required=True
    )
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['action'] == 'approve' and not data.get('transaction_id'):
            raise serializers.ValidationError(
                'Transaction ID is required for approval'
            )
        return data


class PaymentStatsSerializer(serializers.Serializer):
    """Payment statistics serializer"""
    
    total_volume = serializers.DecimalField(max_digits=12, decimal_places=2)
    platform_fees = serializers.DecimalField(max_digits=12, decimal_places=2)
    worker_payments = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_payments = serializers.DecimalField(max_digits=12, decimal_places=2)
    completed_transactions = serializers.IntegerField()
    pending_withdrawals = serializers.IntegerField()