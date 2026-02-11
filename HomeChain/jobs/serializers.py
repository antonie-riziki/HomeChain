from rest_framework import serializers
from django.utils import timezone
from .models import Job, JobApplication, JobSaved
from accounts.serializers import UserSerializer, WorkerPublicSerializer

class JobSerializer(serializers.ModelSerializer):
    """Main Job serializer"""
    
    employer_name = serializers.ReadOnlyField(source='employer.full_name')
    employer_rating = serializers.ReadOnlyField(source='employer.average_rating')
    worker_name = serializers.ReadOnlyField(source='worker.full_name', default=None)
    
    class Meta:
        model = Job
        fields = [
            'id', 'employer', 'employer_name', 'employer_rating',
            'worker', 'worker_name', 'title', 'description', 'category',
            'skills_required', 'experience_level', 'location', 'is_remote',
            'start_date', 'end_date', 'estimated_duration',
            'payment_type', 'budget', 'hourly_rate_min', 'hourly_rate_max',
            'status', 'is_urgent', 'is_featured',
            'views_count', 'applications_count', 'shortlisted_count',
            'escrow_id', 'contract_id',
            'created_at', 'published_at', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'employer', 'worker', 'status', 'views_count',
            'applications_count', 'shortlisted_count',
            'escrow_id', 'contract_id', 'created_at', 'published_at',
            'started_at', 'completed_at'
        ]
    
    def validate(self, data):
        # Validate payment based on type
        if data.get('payment_type') == 'FIXED':
            if not data.get('budget'):
                raise serializers.ValidationError({
                    'budget': 'Budget is required for fixed price jobs'
                })
        elif data.get('payment_type') == 'HOURLY':
            if not data.get('hourly_rate_min') or not data.get('hourly_rate_max'):
                raise serializers.ValidationError({
                    'hourly_rate': 'Hourly rate range is required for hourly jobs'
                })
            if data['hourly_rate_min'] >= data['hourly_rate_max']:
                raise serializers.ValidationError({
                    'hourly_rate': 'Minimum rate must be less than maximum rate'
                })
        
        # Validate dates
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError({
                    'dates': 'Start date must be before end date'
                })
        
        return data
    
    def create(self, validated_data):
        validated_data['employer'] = self.context['request'].user
        return super().create(validated_data)


class JobDetailSerializer(serializers.ModelSerializer):
    """Detailed Job serializer with nested data"""
    
    employer = UserSerializer(read_only=True)
    worker = WorkerPublicSerializer(read_only=True)
    applications_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Job
        fields = '__all__'
        depth = 1


class JobCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating jobs"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'category', 'skills_required',
            'experience_level', 'location', 'is_remote',
            'start_date', 'end_date', 'estimated_duration',
            'payment_type', 'budget', 'hourly_rate_min', 'hourly_rate_max',
            'is_urgent'
        ]
    
    def validate_skills_required(self, skills):
        if not skills:
            raise serializers.ValidationError("At least one skill is required")
        return skills


class JobApplicationSerializer(serializers.ModelSerializer):
    """Job application serializer"""
    
    worker_name = serializers.ReadOnlyField(source='worker.full_name')
    worker_profile_picture = serializers.ImageField(
        source='worker.profile_picture', 
        read_only=True
    )
    job_title = serializers.ReadOnlyField(source='job.title')
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'job_title', 'worker', 'worker_name',
            'worker_profile_picture', 'cover_letter', 'proposed_rate',
            'estimated_days', 'worker_rating', 'worker_completed_jobs',
            'worker_hourly_rate', 'status', 'employer_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'worker', 'worker_rating', 'worker_completed_jobs',
            'worker_hourly_rate', 'status', 'created_at', 'updated_at'
        ]
    
    def validate_proposed_rate(self, rate):
        if rate <= 0:
            raise serializers.ValidationError("Proposed rate must be greater than 0")
        return rate
    
    def validate(self, data):
        job = data.get('job')
        worker = self.context['request'].user
        
        # Check if already applied
        if JobApplication.objects.filter(job=job, worker=worker).exists():
            raise serializers.ValidationError(
                "You have already applied for this job"
            )
        
        # Check if job is open
        if job.status != 'OPEN':
            raise serializers.ValidationError(
                "This job is not accepting applications"
            )
        
        return data
    
    def create(self, validated_data):
        validated_data['worker'] = self.context['request'].user
        return super().create(validated_data)


class JobApplicationDetailSerializer(serializers.ModelSerializer):
    """Detailed job application serializer"""
    
    worker = WorkerPublicSerializer(read_only=True)
    job = JobSerializer(read_only=True)
    
    class Meta:
        model = JobApplication
        fields = '__all__'
        depth = 1


class JobApplicationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating application status (employer only)"""
    
    class Meta:
        model = JobApplication
        fields = ['status', 'employer_notes']
    
    def validate_status(self, status):
        valid_statuses = ['SHORTLISTED', 'ACCEPTED', 'REJECTED']
        if status not in valid_statuses:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(valid_statuses)}"
            )
        return status


class JobSavedSerializer(serializers.ModelSerializer):
    """Saved jobs serializer"""
    
    job_title = serializers.ReadOnlyField(source='job.title')
    employer_name = serializers.ReadOnlyField(source='job.employer.full_name')
    
    class Meta:
        model = JobSaved
        fields = ['id', 'job', 'job_title', 'employer_name', 'created_at']
        read_only_fields = ['worker', 'created_at']
    
    def create(self, validated_data):
        validated_data['worker'] = self.context['request'].user
        return super().create(validated_data)


class JobPublicSerializer(serializers.ModelSerializer):
    """Public job listing serializer (no sensitive data)"""
    
    employer_name = serializers.ReadOnlyField(source='employer.full_name')
    employer_rating = serializers.ReadOnlyField(source='employer.average_rating')
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'description', 'category', 'skills_required',
            'experience_level', 'location', 'is_remote',
            'payment_type', 'budget', 'hourly_rate_min', 'hourly_rate_max',
            'status', 'is_urgent', 'is_featured',
            'employer_name', 'employer_rating',
            'applications_count', 'created_at'
        ]