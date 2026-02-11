from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils import timezone

class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, email, username, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('Email is required')
        if not username:
            raise ValueError('Username is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'ADMIN')
        
        return self.create_user(email, username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """Custom User Model - Completely overridden"""
    
    USER_TYPES = (
        ('WORKER', 'Domestic Worker'),
        ('EMPLOYER', 'Employer'),
        ('ADMIN', 'Administrator'),
    )
    
    # Required fields
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    
    # Personal info
    full_name = models.CharField(max_length=100)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    
    # Stellar Blockchain Wallet
    stellar_public_key = models.CharField(max_length=56, unique=True, null=True, blank=True)
    stellar_secret_key = models.CharField(max_length=56, null=True, blank=True)  # TODO: Encrypt in production
    
    # WORKER specific fields
    skills = models.JSONField(default=list, blank=True)  # ["cleaning", "cooking"]
    experience_years = models.IntegerField(null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    
    # EMPLOYER specific fields
    company_name = models.CharField(max_length=100, blank=True)
    company_registration = models.CharField(max_length=100, blank=True)
    
    # Stats
    completed_jobs = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Django required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'user_type', 'full_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['user_type']),
        ]
    
    def __str__(self):
        return f"{self.full_name} - {self.user_type}"
    
    @property
    def is_worker(self):
        return self.user_type == 'WORKER'
    
    @property
    def is_employer(self):
        return self.user_type == 'EMPLOYER'
    
    @property
    def is_admin(self):
        return self.user_type == 'ADMIN'
    
    def get_full_name(self):
        return self.full_name
    
    def get_short_name(self):
        return self.username


class Skill(models.Model):
    """Predefined skills that workers can have"""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100)  # cleaning, cooking, childcare, etc.
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'skills'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class WorkerSkill(models.Model):
    """Worker's skills with proficiency and verification"""
    
    PROFICIENCY_LEVELS = (
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
    )
    
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='worker_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='worker_skills')
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_LEVELS, default='INTERMEDIATE')
    years_experience = models.PositiveIntegerField(default=0)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_skills'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_note = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'worker_skills'
        unique_together = ['worker', 'skill']
        indexes = [
            models.Index(fields=['worker', 'is_verified']),
        ]
    
    def __str__(self):
        return f"{self.worker.full_name} - {self.skill.name} ({self.proficiency})"


class WorkerDocument(models.Model):
    """Documents for worker verification"""
    
    DOCUMENT_TYPES = (
        ('ID', 'Government ID'),
        ('CERTIFICATE', 'Professional Certificate'),
        ('REFERENCE', 'Reference Letter'),
        ('BACKGROUND', 'Background Check'),
        ('TRAINING', 'Training Certificate'),
        ('OTHER', 'Other'),
    )
    
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    
    # File
    document_file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_size = models.IntegerField(help_text='File size in bytes', default=0)
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    
    # Document details
    document_number = models.CharField(max_length=100, blank=True)
    issued_by = models.CharField(max_length=200, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'worker_documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['worker', 'document_type']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.worker.full_name} - {self.get_document_type_display()}"
    
    def save(self, *args, **kwargs):
        if self.document_file:
            self.file_size = self.document_file.size
            self.file_name = self.document_file.name
            if hasattr(self.document_file.file, 'content_type'):
                self.mime_type = self.document_file.file.content_type
        super().save(*args, **kwargs)


class VerificationRequest(models.Model):
    """Track verification requests for workers"""
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests')
    documents = models.ManyToManyField(WorkerDocument, related_name='verification_requests')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'verification_requests'
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Verification Request - {self.worker.full_name} - {self.status}"