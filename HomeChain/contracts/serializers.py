from rest_framework import serializers
from django.utils import timezone
from .models import Contract, ContractMilestone, ContractAmendment, ContractTemplate
from accounts.serializers import UserSerializer, WorkerPublicSerializer
from jobs.serializers import JobSerializer

class ContractMilestoneSerializer(serializers.ModelSerializer):
    """Contract milestone serializer"""
    
    class Meta:
        model = ContractMilestone
        fields = [
            'id', 'contract', 'title', 'description', 'amount',
            'due_date', 'completed_date', 'status', 'completed_by',
            'completion_notes', 'payment_released', 'payment_tx_hash',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'contract', 'completed_date', 'status', 'completed_by',
            'payment_released', 'payment_tx_hash', 'created_at', 'updated_at'
        ]


class ContractSerializer(serializers.ModelSerializer):
    """Main Contract serializer"""
    
    employer_name = serializers.ReadOnlyField(source='employer.full_name')
    worker_name = serializers.ReadOnlyField(source='worker.full_name')
    job_title = serializers.ReadOnlyField(source='job.title')
    is_signed_by_both = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = Contract
        fields = [
            'id', 'job', 'job_title', 'employer', 'employer_name',
            'worker', 'worker_name', 'title', 'description', 'terms',
            'special_clauses', 'payment_amount', 'payment_schedule',
            'milestone_amounts', 'start_date', 'end_date',
            'working_hours_per_day', 'working_days',
            'employer_signed', 'worker_signed',
            'employer_signed_at', 'worker_signed_at',
            'contract_hash', 'escrow_id', 'transaction_hash',
            'status', 'is_template', 'version', 'notes',
            'is_signed_by_both', 'is_active', 'days_remaining',
            'created_at', 'updated_at', 'activated_at',
            'completed_at', 'terminated_at'
        ]
        read_only_fields = [
            'employer', 'worker', 'job', 'employer_signed',
            'worker_signed', 'employer_signed_at', 'worker_signed_at',
            'contract_hash', 'escrow_id', 'transaction_hash',
            'status', 'version', 'created_at', 'updated_at',
            'activated_at', 'completed_at', 'terminated_at',
            'is_signed_by_both', 'is_active', 'days_remaining'
        ]
    
    def validate(self, data):
        """Validate contract data"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date'
                })
        
        return data


class ContractCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating contracts"""
    
    class Meta:
        model = Contract
        fields = [
            'job', 'title', 'description', 'terms', 'special_clauses',
            'payment_amount', 'payment_schedule', 'milestone_amounts',
            'start_date', 'end_date', 'working_hours_per_day', 'working_days'
        ]
    
    def validate(self, data):
        job = data.get('job')
        
        # Check if job already has a contract
        if hasattr(job, 'contract'):
            raise serializers.ValidationError(
                'This job already has a contract'
            )
        
        # Check if job is in correct state
        if job.status != 'IN_PROGRESS' and job.status != 'OPEN':
            raise serializers.ValidationError(
                'Job must be in progress or open to create contract'
            )
        
        return data
    
    def create(self, validated_data):
        job = validated_data['job']
        validated_data['employer'] = job.employer
        validated_data['worker'] = job.worker
        validated_data['created_by'] = self.context['request'].user
        validated_data['status'] = 'PENDING'
        
        return super().create(validated_data)


class ContractSignSerializer(serializers.Serializer):
    """Serializer for signing contracts"""
    
    signature = serializers.CharField(required=False, help_text="Digital signature")
    ip_address = serializers.IPAddressField(required=False)
    
    def validate(self, data):
        contract = self.context['contract']
        user = self.context['request'].user
        
        # Check if contract is in pending state
        if contract.status != 'PENDING':
            raise serializers.ValidationError(
                f'Contract is {contract.get_status_display()}, cannot sign'
            )
        
        # Check if user is party to contract
        if user != contract.employer and user != contract.worker:
            raise serializers.ValidationError(
                'You are not a party to this contract'
            )
        
        # Check if already signed
        if user == contract.employer and contract.employer_signed:
            raise serializers.ValidationError(
                'You have already signed this contract'
            )
        if user == contract.worker and contract.worker_signed:
            raise serializers.ValidationError(
                'You have already signed this contract'
            )
        
        return data


class ContractDetailSerializer(serializers.ModelSerializer):
    """Detailed contract serializer with nested relations"""
    
    employer = UserSerializer(read_only=True)
    worker = WorkerPublicSerializer(read_only=True)
    job = JobSerializer(read_only=True)
    milestones = ContractMilestoneSerializer(many=True, read_only=True)
    
    class Meta:
        model = Contract
        fields = '__all__'
        depth = 1


class ContractAmendmentSerializer(serializers.ModelSerializer):
    """Contract amendment serializer"""
    
    proposed_by_name = serializers.ReadOnlyField(source='proposed_by.full_name')
    
    class Meta:
        model = ContractAmendment
        fields = [
            'id', 'contract', 'proposed_by', 'proposed_by_name',
            'title', 'description', 'changes',
            'employer_approved', 'worker_approved', 'status',
            'rejection_reason', 'created_at', 'updated_at',
            'approved_at', 'rejected_at'
        ]
        read_only_fields = [
            'proposed_by', 'employer_approved', 'worker_approved',
            'status', 'rejection_reason', 'created_at', 'updated_at',
            'approved_at', 'rejected_at'
        ]
    
    def create(self, validated_data):
        validated_data['proposed_by'] = self.context['request'].user
        return super().create(validated_data)


class ContractTemplateSerializer(serializers.ModelSerializer):
    """Contract template serializer"""
    
    class Meta:
        model = ContractTemplate
        fields = [
            'id', 'name', 'category', 'description', 'terms',
            'is_active', 'version', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'version']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)