from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from accounts.models import User
from contracts.models import Contract

class PaymentTransaction(models.Model):
    """Blockchain payment transactions"""
    
    TRANSACTION_TYPES = (
        ('ESCROW_CREATE', 'Escrow Created'),
        ('ESCROW_FUND', 'Escrow Funded'),
        ('ESCROW_RELEASE', 'Payment Released'),
        ('ESCROW_REFUND', 'Payment Refunded'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('DEPOSIT', 'Deposit'),
        ('PLATFORM_FEE', 'Platform Fee'),
    )
    
    STATUS = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    # Relations
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='payments'
    )
    employer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='payments_made'
    )
    worker = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='payments_received'
    )
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    platform_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    worker_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    
    # Stellar blockchain
    stellar_transaction_id = models.CharField(
        max_length=64, 
        unique=True,
        null=True, 
        blank=True
    )
    stellar_escrow_id = models.CharField(max_length=100, blank=True)
    stellar_source_account = models.CharField(max_length=56, blank=True)
    stellar_destination_account = models.CharField(max_length=56, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    error_message = models.TextField(blank=True)
    
    # Metadata
    description = models.CharField(max_length=255, blank=True)
    milestone_id = models.IntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['stellar_transaction_id']),
            models.Index(fields=['contract', 'transaction_type']),
            models.Index(fields=['employer', 'status']),
            models.Index(fields=['worker', 'status']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - ${self.amount} - {self.status}"
    
    def mark_success(self, transaction_id=None):
        """Mark transaction as successful"""
        self.status = 'SUCCESS'
        self.completed_at = timezone.now()
        if transaction_id:
            self.stellar_transaction_id = transaction_id
        self.save()
    
    def mark_failed(self, error):
        """Mark transaction as failed"""
        self.status = 'FAILED'
        self.error_message = str(error)[:255]
        self.save()


class PaymentWallet(models.Model):
    """User wallet information"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    
    # Stellar wallet
    stellar_public_key = models.CharField(max_length=56, unique=True)
    stellar_secret_key = models.CharField(max_length=56)  # Encrypted in production
    
    # Balances
    available_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0.00
    )
    pending_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0.00
    )
    total_earned = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0.00
    )
    total_withdrawn = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0.00
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_wallets'
    
    def __str__(self):
        return f"{self.user.full_name} - Balance: ${self.available_balance}"
    
    def credit(self, amount):
        """Add money to wallet"""
        self.available_balance += Decimal(str(amount))
        self.total_earned += Decimal(str(amount))
        self.save()
    
    def debit(self, amount):
        """Remove money from wallet"""
        if self.available_balance >= Decimal(str(amount)):
            self.available_balance -= Decimal(str(amount))
            self.total_withdrawn += Decimal(str(amount))
            self.save()
            return True
        return False


class PaymentEscrow(models.Model):
    """Escrow records for jobs"""
    
    STATUS = (
        ('PENDING', 'Pending Funding'),
        ('FUNDED', 'Funded'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('DISPUTED', 'Disputed'),
        ('REFUNDED', 'Refunded'),
    )
    
    contract = models.OneToOneField(
        Contract, 
        on_delete=models.CASCADE,
        related_name='escrow'
    )
    
    # Stellar escrow
    stellar_escrow_id = models.CharField(max_length=100, unique=True)
    stellar_contract_id = models.CharField(max_length=100)
    stellar_transaction_hash = models.CharField(max_length=64)
    
    # Amounts
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    platform_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    worker_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    released_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    
    # Signatures
    employer_approved = models.BooleanField(default=False)
    worker_approved = models.BooleanField(default=False)
    employer_approved_at = models.DateTimeField(null=True, blank=True)
    worker_approved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    funded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    disputed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_escrows'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['stellar_escrow_id']),
        ]
    
    def __str__(self):
        return f"Escrow {self.stellar_escrow_id} - ${self.total_amount} - {self.status}"
    
    def fund(self, transaction_id=None):
        """Mark escrow as funded"""
        self.status = 'FUNDED'
        self.funded_at = timezone.now()
        if transaction_id:
            self.stellar_transaction_hash = transaction_id
        self.save()
    
    def approve_by_employer(self):
        """Employer approves payment release"""
        self.employer_approved = True
        self.employer_approved_at = timezone.now()
        self.save()
        self.check_and_release()
    
    def approve_by_worker(self):
        """Worker approves payment release"""
        self.worker_approved = True
        self.worker_approved_at = timezone.now()
        self.save()
        self.check_and_release()
    
    def check_and_release(self):
        """Check if both parties approved and release payment"""
        if self.employer_approved and self.worker_approved:
            self.status = 'COMPLETED'
            self.completed_at = timezone.now()
            self.save()
            return True
        return False
    
    def raise_dispute(self):
        """Raise dispute on escrow"""
        self.status = 'DISPUTED'
        self.disputed_at = timezone.now()
        self.save()


class PlatformFee(models.Model):
    """Platform fee configuration"""
    
    FEE_TYPE = (
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
    )
    
    name = models.CharField(max_length=100)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPE, default='PERCENTAGE')
    fee_value = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Percentage or fixed amount"
    )
    min_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        help_text="Minimum fee for percentage-based"
    )
    max_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        help_text="Maximum fee for percentage-based"
    )
    
    is_active = models.BooleanField(default=True)
    effective_from = models.DateTimeField(default=timezone.now)
    effective_to = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'platform_fees'
        ordering = ['-effective_from']
    
    def __str__(self):
        if self.fee_type == 'PERCENTAGE':
            return f"{self.name} - {self.fee_value}%"
        else:
            return f"{self.name} - ${self.fee_value}"
    
    def calculate_fee(self, amount):
        """Calculate platform fee for given amount"""
        amount = Decimal(str(amount))
        
        if self.fee_type == 'PERCENTAGE':
            fee = amount * (self.fee_value / 100)
            if self.min_fee:
                fee = max(fee, self.min_fee)
            if self.max_fee:
                fee = min(fee, self.max_fee)
        else:
            fee = self.fee_value
        
        return fee.quantize(Decimal('0.01'))


class WithdrawalRequest(models.Model):
    """Worker withdrawal requests"""
    
    STATUS = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    worker = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='withdrawal_requests'
    )
    
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(1.00)]
    )
    stellar_destination = models.CharField(max_length=56)
    
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    stellar_transaction_id = models.CharField(max_length=64, blank=True)
    
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='processed_withdrawals'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'withdrawal_requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Withdrawal ${self.amount} - {self.worker.full_name} - {self.status}"
    
    def process(self, admin_user, transaction_id=None):
        """Process withdrawal request"""
        self.status = 'COMPLETED'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        if transaction_id:
            self.stellar_transaction_id = transaction_id
        self.save()
        
        # Update wallet
        wallet = self.worker.wallet
        wallet.debit(self.amount)
    
    def fail(self, error_message):
        """Mark withdrawal as failed"""
        self.status = 'FAILED'
        self.notes = error_message
        self.save()
    
    def cancel(self):
        """Cancel withdrawal request"""
        self.status = 'CANCELLED'
        self.save()