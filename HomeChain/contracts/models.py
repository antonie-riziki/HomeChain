from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import User
from jobs.models import Job
import hashlib
import json

class Contract(models.Model):
    """Digital contract between employer and worker"""
    
    CONTRACT_STATUS = (
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Signatures'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('TERMINATED', 'Terminated'),
        ('DISPUTED', 'Disputed'),
    )
    
    PAYMENT_SCHEDULE = (
        ('FULL', 'Full Payment Upon Completion'),
        ('HALF', '50% Advance, 50% Upon Completion'),
        ('MILESTONE', 'Milestone Based'),
        ('WEEKLY', 'Weekly Payment'),
    )
    
    # Relations
    job = models.OneToOneField(
        Job, 
        on_delete=models.CASCADE, 
        related_name='contract'
    )
    employer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='contracts_as_employer'
    )
    worker = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='contracts_as_worker'
    )
    
    # Contract Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    terms = models.TextField(help_text="Full contract terms and conditions")
    special_clauses = models.TextField(blank=True, help_text="Custom clauses agreed by both parties")
    
    # Payment Terms
    payment_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    payment_schedule = models.CharField(
        max_length=20, 
        choices=PAYMENT_SCHEDULE, 
        default='FULL'
    )
    milestone_amounts = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of milestone payments"
    )
    
    # Duration
    start_date = models.DateField()
    end_date = models.DateField()
    working_hours_per_day = models.IntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(24)]
    )
    # Fixed: Changed from ArrayField to JSONField for SQLite compatibility
    working_days = models.JSONField(
        default=list,
        blank=True,
        help_text="Days of week: MON, TUE, WED, THU, FRI, SAT, SUN"
    )
    
    # Signatures
    employer_signed = models.BooleanField(default=False)
    worker_signed = models.BooleanField(default=False)
    employer_signed_at = models.DateTimeField(null=True, blank=True)
    worker_signed_at = models.DateTimeField(null=True, blank=True)
    employer_signature_ip = models.GenericIPAddressField(null=True, blank=True)
    worker_signature_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Document
    contract_file = models.FileField(
        upload_to='contracts/%Y/%m/%d/',
        null=True, 
        blank=True,
        help_text="PDF version of contract"
    )
    
    # Blockchain
    contract_hash = models.CharField(
        max_length=64, 
        blank=True,
        help_text="SHA256 hash of contract terms"
    )
    escrow_id = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Stellar escrow contract ID"
    )
    transaction_hash = models.CharField(
        max_length=64, 
        blank=True,
        help_text="Stellar transaction hash"
    )
    
    # Status
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS, default='DRAFT')
    is_template = models.BooleanField(default=False, help_text="Is this a template contract?")
    version = models.PositiveIntegerField(default=1)
    
    # Metadata
    notes = models.TextField(blank=True, help_text="Internal notes")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='contracts_created'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    terminated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'contracts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employer', 'status']),
            models.Index(fields=['worker', 'status']),
            models.Index(fields=['job', 'status']),
            models.Index(fields=['contract_hash']),
        ]
    
    def __str__(self):
        return f"Contract: {self.job.title} - {self.employer.full_name} & {self.worker.full_name}"
    
    def generate_hash(self):
        """Generate SHA256 hash of contract terms"""
        contract_data = {
            'job_id': self.job.id,
            'employer': self.employer.stellar_public_key,
            'worker': self.worker.stellar_public_key,
            'amount': str(self.payment_amount),
            'terms': self.terms,
            'special_clauses': self.special_clauses,
            'start_date': str(self.start_date),
            'end_date': str(self.end_date),
            'version': self.version
        }
        contract_string = json.dumps(contract_data, sort_keys=True)
        return hashlib.sha256(contract_string.encode()).hexdigest()
    
    def sign_by_employer(self, ip_address=None):
        """Employer signs the contract"""
        self.employer_signed = True
        self.employer_signed_at = timezone.now()
        if ip_address:
            self.employer_signature_ip = ip_address
        self.save()
        self.check_activation()
    
    def sign_by_worker(self, ip_address=None):
        """Worker signs the contract"""
        self.worker_signed = True
        self.worker_signed_at = timezone.now()
        if ip_address:
            self.worker_signature_ip = ip_address
        self.save()
        self.check_activation()
    
    def check_activation(self):
        """Check if contract can be activated"""
        if self.employer_signed and self.worker_signed and self.status == 'PENDING':
            self.status = 'ACTIVE'
            self.activated_at = timezone.now()
            self.contract_hash = self.generate_hash()
            self.save()
            
            # Update job status
            self.job.status = 'IN_PROGRESS'
            self.job.save()
    
    def complete(self):
        """Mark contract as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
        
        # Update job status
        self.job.complete()
    
    def terminate(self, reason=""):
        """Terminate contract"""
        self.status = 'TERMINATED'
        self.terminated_at = timezone.now()
        self.notes = reason
        self.save()
        
        # Update job status
        self.job.status = 'CANCELLED'
        self.job.save()
    
    def raise_dispute(self, reason=""):
        """Raise dispute on contract"""
        self.status = 'DISPUTED'
        self.notes = reason
        self.save()
        
        # Update job status
        self.job.status = 'DISPUTED'
        self.job.save()
    
    @property
    def is_signed_by_both(self):
        """Check if both parties have signed"""
        return self.employer_signed and self.worker_signed
    
    @property
    def is_active(self):
        """Check if contract is active"""
        return self.status == 'ACTIVE'
    
    @property
    def days_remaining(self):
        """Calculate days remaining"""
        if self.end_date and self.status == 'ACTIVE':
            remaining = (self.end_date - timezone.now().date()).days
            return max(remaining, 0)
        return 0


class ContractMilestone(models.Model):
    """Milestones for milestone-based payments"""
    
    STATUS = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('DISPUTED', 'Disputed'),
    )
    
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        related_name='milestones'
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    
    due_date = models.DateField()
    completed_date = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    
    # Completion verification
    completed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='completed_milestones'
    )
    completion_notes = models.TextField(blank=True)
    
    # Blockchain
    payment_released = models.BooleanField(default=False)
    payment_tx_hash = models.CharField(max_length=64, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contract_milestones'
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['contract', 'status']),
        ]
    
    def __str__(self):
        return f"{self.contract.job.title} - {self.title}"
    
    def complete(self, user, notes=""):
        """Mark milestone as completed"""
        self.status = 'COMPLETED'
        self.completed_date = timezone.now()
        self.completed_by = user
        self.completion_notes = notes
        self.save()


class ContractAmendment(models.Model):
    """Amendments to existing contracts"""
    
    STATUS = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        related_name='amendments'
    )
    proposed_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='proposed_amendments'
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    changes = models.JSONField(help_text="JSON of changes made")
    
    employer_approved = models.BooleanField(default=False)
    worker_approved = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contract_amendments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Amendment to {self.contract.job.title} - {self.title}"
    
    def approve_by_employer(self):
        self.employer_approved = True
        if self.worker_approved:
            self.status = 'APPROVED'
            self.approved_at = timezone.now()
        self.save()
    
    def approve_by_worker(self):
        self.worker_approved = True
        if self.employer_approved:
            self.status = 'APPROVED'
            self.approved_at = timezone.now()
        self.save()
    
    def reject(self, reason=""):
        self.status = 'REJECTED'
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save()


class ContractTemplate(models.Model):
    """Reusable contract templates"""
    
    CATEGORIES = (
        ('CLEANING', 'Cleaning'),
        ('COOKING', 'Cooking'),
        ('CHILDCARE', 'Childcare'),
        ('ELDERLY', 'Elderly Care'),
        ('GARDENING', 'Gardening'),
        ('OTHER', 'Other'),
    )
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    description = models.TextField()
    terms = models.TextField(help_text="Standard contract terms")
    
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='contract_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contract_templates'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.category}"