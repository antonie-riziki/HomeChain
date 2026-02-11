from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
from .models import (
    PaymentTransaction, PaymentWallet, PaymentEscrow, 
    PlatformFee, WithdrawalRequest
)
from .serializers import *
from .permissions import *
from .stellar_client import StellarEscrowClient
from contracts.models import Contract
import logging

logger = logging.getLogger(__name__)


class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """View payment transactions"""
    
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'status']
    search_fields = ['stellar_transaction_id', 'description']
    ordering_fields = ['created_at', 'amount']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'EMPLOYER':
            return PaymentTransaction.objects.filter(employer=user)
        elif user.user_type == 'WORKER':
            return PaymentTransaction.objects.filter(worker=user)
        elif user.user_type == 'ADMIN':
            return PaymentTransaction.objects.all()
        
        return PaymentTransaction.objects.none()


class PaymentWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """View payment wallets"""
    
    serializer_class = PaymentWalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'ADMIN':
            return PaymentWallet.objects.all()
        else:
            return PaymentWallet.objects.filter(user=user)
    
    def get_object(self):
        """Get wallet for current user if no pk provided"""
        if self.kwargs.get('pk') == 'me':
            wallet, created = PaymentWallet.objects.get_or_create(
                user=self.request.user,
                defaults={
                    'stellar_public_key': self.request.user.stellar_public_key,
                    'stellar_secret_key': self.request.user.stellar_secret_key,
                }
            )
            return wallet
        return super().get_object()
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get wallet transactions"""
        wallet = self.get_object()
        transactions = PaymentTransaction.objects.filter(
            Q(employer=wallet.user) | Q(worker=wallet.user)
        )[:50]
        
        serializer = PaymentTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync wallet with blockchain"""
        wallet = self.get_object()
        
        try:
            stellar = StellarEscrowClient()
            balances = stellar.get_account_balance(wallet.stellar_public_key)
            
            # Update wallet balance (XLM)
            if 'XLM' in balances:
                wallet.available_balance = Decimal(str(balances['XLM']))
            
            wallet.last_synced_at = timezone.now()
            wallet.save()
            
            return Response({
                'message': 'Wallet synced successfully',
                'balances': balances
            })
        except Exception as e:
            logger.error(f"Failed to sync wallet: {str(e)}")
            return Response(
                {'error': f'Failed to sync wallet: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentEscrowViewSet(viewsets.ModelViewSet):
    """Payment escrow management"""
    
    queryset = PaymentEscrow.objects.all()
    serializer_class = PaymentEscrowSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status']
    search_fields = ['stellar_escrow_id', 'contract__job__title']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'EMPLOYER':
            return PaymentEscrow.objects.filter(contract__employer=user)
        elif user.user_type == 'WORKER':
            return PaymentEscrow.objects.filter(contract__worker=user)
        elif user.user_type == 'ADMIN':
            return PaymentEscrow.objects.all()
        
        return PaymentEscrow.objects.none()
    
    def get_permissions(self):
        if self.action in ['approve', 'dispute']:
            permission_classes = [permissions.IsAuthenticated, IsEscrowParty]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve payment release"""
        escrow = self.get_object()
        
        serializer = PaymentEscrowActionSerializer(
            data=request.data,
            context={'request': request, 'escrow': escrow}
        )
        serializer.is_valid(raise_exception=True)
        
        # Record approval
        if request.user == escrow.contract.employer:
            escrow.approve_by_employer()
            approver_type = 'employer'
        else:
            escrow.approve_by_worker()
            approver_type = 'worker'
        
        # Check if both approved and release payment
        if escrow.employer_approved and escrow.worker_approved:
            try:
                # Release payment on Stellar
                stellar = StellarEscrowClient()
                result = stellar.release_payment(
                    contract=escrow.contract,
                    approved_by=request.user
                )
                
                # Create transaction record
                PaymentTransaction.objects.create(
                    contract=escrow.contract,
                    employer=escrow.contract.employer,
                    worker=escrow.contract.worker,
                    transaction_type='ESCROW_RELEASE',
                    amount=escrow.worker_amount,
                    platform_fee=escrow.platform_fee,
                    worker_amount=escrow.worker_amount,
                    stellar_transaction_id=result['transaction_hash'],
                    stellar_escrow_id=escrow.stellar_escrow_id,
                    status='SUCCESS',
                    completed_at=timezone.now(),
                    description=f'Payment released for contract {escrow.contract.id}'
                )
                
                # Update worker wallet
                try:
                    wallet = escrow.contract.worker.wallet
                    wallet.credit(escrow.worker_amount)
                except PaymentWallet.DoesNotExist:
                    pass
                
            except Exception as e:
                logger.error(f"Failed to release payment: {str(e)}")
                return Response(
                    {'error': f'Failed to release payment: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response({
            'message': f'Approval recorded ({approver_type})',
            'employer_approved': escrow.employer_approved,
            'worker_approved': escrow.worker_approved,
            'status': escrow.status
        })
    
    @action(detail=True, methods=['post'])
    def dispute(self, request, pk=None):
        """Raise dispute on escrow"""
        escrow = self.get_object()
        
        serializer = PaymentEscrowActionSerializer(
            data=request.data,
            context={'request': request, 'escrow': escrow}
        )
        serializer.is_valid(raise_exception=True)
        
        escrow.raise_dispute()
        
        # Create transaction record
        PaymentTransaction.objects.create(
            contract=escrow.contract,
            employer=escrow.contract.employer,
            worker=escrow.contract.worker,
            transaction_type='ESCROW_REFUND',
            amount=escrow.total_amount,
            stellar_escrow_id=escrow.stellar_escrow_id,
            status='PENDING',
            description=f'Dispute raised: {serializer.validated_data.get("notes", "")}'
        )
        
        return Response({
            'message': 'Dispute raised successfully',
            'status': escrow.status
        })
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get escrow status from blockchain"""
        escrow = self.get_object()
        
        try:
            stellar = StellarEscrowClient()
            blockchain_status = stellar.get_escrow_status(escrow.stellar_escrow_id)
            
            return Response({
                'local_status': escrow.status,
                'blockchain_status': blockchain_status,
                'employer_approved': escrow.employer_approved,
                'worker_approved': escrow.worker_approved
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to get blockchain status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WithdrawalRequestViewSet(viewsets.ModelViewSet):
    """Withdrawal request management"""
    
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['worker__full_name', 'stellar_transaction_id']
    ordering_fields = ['created_at', 'amount']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'WORKER':
            return WithdrawalRequest.objects.filter(worker=user)
        elif user.user_type == 'ADMIN':
            return WithdrawalRequest.objects.all()
        
        return WithdrawalRequest.objects.none()
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, CanWithdraw]
        elif self.action in ['process', 'cancel']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save()
        
        # Create transaction record
        PaymentTransaction.objects.create(
            worker=self.request.user,
            transaction_type='WITHDRAWAL',
            amount=serializer.validated_data['amount'],
            status='PENDING',
            description=f'Withdrawal request to {serializer.validated_data["stellar_destination"]}'
        )
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process withdrawal request (admin only)"""
        withdrawal = self.get_object()
        
        serializer = WithdrawalProcessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        
        if action == 'approve':
            try:
                # Send payment on Stellar
                stellar = StellarEscrowClient()
                result = stellar.send_payment(
                    from_secret=settings.STELLAR_PLATFORM_SECRET,
                    to_public=withdrawal.stellar_destination,
                    amount=float(withdrawal.amount)
                )
                
                withdrawal.process(
                    admin_user=request.user,
                    transaction_id=result['transaction_hash']
                )
                
                # Update transaction
                PaymentTransaction.objects.filter(
                    worker=withdrawal.worker,
                    transaction_type='WITHDRAWAL',
                    status='PENDING'
                ).latest('created_at').mark_success(result['transaction_hash'])
                
                message = 'Withdrawal approved and processed'
                
            except Exception as e:
                withdrawal.fail(str(e))
                return Response(
                    {'error': f'Failed to process withdrawal: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        else:  # reject
            withdrawal.status = 'CANCELLED'
            withdrawal.notes = serializer.validated_data.get('notes', '')
            withdrawal.save()
            message = 'Withdrawal rejected'
        
        return Response({
            'message': message,
            'status': withdrawal.status
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel withdrawal request"""
        withdrawal = self.get_object()
        
        if withdrawal.status != 'PENDING':
            return Response(
                {'error': f'Cannot cancel withdrawal with status {withdrawal.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        withdrawal.cancel()
        
        # Update transaction
        PaymentTransaction.objects.filter(
            worker=withdrawal.worker,
            transaction_type='WITHDRAWAL',
            status='PENDING'
        ).latest('created_at').mark_failed('Cancelled by user')
        
        return Response({
            'message': 'Withdrawal request cancelled',
            'status': withdrawal.status
        })


class PlatformFeeViewSet(viewsets.ModelViewSet):
    """Platform fee configuration (admin only)"""
    
    queryset = PlatformFee.objects.filter(is_active=True)
    serializer_class = PlatformFeeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['fee_type', 'is_active']
    search_fields = ['name']
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current active fee"""
        fee = PlatformFee.objects.filter(
            is_active=True,
            effective_from__lte=timezone.now()
        ).exclude(
            effective_to__lt=timezone.now()
        ).first()
        
        if fee:
            serializer = self.get_serializer(fee)
            return Response(serializer.data)
        
        # Default fee if none configured
        return Response({
            'name': 'Default Fee',
            'fee_type': 'PERCENTAGE',
            'fee_value': '5.00',
            'min_fee': '1.00',
            'max_fee': '50.00'
        })
    
    @action(detail=True, methods=['get'])
    def calculate(self, request, pk=None):
        """Calculate fee for an amount"""
        fee = self.get_object()
        amount = request.query_params.get('amount')
        
        if not amount:
            return Response(
                {'error': 'Amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(amount)
            fee_amount = fee.calculate_fee(amount)
            
            return Response({
                'amount': str(amount),
                'fee': str(fee_amount),
                'total': str(amount + fee_amount),
                'worker_gets': str(amount - fee_amount)
            })
        except:
            return Response(
                {'error': 'Invalid amount'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentStatsViewSet(viewsets.ViewSet):
    """Payment statistics"""
    
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get payment overview statistics"""
        
        # Total volume
        total_volume = PaymentTransaction.objects.filter(
            status='SUCCESS'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Platform fees
        platform_fees = PaymentTransaction.objects.filter(
            status='SUCCESS',
            transaction_type='PLATFORM_FEE'
        ).aggregate(total=Sum('platform_fee'))['total'] or 0
        
        # Worker payments
        worker_payments = PaymentTransaction.objects.filter(
            status='SUCCESS',
            transaction_type='ESCROW_RELEASE'
        ).aggregate(total=Sum('worker_amount'))['total'] or 0
        
        # Pending payments
        pending_payments = PaymentEscrow.objects.filter(
            status='FUNDED'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Transaction counts
        completed_transactions = PaymentTransaction.objects.filter(
            status='SUCCESS'
        ).count()
        
        pending_withdrawals = WithdrawalRequest.objects.filter(
            status='PENDING'
        ).count()
        
        serializer = PaymentStatsSerializer({
            'total_volume': total_volume,
            'platform_fees': platform_fees,
            'worker_payments': worker_payments,
            'pending_payments': pending_payments,
            'completed_transactions': completed_transactions,
            'pending_withdrawals': pending_withdrawals
        })
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Get monthly payment statistics"""
        from django.db.models.functions import TruncMonth
        
        monthly_stats = PaymentTransaction.objects.filter(
            status='SUCCESS'
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            volume=Sum('amount'),
            fees=Sum('platform_fee'),
            count=Count('id')
        ).order_by('-month')[:12]
        
        return Response(monthly_stats)