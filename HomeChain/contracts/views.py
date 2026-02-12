from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from .models import Contract, ContractMilestone, ContractAmendment, ContractTemplate
from .serializers import *
from .permissions import *
from .utils import generate_contract_pdf, generate_contract_summary
from payments.stellar_client import StellarEscrowClient
import json

class ContractViewSet(viewsets.ModelViewSet):
    """Contract management viewset"""
    
    queryset = Contract.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_schedule']
    search_fields = ['title', 'description', 'job__title']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'payment_amount']
    
    def get_serializer_class(self):
        """Return different serializers for different actions"""
        if self.action == 'create':
            return ContractCreateSerializer
        elif self.action == 'retrieve':
            return ContractDetailSerializer
        return ContractSerializer
    
    def get_permissions(self):
        """Set custom permissions for different actions"""
        if self.action in ['sign', 'download_pdf']:
            permission_classes = [permissions.IsAuthenticated, CanSignContract]
        elif self.action in ['terminate', 'complete', 'dispute']:
            permission_classes = [permissions.IsAuthenticated, IsContractParty]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user type"""
        user = self.request.user
        
        if user.user_type == 'EMPLOYER':
            # Employers see contracts they created
            return Contract.objects.filter(employer=user)
        elif user.user_type == 'WORKER':
            # Workers see contracts assigned to them
            return Contract.objects.filter(worker=user)
        elif user.user_type == 'ADMIN':
            # Admins see all
            return Contract.objects.all()
        
        return Contract.objects.none()
    
    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """Sign contract"""
        contract = self.get_object()
        
        serializer = ContractSignSerializer(
            data=request.data,
            context={'request': request, 'contract': contract}
        )
        serializer.is_valid(raise_exception=True)
        
        ip_address = serializer.validated_data.get(
            'ip_address',
            request.META.get('REMOTE_ADDR')
        )
        
        # Sign based on user type
        if request.user == contract.employer:
            contract.sign_by_employer(ip_address)
        elif request.user == contract.worker:
            contract.sign_by_worker(ip_address)
        
        # If both signed, create escrow
        if contract.is_signed_by_both:
            try:
                # Create escrow on Stellar
                stellar = StellarEscrowClient()
                escrow = stellar.create_escrow(
                    employer_secret=contract.employer.stellar_secret_key,
                    worker_public=contract.worker.stellar_public_key,
                    amount=float(contract.payment_amount),
                    job_id=contract.job.id,
                    contract_id=contract.id
                )
                
                contract.escrow_id = escrow['escrow_id']
                contract.transaction_hash = escrow['transaction_hash']
                contract.save()
                
            except Exception as e:
                # Log error but don't fail
                print(f"Failed to create escrow: {str(e)}")
        
        return Response({
            'message': 'Contract signed successfully',
            'employer_signed': contract.employer_signed,
            'worker_signed': contract.worker_signed,
            'status': contract.status
        })
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Download contract as PDF"""
        contract = self.get_object()
        
        # Check permission
        if request.user not in [contract.employer, contract.worker] and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to download this contract'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate PDF
        pdf_file = generate_contract_pdf(contract)
        
        # Create response
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="contract_{contract.id}.pdf"'
        
        return response
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get human-readable contract summary"""
        contract = self.get_object()
        
        summary = generate_contract_summary(contract)
        
        return Response({'summary': summary})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark contract as completed"""
        contract = self.get_object()
        
        if contract.status != 'ACTIVE':
            return Response(
                {'error': f'Contract is {contract.get_status_display()}, cannot complete'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contract.complete()
        
        return Response({
            'message': 'Contract completed successfully',
            'status': contract.status
        })
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate contract"""
        contract = self.get_object()
        
        reason = request.data.get('reason', '')
        
        contract.terminate(reason)
        
        return Response({
            'message': 'Contract terminated',
            'status': contract.status
        })
    
    @action(detail=True, methods=['post'])
    def dispute(self, request, pk=None):
        """Raise dispute on contract"""
        contract = self.get_object()
        
        reason = request.data.get('reason', '')
        
        contract.raise_dispute(reason)
        
        return Response({
            'message': 'Dispute raised',
            'status': contract.status
        })
    
    @action(detail=True, methods=['get'])
    def verify(self, request, pk=None):
        """Verify contract hash"""
        contract = self.get_object()
        
        from .utils import verify_contract_hash
        is_valid = verify_contract_hash(contract)
        
        return Response({
            'contract_id': contract.id,
            'contract_hash': contract.contract_hash,
            'current_hash': contract.generate_hash(),
            'is_valid': is_valid
        })


class ContractMilestoneViewSet(viewsets.ModelViewSet):
    """Contract milestone management"""
    
    serializer_class = ContractMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated, IsContractParty]
    
    def get_queryset(self):
        user = self.request.user
        return ContractMilestone.objects.filter(
            Q(contract__employer=user) | Q(contract__worker=user)
        ).distinct()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsContractEmployer]
        else:
            permission_classes = [permissions.IsAuthenticated, IsContractParty]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark milestone as completed"""
        milestone = self.get_object()
        
        if milestone.contract.worker != request.user:
            return Response(
                {'error': 'Only the worker can complete milestones'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if milestone.status == 'COMPLETED':
            return Response(
                {'error': 'Milestone already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notes = request.data.get('notes', '')
        milestone.complete(request.user, notes)
        
        return Response({
            'message': 'Milestone completed',
            'status': milestone.status
        })


class ContractAmendmentViewSet(viewsets.ModelViewSet):
    """Contract amendment management"""
    
    serializer_class = ContractAmendmentSerializer
    permission_classes = [permissions.IsAuthenticated, CanAmendContract]
    
    def get_queryset(self):
        user = self.request.user
        return ContractAmendment.objects.filter(
            Q(contract__employer=user) | Q(contract__worker=user)
        ).distinct()
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve amendment"""
        amendment = self.get_object()
        contract = amendment.contract
        
        if request.user == contract.employer:
            amendment.approve_by_employer()
        elif request.user == contract.worker:
            amendment.approve_by_worker()
        else:
            return Response(
                {'error': 'You are not a party to this contract'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            'message': 'Amendment approved',
            'status': amendment.status
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject amendment"""
        amendment = self.get_object()
        
        reason = request.data.get('reason', '')
        amendment.reject(reason)
        
        return Response({
            'message': 'Amendment rejected',
            'status': amendment.status
        })


class ContractTemplateViewSet(viewsets.ModelViewSet):
    """Contract template management"""
    
    queryset = ContractTemplate.objects.filter(is_active=True)
    serializer_class = ContractTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def create_contract(self, request, pk=None):
        """Create contract from template"""
        template = self.get_object()
        
        job_id = request.data.get('job_id')
        from jobs.models import Job
        job = get_object_or_404(Job, id=job_id)
        
        # Check permissions
        if job.employer != request.user:
            return
