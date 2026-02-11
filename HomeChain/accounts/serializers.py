from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from .models import User, Skill, WorkerSkill, WorkerDocument, VerificationRequest
from .utils import create_stellar_account, validate_file_size, validate_file_extension

class UserSerializer(serializers.ModelSerializer):
    """Main User serializer"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'user_type', 'full_name', 'phone',
            'location', 'profile_picture', 'bio', 'stellar_public_key',
            'skills', 'experience_years', 'hourly_rate', 'is_verified',
            'is_available', 'company_name', 'company_registration',
            'completed_jobs', 'average_rating', 'total_earned', 'total_spent',
            'date_joined', 'is_active'
        ]
        read_only_fields = [
            'stellar_public_key', 'is_verified', 'completed_jobs',
            'average_rating', 'total_earned', 'total_spent', 'date_joined'
        ]
        extra_kwargs = {
            'profile_picture': {'required': False},
            'phone': {'required': False},
            'location': {'required': False},
            'bio': {'required': False},
        }


class RegisterSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password', 'user_type',
            'full_name', 'phone', 'location', 'skills', 'hourly_rate',
            'experience_years', 'bio', 'company_name', 'company_registration'
        ]
    
    def validate(self, data):
        # Validate passwords match
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "password": "Passwords do not match."
            })
        
        # Validate worker has required fields
        if data['user_type'] == 'WORKER':
            if not data.get('skills'):
                raise serializers.ValidationError({
                    "skills": "Workers must specify at least one skill."
                })
            if not data.get('hourly_rate'):
                raise serializers.ValidationError({
                    "hourly_rate": "Workers must set an hourly rate."
                })
            if data.get('hourly_rate') and float(data['hourly_rate']) <= 0:
                raise serializers.ValidationError({
                    "hourly_rate": "Hourly rate must be greater than 0."
                })
        
        # Validate employer has company name
        if data['user_type'] == 'EMPLOYER':
            if not data.get('company_name'):
                raise serializers.ValidationError({
                    "company_name": "Employers must provide a company name."
                })
        
        return data
    
    def create(self, validated_data):
        # Remove confirm_password
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            user_type=validated_data['user_type'],
            full_name=validated_data.get('full_name', ''),
            phone=validated_data.get('phone', ''),
            location=validated_data.get('location', ''),
            bio=validated_data.get('bio', ''),
        )
        
        # Set worker-specific fields
        if user.user_type == 'WORKER':
            # Create Stellar wallet
            stellar_account = create_stellar_account()
            user.stellar_public_key = stellar_account['public_key']
            user.stellar_secret_key = stellar_account['secret_key']
            user.skills = validated_data.get('skills', [])
            user.hourly_rate = validated_data.get('hourly_rate')
            user.experience_years = validated_data.get('experience_years', 0)
            user.is_available = True
        
        # Set employer-specific fields
        elif user.user_type == 'EMPLOYER':
            user.company_name = validated_data.get('company_name', '')
            user.company_registration = validated_data.get('company_registration', '')
        
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """User login serializer"""
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        user = authenticate(
            username=data['username'],
            password=data['password']
        )
        
        if not user:
            raise serializers.ValidationError(
                "Unable to log in with provided credentials."
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                "User account is disabled."
            )
        
        refresh = RefreshToken.for_user(user)
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }


class SkillSerializer(serializers.ModelSerializer):
    """Skill serializer"""
    
    class Meta:
        model = Skill
        fields = ['id', 'name', 'category', 'description', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class WorkerSkillSerializer(serializers.ModelSerializer):
    """Worker skill serializer"""
    
    skill_name = serializers.ReadOnlyField(source='skill.name')
    skill_category = serializers.ReadOnlyField(source='skill.category')
    worker_name = serializers.ReadOnlyField(source='worker.full_name')
    
    class Meta:
        model = WorkerSkill
        fields = [
            'id', 'worker', 'worker_name', 'skill', 'skill_name', 
            'skill_category', 'proficiency', 'years_experience',
            'is_verified', 'verified_at', 'verification_note',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['is_verified', 'verified_at', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Check if skill already exists for this worker
        worker = self.context['request'].user
        skill = data.get('skill')
        
        if self.instance is None:  # Creating new
            if WorkerSkill.objects.filter(worker=worker, skill=skill).exists():
                raise serializers.ValidationError(
                    "You have already added this skill."
                )
        
        return data
    
    def create(self, validated_data):
        validated_data['worker'] = self.context['request'].user
        return super().create(validated_data)


class WorkerDocumentSerializer(serializers.ModelSerializer):
    """Worker document serializer"""
    
    class Meta:
        model = WorkerDocument
        fields = [
            'id', 'worker', 'document_type', 'title', 'document_file',
            'file_name', 'file_size', 'mime_type', 'document_number',
            'issued_by', 'issue_date', 'expiry_date', 'is_verified',
            'rejection_reason', 'uploaded_at', 'updated_at'
        ]
        read_only_fields = [
            'worker', 'file_name', 'file_size', 'mime_type',
            'is_verified', 'rejection_reason', 'uploaded_at', 'updated_at'
        ]
        extra_kwargs = {
            'document_file': {'write_only': True}
        }
    
    def validate_document_file(self, file):
        # Validate file size
        is_valid, error = validate_file_size(file, max_size_mb=10)
        if not is_valid:
            raise serializers.ValidationError(error)
        
        # Validate file extension
        is_valid, error = validate_file_extension(file)
        if not is_valid:
            raise serializers.ValidationError(error)
        
        return file
    
    def create(self, validated_data):
        validated_data['worker'] = self.context['request'].user
        return super().create(validated_data)


class VerificationRequestSerializer(serializers.ModelSerializer):
    """Verification request serializer"""
    
    worker_name = serializers.ReadOnlyField(source='worker.full_name')
    documents = WorkerDocumentSerializer(many=True, read_only=True)
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )
    
    class Meta:
        model = VerificationRequest
        fields = [
            'id', 'worker', 'worker_name', 'documents', 'document_ids',
            'status', 'admin_notes', 'submitted_at', 'reviewed_at'
        ]
        read_only_fields = [
            'worker', 'status', 'admin_notes', 'submitted_at', 'reviewed_at'
        ]
    
    def validate_document_ids(self, document_ids):
        worker = self.context['request'].user
        
        # Verify all documents belong to this worker
        documents = WorkerDocument.objects.filter(
            id__in=document_ids,
            worker=worker
        )
        
        if len(documents) != len(document_ids):
            raise serializers.ValidationError(
                "One or more documents are invalid or do not belong to you."
            )
        
        # Check if any documents are already verified
        if documents.filter(is_verified=True).exists():
            raise serializers.ValidationError(
                "Some documents are already verified."
            )
        
        return document_ids
    
    def create(self, validated_data):
        document_ids = validated_data.pop('document_ids')
        worker = self.context['request'].user
        
        # Check for existing pending request
        if VerificationRequest.objects.filter(
            worker=worker,
            status='PENDING'
        ).exists():
            raise serializers.ValidationError(
                "You already have a pending verification request."
            )
        
        # Create verification request
        verification_request = VerificationRequest.objects.create(
            worker=worker,
            **validated_data
        )
        
        # Add documents
        documents = WorkerDocument.objects.filter(id__in=document_ids)
        verification_request.documents.add(*documents)
        
        return verification_request


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = User
        fields = [
            'full_name', 'phone', 'location', 'bio', 'profile_picture',
            'skills', 'hourly_rate', 'experience_years', 'is_available',
            'company_name', 'company_registration'
        ]
        extra_kwargs = {
            'profile_picture': {'required': False},
            'skills': {'required': False},
            'hourly_rate': {'required': False},
        }
    
    def validate(self, data):
        user = self.context['request'].user
        
        # Worker-specific validations
        if user.user_type == 'WORKER':
            if 'hourly_rate' in data and float(data['hourly_rate']) <= 0:
                raise serializers.ValidationError({
                    "hourly_rate": "Hourly rate must be greater than 0."
                })
        
        return data
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class WorkerPublicSerializer(serializers.ModelSerializer):
    """Public serializer for workers (no sensitive data)"""
    
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'location', 'profile_picture', 'bio',
            'skills', 'experience_years', 'hourly_rate', 'is_verified',
            'is_available', 'completed_jobs', 'average_rating'
        ]