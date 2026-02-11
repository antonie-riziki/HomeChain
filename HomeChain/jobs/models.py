from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import User

class Job(models.Model):
    """Job posting by employer"""
    
    JOB_STATUS = (
        ('DRAFT', 'Draft'),
        ('OPEN', 'Open for Applications'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('DISPUTED', 'Disputed'),
    )
    
    PAYMENT_TYPE = (
        ('FIXED', 'Fixed Price'),
        ('HOURLY', 'Hourly Rate'),
    )
    
    EXPERIENCE_LEVEL = (
        ('ENTRY', 'Entry Level'),
        ('INTERMEDIATE', 'Intermediate'),
        ('EXPERT', 'Expert'),
    )
    
    # Relations
    employer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='jobs_posted',
        limit_choices_to={'user_type': 'EMPLOYER'}
    )
    worker = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='jobs_assigned',
        limit_choices_to={'user_type': 'WORKER'}
    )
    
    # Basic Info
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100)  # Cleaning, Cooking, etc.
    skills_required = models.JSONField(default=list)  # ["cleaning", "cooking"]
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL, default='ENTRY')
    
    # Location
    location = models.CharField(max_length=200)
    is_remote = models.BooleanField(default=False)
    
    # Schedule
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    estimated_duration = models.IntegerField(help_text="Estimated days to complete", default=1)
    
    # Payment
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE, default='FIXED')
    budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    hourly_rate_min = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.01)]
    )
    hourly_rate_max = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.01)]
    )
    
    # Status
    status = models.CharField(max_length=20, choices=JOB_STATUS, default='DRAFT')
    is_urgent = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # Tracking
    views_count = models.IntegerField(default=0)
    applications_count = models.IntegerField(default=0)
    shortlisted_count = models.IntegerField(default=0)
    
    # Blockchain
    escrow_id = models.CharField(max_length=100, null=True, blank=True)
    contract_id = models.CharField(max_length=100, null=True, blank=True)  # Contract app reference
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['employer', 'status']),
            models.Index(fields=['category']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"{self.title} - ${self.budget} - {self.get_status_display()}"
    
    def publish(self):
        """Publish job to make it open for applications"""
        self.status = 'OPEN'
        self.published_at = timezone.now()
        self.save()
    
    def assign_worker(self, worker):
        """Assign worker to job"""
        self.worker = worker
        self.status = 'IN_PROGRESS'
        self.started_at = timezone.now()
        self.save()
        
        # Reject all other pending applications
        self.applications.exclude(
            worker=worker
        ).filter(
            status='PENDING'
        ).update(status='REJECTED')
    
    def complete(self):
        """Mark job as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
        
        # Update worker stats
        if self.worker:
            self.worker.completed_jobs += 1
            self.worker.total_earned += self.budget
            self.worker.save()
        
        # Update employer stats
        self.employer.total_spent += self.budget
        self.employer.save()
    
    def cancel(self):
        """Cancel the job"""
        self.status = 'CANCELLED'
        self.save()
        
        # Reject all pending applications
        self.applications.filter(status='PENDING').update(status='REJECTED')
    
    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class JobApplication(models.Model):
    """Worker application for a job"""
    
    APPLICATION_STATUS = (
        ('PENDING', 'Pending Review'),
        ('SHORTLISTED', 'Shortlisted'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    )
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    worker = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='job_applications',
        limit_choices_to={'user_type': 'WORKER'}
    )
    
    # Application details
    cover_letter = models.TextField(max_length=2000)
    proposed_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    estimated_days = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Estimated days to complete"
    )
    
    # Worker info at time of application (snapshot)
    worker_rating = models.FloatField(default=0.0)
    worker_completed_jobs = models.IntegerField(default=0)
    worker_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='PENDING')
    employer_notes = models.TextField(blank=True, help_text="Private notes for employer")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_applications'
        ordering = ['-created_at']
        unique_together = ['job', 'worker']  # One application per job
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['worker', 'status']),
        ]
    
    def __str__(self):
        return f"{self.worker.full_name} applied for {self.job.title}"
    
    def save(self, *args, **kwargs):
        # Capture worker stats at time of application
        if not self.pk:  # Only on creation
            self.worker_rating = self.worker.average_rating
            self.worker_completed_jobs = self.worker.completed_jobs
            self.worker_hourly_rate = self.worker.hourly_rate
        super().save(*args, **kwargs)
    
    def shortlist(self):
        """Shortlist this application"""
        self.status = 'SHORTLISTED'
        self.save()
        
        # Update job shortlist count
        self.job.shortlisted_count = self.job.applications.filter(
            status='SHORTLISTED'
        ).count()
        self.job.save()
    
    def accept(self):
        """Accept this application and assign worker"""
        self.status = 'ACCEPTED'
        self.save()
        
        # Assign worker to job
        self.job.assign_worker(self.worker)
    
    def reject(self):
        """Reject this application"""
        self.status = 'REJECTED'
        self.save()
    
    def withdraw(self):
        """Withdraw application"""
        self.status = 'WITHDRAWN'
        self.save()


class JobSaved(models.Model):
    """Saved jobs for workers to apply later"""
    
    worker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_jobs',
        limit_choices_to={'user_type': 'WORKER'}
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'job_saved'
        unique_together = ['worker', 'job']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.worker.full_name} saved {self.job.title}"


class JobView(models.Model):
    """Track job views"""
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'job_views'
        ordering = ['-viewed_at']